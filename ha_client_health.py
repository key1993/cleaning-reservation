"""
Poll each client's Home Assistant (Brain URL + token) for connectivity and entity states.
Grid/solar: input_boolean ON = offline (bad LED), OFF = running (good LED).
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import requests

DEFAULT_TIMEOUT = float(os.environ.get("HA_HEALTH_TIMEOUT", "8"))
VERIFY_SSL = os.environ.get("HA_HEALTH_VERIFY_SSL", "true").lower() in ("1", "true", "yes")
GRID_ENTITY = os.environ.get("HA_GRID_ENTITY", "input_boolean.grid_check")
SOLAR_ENTITY = os.environ.get("HA_SOLAR_ENTITY", "input_boolean.solar_check")


def _normalize_base(url: str) -> str:
    return (url or "").strip().rstrip("/")


def _headers(token: str) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {token.strip()}",
        "Content-Type": "application/json",
    }


def poll_client_health(
    ha_url: str,
    ha_token: str,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[Optional[bool], Optional[bool], Optional[bool]]:
    """
    Returns (pi_ok, grid_ok, solar_ok).
    pi_ok: True if GET /api/config succeeds with this token (Brain reachable).
    grid_ok / solar_ok: True when entity state is off (running); False when on (offline);
    None if entity missing or error.
    If Brain is unreachable, returns (False, None, None).
    """
    base = _normalize_base(ha_url)
    token = (ha_token or "").strip()
    if not base or not token:
        return (None, None, None)

    hdrs = _headers(token)
    pi_ok: Optional[bool] = None

    try:
        r = requests.get(
            f"{base}/api/config",
            headers=hdrs,
            timeout=timeout,
            verify=VERIFY_SSL,
        )
        if r.status_code == 200:
            pi_ok = True
        else:
            pi_ok = False
    except requests.RequestException:
        pi_ok = False

    if not pi_ok:
        return (False, None, None)

    def entity_running_ok(entity_id: str) -> Optional[bool]:
        try:
            r = requests.get(
                f"{base}/api/states/{entity_id}",
                headers=hdrs,
                timeout=timeout,
                verify=VERIFY_SSL,
            )
            if r.status_code != 200:
                return None
            data = r.json()
            state = (data.get("state") or "").lower()
            if state == "on":
                return False
            if state == "off":
                return True
            return None
        except (requests.RequestException, ValueError, TypeError):
            return None

    grid_ok = entity_running_ok(GRID_ENTITY)
    solar_ok = entity_running_ok(SOLAR_ENTITY)
    return (pi_ok, grid_ok, solar_ok)


def _apply_health_update(
    clients_collection: Any,
    client_id: Any,
    pi_ok: Optional[bool],
    grid_ok: Optional[bool],
    solar_ok: Optional[bool],
) -> None:
    set_doc: Dict[str, Any] = {"health_reported_at": datetime.utcnow()}
    unset_doc: Dict[str, str] = {}

    if pi_ok is not None:
        set_doc["health_pi_ok"] = pi_ok
    else:
        unset_doc["health_pi_ok"] = ""
    if grid_ok is not None:
        set_doc["health_inverter_ok"] = grid_ok
    else:
        unset_doc["health_inverter_ok"] = ""
    if solar_ok is not None:
        set_doc["health_solar_ok"] = solar_ok
    else:
        unset_doc["health_solar_ok"] = ""

    op: Dict[str, Any] = {}
    if set_doc:
        op["$set"] = set_doc
    if unset_doc:
        op["$unset"] = unset_doc
    if op:
        clients_collection.update_one({"_id": client_id}, op)


def _refresh_one_client(clients_collection: Any, client: Dict[str, Any]) -> None:
    ha_url = client.get("ha_url") or ""
    ha_token = client.get("ha_token") or ""
    cid = client["_id"]

    if not _normalize_base(ha_url) or not (ha_token or "").strip():
        clients_collection.update_one(
            {"_id": cid},
            {
                "$set": {"health_reported_at": datetime.utcnow()},
                "$unset": {
                    "health_pi_ok": "",
                    "health_inverter_ok": "",
                    "health_solar_ok": "",
                },
            },
        )
        return

    pi_ok, grid_ok, solar_ok = poll_client_health(ha_url, ha_token)
    _apply_health_update(clients_collection, cid, pi_ok, grid_ok, solar_ok)


def refresh_all_clients_health(clients_collection: Any, max_workers: int = 12) -> None:
    """Poll HA for every client document (parallel). Safe to call from scheduler or admin load."""
    clients = list(clients_collection.find({}, {"ha_url": 1, "ha_token": 1}))
    if not clients:
        return
    workers = min(max_workers, max(1, len(clients)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(_refresh_one_client, clients_collection, c) for c in clients
        ]
        for f in as_completed(futures):
            f.result()
