"""
Poll each client's Home Assistant (Brain URL + token) for connectivity and entity states.
Grid/Solar: driven by input_boolean.grid_check / input_boolean.solar_check.
ON = problem (red). OFF = OK (green).
"""
import os
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

import requests

DEFAULT_TIMEOUT = float(os.environ.get("HA_HEALTH_TIMEOUT", "8"))
VERIFY_SSL = os.environ.get("HA_HEALTH_VERIFY_SSL", "true").lower() in ("1", "true", "yes")
GRID_CHECK_ENTITY = os.environ.get("GRID_CHECK_ENTITY", "input_boolean.grid_check")
SOLAR_CHECK_ENTITY = os.environ.get("SOLAR_CHECK_ENTITY", "input_boolean.solar_check")
HEALTH_ALERTS_WHATSAPP = os.environ.get("HEALTH_ALERTS_WHATSAPP", "true").lower() in (
    "1",
    "true",
    "yes",
    "on",
)
# Number of consecutive failing polls required before a fault alert fires.
# Prevents single transient timeouts from sending WhatsApp notifications.
# Set HEALTH_FAULT_THRESHOLD=1 in env to revert to immediate alerting.
FAULT_CONFIRM_THRESHOLD = int(os.environ.get("HEALTH_FAULT_THRESHOLD", "2"))

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

    Fault    : new is False  AND previous was strictly True.
               Using "old_v is True" (not "old_v is not False") prevents two false-positive sources:
               - None  → False : first-ever poll for a client that is already down.
               - "standby" (cast to None) → False : inverter not yet producing at dawn.
    Recovery : new is True AND previous was strictly False.
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
        if new_v is False and old_v is True:
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
        pi_ok = r.status_code == 200
    except requests.RequestException:
        pi_ok = False

    if not pi_ok:
        return (False, False, False)

    def boolean_state(entity_id: str) -> Optional[str]:
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
            return str(r.json().get("state") or "").strip().lower()
        except (requests.RequestException, ValueError, TypeError):
            return None

    # ON = problem detected → red (False). OFF = all good → green (True).
    grid_state = boolean_state(GRID_CHECK_ENTITY)
    solar_state = boolean_state(SOLAR_CHECK_ENTITY)

    grid_ok: Optional[bool] = (False if grid_state == "on" else True) if grid_state is not None else None
    solar_ok: Optional[bool] = (False if solar_state == "on" else True) if solar_state is not None else None

    return (pi_ok, grid_ok, solar_ok)


def _apply_health_update(
    clients_collection: Any,
    client_id: Any,
    pi_ok: Optional[bool],
    grid_ok: Optional[bool],
    solar_ok: Any,
    pi_streak: int = 0,
    grid_streak: int = 0,
    solar_streak: int = 0,
) -> None:
    set_doc: Dict[str, Any] = {
        "health_reported_at": datetime.utcnow(),
        "health_pi_fail_streak": pi_streak,
        "health_grid_fail_streak": grid_streak,
        "health_solar_fail_streak": solar_streak,
    }
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

    pi_streak = int(client.get("health_pi_fail_streak") or 0)
    grid_streak = int(client.get("health_grid_fail_streak") or 0)
    solar_streak = int(client.get("health_solar_fail_streak") or 0)

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

    pi_ok, grid_ok, solar_ok = poll_client_health(ha_url, ha_token, account_id=account_id)

    # Cascade fix: when Brain is unreachable, poll_client_health returns (False, False, False)
    # for all three. Grid and Solar are unreachable *because* Brain is down, not genuine faults.
    # Keep their previous stored values for notification purposes so only Brain fires an alert.
    if pi_ok is False:
        notify_grid = old_grid
        notify_solar = old_solar
    else:
        notify_grid = grid_ok
        notify_solar = solar_ok

    # Transient fix: only commit False to DB and fire alerts after FAULT_CONFIRM_THRESHOLD
    # consecutive failing polls. A single timeout (< threshold) is silently ignored.
    new_pi_streak = (pi_streak + 1) if pi_ok is False else 0
    new_grid_streak = (grid_streak + 1) if notify_grid is False else 0
    new_solar_streak = (solar_streak + 1) if notify_solar is False else 0

    effective_pi = pi_ok if (pi_ok is not False or new_pi_streak >= FAULT_CONFIRM_THRESHOLD) else old_pi
    effective_grid = notify_grid if (notify_grid is not False or new_grid_streak >= FAULT_CONFIRM_THRESHOLD) else old_grid
    effective_solar = notify_solar if (notify_solar is not False or new_solar_streak >= FAULT_CONFIRM_THRESHOLD) else old_solar

    _apply_health_update(
        clients_collection, cid,
        effective_pi, effective_grid, effective_solar,
        new_pi_streak, new_grid_streak, new_solar_streak,
    )
    _notify_health_transitions(
        full_name, email, phone,
        old_pi, effective_pi,
        old_grid, effective_grid,
        old_solar, effective_solar,
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
                "health_pi_fail_streak": 1,
                "health_grid_fail_streak": 1,
                "health_solar_fail_streak": 1,
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
