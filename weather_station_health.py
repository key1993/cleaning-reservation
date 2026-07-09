"""
Poll each registered weather station's live GHI-sensor / Arabia-Weather
connectivity via its own public `/api/local-solar-harvest/samples` endpoint
(see src/main.py in Ebsher_Harvist_software — that route has no @require_auth,
same pattern this module relies on).
"""
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict

import requests

DEFAULT_TIMEOUT = float(os.environ.get("WEATHER_STATION_HEALTH_TIMEOUT", "6"))
VERIFY_SSL = os.environ.get("WEATHER_STATION_HEALTH_VERIFY_SSL", "true").lower() in ("1", "true", "yes")


def _normalize_base(url: str) -> str:
    return (url or "").strip().rstrip("/")


def poll_station_health(url: str, *, timeout: float = DEFAULT_TIMEOUT) -> Dict[str, Any]:
    """Returns ghi_ok/weather_ok (True/False/None) + their error strings."""
    base = _normalize_base(url)
    if not base:
        return {"ghi_ok": None, "ghi_error": None, "weather_ok": None, "weather_error": None}
    try:
        r = requests.get(
            f"{base}/api/local-solar-harvest/samples",
            timeout=timeout,
            verify=VERIFY_SSL,
        )
        if r.status_code != 200:
            err = f"HTTP {r.status_code}"
            return {"ghi_ok": False, "ghi_error": err, "weather_ok": False, "weather_error": err}
        payload = r.json() if r.content else {}
        if not payload.get("success"):
            err = payload.get("error") or "Unexpected response"
            return {"ghi_ok": False, "ghi_error": err, "weather_ok": False, "weather_error": err}
        return {
            "ghi_ok": payload.get("ghi_sensor_ok"),
            "ghi_error": payload.get("ghi_sensor_error"),
            "weather_ok": payload.get("arabia_weather_ok"),
            "weather_error": payload.get("arabia_weather_error"),
        }
    except requests.RequestException as e:
        return {"ghi_ok": False, "ghi_error": str(e), "weather_ok": False, "weather_error": str(e)}


def _refresh_one_station(weather_stations_collection: Any, station: Dict[str, Any]) -> None:
    health = poll_station_health(station.get("url") or "")
    weather_stations_collection.update_one(
        {"_id": station["_id"]},
        {
            "$set": {
                "health_ghi_ok": health.get("ghi_ok"),
                "health_ghi_error": health.get("ghi_error"),
                "health_weather_ok": health.get("weather_ok"),
                "health_weather_error": health.get("weather_error"),
                "health_checked_at": datetime.utcnow(),
            }
        },
    )


def refresh_all_stations_health(weather_stations_collection: Any, max_workers: int = 8) -> None:
    """Poll every registered station in parallel. Safe to call on admin dashboard load."""
    stations = list(weather_stations_collection.find({}, {"url": 1}))
    if not stations:
        return
    workers = min(max_workers, max(1, len(stations)))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = [pool.submit(_refresh_one_station, weather_stations_collection, s) for s in stations]
        for f in as_completed(futures):
            f.result()
