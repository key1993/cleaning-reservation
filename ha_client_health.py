"""
Poll each client's Home Assistant (Brain URL + token) for connectivity and entity states.
Grid/Inverter sensors are green when state is online/active/normal.
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import requests

DEFAULT_TIMEOUT = float(os.environ.get("HA_HEALTH_TIMEOUT", "8"))
VERIFY_SSL = os.environ.get("HA_HEALTH_VERIFY_SSL", "true").lower() in ("1", "true", "yes")
SG_PLANT_STATUS_ENTITY = os.environ.get("HA_SG_PLANT_STATUS_ENTITY", "sensor.sg_plant_status")
SMARTLIFE_STATUS_ENTITY = os.environ.get("HA_SMARTLIFE_STATUS_ENTITY", "sensor.smartlife_device_status")
IS_NIGHT_TIME_ENTITY = os.environ.get("HA_IS_NIGHT_TIME_ENTITY", "input_boolean.is_night_time")
HEALTHY_SENSOR_STATES = {"online", "active", "normal"}
HEALTH_ALERTS_WHATSAPP = os.environ.get("HEALTH_ALERTS_WHATSAPP", "true").lower() in (
    "1",
    "true",
    "yes",
    "on",
)

_whatsapp_lock = threading.Lock()


def _send_whatsapp_safe(message: str) -> None:
    if not HEALTH_ALERTS_WHATSAPP or not message.strip():
        return
    try:
        with _whatsapp_lock:
            from routes import send_whatsapp_message

            send_whatsapp_message(message)
    except Exception as e:
        print(f"⚠️ Health WhatsApp notify failed: {e}")


def _notify_health_transitions(
    full_name: str,
    email: str,
    phone: str,
    old_pi: Optional[bool],
    new_pi: Optional[bool],
    old_grid: Optional[bool],
    new_grid: Optional[bool],
    old_solar: Any,
    new_solar: Any,
) -> None:
    """
    WhatsApp when a light goes red (fault) or returns green (recovered).
    Fault: new is False and previous was not False (True or None).
    Recovery: new is True and previous was strictly False.
    """
    display_name = (full_name or "Unknown").strip() or "Unknown"
    email_s = (email or "N/A").strip() or "N/A"
    phone_s = (phone or "N/A").strip() or "N/A"

    checks: Tuple[Tuple[str, str, Optional[bool], Optional[bool]], ...] = (
        ("Brain (HA)", "🏠", old_pi, new_pi),
        ("Grid", "⚡", old_grid, new_grid),
        ("Inverter", "☀️", old_solar if isinstance(old_solar, bool) else None, new_solar if isinstance(new_solar, bool) else None),
    )

    for label, icon, old_v, new_v in checks:
        if new_v is False and old_v is not False:
            msg = (
                f"⚠️ *Client health — fault*\n\n"
                f"👤 *{display_name}*\n"
                f"📧 {email_s}\n"
                f"📱 {phone_s}\n\n"
                f"{icon} *{label}* is OFF/down (red on dashboard).\n"
                f"Check Home Assistant / site status."
            )
            _send_whatsapp_safe(msg)
        elif new_v is True and old_v is False:
            msg = (
                f"✅ *Client health — recovered*\n\n"
                f"👤 *{display_name}*\n"
                f"📧 {email_s}\n"
                f"📱 {phone_s}\n\n"
                f"{icon} *{label}* is OK again (green on dashboard)."
            )
            _send_whatsapp_safe(msg)


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
    account_id: Optional[str] = None,
    *,
    timeout: float = DEFAULT_TIMEOUT,
) -> Tuple[Optional[bool], Optional[bool], Any]:
    """
    Returns (pi_ok, grid_ok, inverter_ok_or_standby).
    pi_ok: True if GET /api/config succeeds with this token (Brain reachable).
    grid_ok: smartlife status in online/active/normal.
    inverter_ok_or_standby: plant status in online/active/normal; or "standby" if non-healthy at night.
    If Brain is unreachable, returns (False, False, False).
    """
    base = _normalize_base(ha_url)
    token = (ha_token or "").strip()
    if not base or not token:
        return (None, None, None)
    account_id = str(account_id or "").strip()

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
        return (False, False, False)

    def entity_state(entity_id: str) -> Optional[str]:
        if not account_id:
            return None
        try:
            r = requests.get(
                f"{base}/api/states/{entity_id}",
                params={"account_id": account_id},
                headers=hdrs,
                timeout=timeout,
                verify=VERIFY_SSL,
            )
            if r.status_code != 200:
                return None
            data = r.json()
            return str(data.get("state") or "").strip().lower()
        except (requests.RequestException, ValueError, TypeError):
            return None

    smartlife_state = entity_state(SMARTLIFE_STATUS_ENTITY)
    plant_state = entity_state(SG_PLANT_STATUS_ENTITY)
    is_night_state = entity_state(IS_NIGHT_TIME_ENTITY)

    # Middle (⚡) = Grid: derived from SmartLife status.
    grid_ok = bool(smartlife_state in HEALTHY_SENSOR_STATES)

    inverter_healthy = bool(plant_state in HEALTHY_SENSOR_STATES)
    is_night = bool(is_night_state in {"on", "true", "1", "active", "yes"})
    if inverter_healthy:
        inverter_ok: Any = True
    elif is_night:
        # Avoid false positive notifications at night when inverter can be off/unavailable.
        inverter_ok = "standby"
    else:
        inverter_ok = False

    return (pi_ok, grid_ok, inverter_ok)


def _apply_health_update(
    clients_collection: Any,
    client_id: Any,
    pi_ok: Optional[bool],
    grid_ok: Optional[bool],
    solar_ok: Any,
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
    account_id = client.get("account_number") or client.get("account_id") or ""
    cid = client["_id"]

    old_pi = client.get("health_pi_ok")
    old_grid = client.get("health_inverter_ok")
    old_solar = client.get("health_solar_ok")
    full_name = client.get("full_name") or ""
    email = client.get("email") or ""
    phone = client.get("phone") or ""

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

    # Sensor status endpoints require account_id query parameter.
    pi_ok, grid_ok, solar_ok = poll_client_health(ha_url, ha_token, account_id=account_id)
    _apply_health_update(clients_collection, cid, pi_ok, grid_ok, solar_ok)
    _notify_health_transitions(
        full_name,
        email,
        phone,
        old_pi,
        pi_ok,
        old_grid,
        grid_ok,
        old_solar,
        solar_ok,
    )


def refresh_all_clients_health(clients_collection: Any, max_workers: int = 12) -> None:
    """Poll HA for every client document (parallel). Safe to call from scheduler or admin load."""
    clients = list(
        clients_collection.find(
            {},
            {
                "ha_url": 1,
                "ha_token": 1,
                "account_number": 1,
                "account_id": 1,
                "full_name": 1,
                "email": 1,
                "phone": 1,
                "health_pi_ok": 1,
                "health_inverter_ok": 1,
                "health_solar_ok": 1,
            },
        )
    )
    if not clients:
        return
    workers = min(max_workers, max(1, len(clients)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [
            pool.submit(_refresh_one_client, clients_collection, c) for c in clients
        ]
        for f in as_completed(futures):
            f.result()
