from flask import Flask
from routes import routes, process_payment_reminders
from admin import admin
from auth import auth
import os
from pymongo import MongoClient
from db import db  # and optionally, reservations_collection if needed
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit

app = Flask(__name__)

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

# Set up automated payment reminder scheduler
def scheduled_payment_reminders():
    """Function called by scheduler to send payment reminders automatically"""
    try:
        result = process_payment_reminders()
        print(f"[SCHEDULER] Payment reminders sent: {result['total']} total ({result['due_soon']} due soon, {result['overdue']} overdue)")
    except Exception as e:
        print(f"[SCHEDULER] Error sending payment reminders: {e}")

# Initialize scheduler
scheduler = BackgroundScheduler()
# Run daily at 9:00 AM to check for payment reminders
scheduler.add_job(
    func=scheduled_payment_reminders,
    trigger=CronTrigger(hour=9, minute=0),  # 9:00 AM daily
    id='payment_reminders_job',
    name='Send payment reminders for due and overdue payments',
    replace_existing=True
)
scheduler.start()

# Shut down the scheduler when exiting the app
atexit.register(lambda: scheduler.shutdown())

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT env variable
    app.run(host="0.0.0.0", port=port)
# hello