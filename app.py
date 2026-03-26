from flask import Flask
from routes import routes, process_payment_reminders
from admin import admin
from auth import auth
import os
from datetime import datetime, timedelta
from pymongo import MongoClient
from db import db, clients_collection  # and optionally, reservations_collection if needed
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from firebase_service import initialize_firebase
import atexit
import sys

app = Flask(__name__)

_scheduler_lock_fp = None


def _try_acquire_scheduler_master_lock():
    """
    Only one Gunicorn/uWSGI worker should run APScheduler, or jobs (and WhatsApp)
    duplicate. On Windows (local dev), no lock — single process expected.
    Set DISABLE_AP_SCHEDULER=true to skip all scheduled jobs on this process.
    """
    if os.environ.get("DISABLE_AP_SCHEDULER", "").lower() in ("1", "true", "yes"):
        print("⏭️ APScheduler disabled (DISABLE_AP_SCHEDULER)")
        return False
    if sys.platform == "win32":
        return True
    try:
        import fcntl

        global _scheduler_lock_fp
        path = os.environ.get(
            "SCHEDULER_LOCK_FILE",
            "/tmp/cleaning_reservation_scheduler.lock",
        )
        _scheduler_lock_fp = open(path, "a+")
        fcntl.flock(_scheduler_lock_fp.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        print(f"✅ Scheduler lock OK ({path})")
        return True
    except BlockingIOError:
        print("⏭️ Another worker holds the scheduler lock; APScheduler not started here")
        return False
    except Exception as e:
        print(f"⚠️ Scheduler lock failed ({e}); starting APScheduler anyway")
        return True

# Connect to MongoDB
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://amerkiwan7723:oPQwW3nr3url61yM@cluster0.6jzip7b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client.get_database("cleaning_reservation")

# Pass `db` to routes and admin
routes.db = db
admin.db = db
auth.db = db

# Register blueprints
app.register_blueprint(routes)
app.register_blueprint(admin)
app.register_blueprint(auth)

app.secret_key = "supersecretkey"

# Initialize Firebase Admin SDK
try:
    initialize_firebase()
    print("✅ Firebase Admin SDK initialized successfully")
except Exception as e:
    print(f"⚠️ Firebase initialization failed: {e}")
    print("Payment reminder system will work, but account disabling will be unavailable")

# Set up automated payment reminder scheduler
def scheduled_payment_reminders():
    """Function called by scheduler to send payment reminders automatically"""
    try:
        result = process_payment_reminders()
        print(f"[SCHEDULER] Payment reminders sent: {result['total']} total ({result['due_soon']} due soon, {result['overdue']} overdue)")
    except Exception as e:
        print(f"[SCHEDULER] Error sending payment reminders: {e}")

# Initialize scheduler (only on the worker that acquires the lock)
scheduler = BackgroundScheduler()

if _try_acquire_scheduler_master_lock():
    # Run daily at 9:00 AM to check for payment reminders
    scheduler.add_job(
        func=scheduled_payment_reminders,
        trigger=CronTrigger(hour=9, minute=0),  # 9:00 AM daily
        id="payment_reminders_job",
        name="Send payment reminders for due and overdue payments",
        replace_existing=True,
    )

    def scheduled_client_health_poll():
        """Poll each client's Home Assistant (Brain URL + token) for dashboard LEDs + WhatsApp."""
        try:
            from ha_client_health import refresh_all_clients_health

            refresh_all_clients_health(clients_collection)
            print("[SCHEDULER] Client Brain health poll completed")
        except Exception as e:
            print(f"[SCHEDULER] Client health poll error: {e}")

    _health_interval = int(os.environ.get("HEALTH_POLL_INTERVAL_MINUTES", "10"))
    if _health_interval > 0:
        from apscheduler.triggers.date import DateTrigger

        # First run soon after boot so alerts work without opening admin
        scheduler.add_job(
            func=scheduled_client_health_poll,
            trigger=DateTrigger(run_date=datetime.now() + timedelta(seconds=60)),
            id="client_ha_health_boot",
            name="Initial Brain health poll after startup",
            replace_existing=True,
        )
        scheduler.add_job(
            func=scheduled_client_health_poll,
            trigger=IntervalTrigger(minutes=_health_interval),
            id="client_ha_health_poll",
            name="Poll Brain (HA) health for all clients",
            replace_existing=True,
        )

    scheduler.start()
    atexit.register(lambda: scheduler.shutdown())
else:
    def scheduled_client_health_poll():
        pass

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT env variable
    app.run(host="0.0.0.0", port=port)
# hello