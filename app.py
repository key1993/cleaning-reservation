from flask import Flask
from routes import routes
from admin import admin
import os
from pymongo import MongoClient
from db import db  # and optionally, reservations_collection if needed

app = Flask(__name__)

# Connect to MongoDB
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://amerkiwan7723:oPQwW3nr3url61yM@cluster0.6jzip7b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
client = MongoClient(MONGO_URI)
db = client.get_database("cleaning_reservation")

# Pass `db` to routes and admin
routes.db = db
admin.db = db

# Register blueprints
app.register_blueprint(routes)
app.register_blueprint(admin)

app.secret_key = "supersecretkey"

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Render sets PORT env variable
    app.run(host="0.0.0.0", port=port)
# hello