import os
from pymongo import MongoClient



MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://saraalthaher7723_db_user:5Errd8L7V2mawi9O@cluster0.7faafep.mongodb.net/?appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "cleaning_reservation")

client = MongoClient(MONGO_URI)
db = client["cleaning"]

# Collections
reservations_collection = db["reservations"]
clients_collection = db["clients"]
disabled_slots_collection = db["disabled_slots"]
cleaning_crew_collection = db["cleaning_crew"]
