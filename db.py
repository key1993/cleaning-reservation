import os
from pymongo import MongoClient



MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://amerkiwan7723:oPQwW3nr3url61yM@cluster0.6jzip7b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "cleaning_reservation")

client = MongoClient(MONGO_URI)
db = client["cleaning"]

# Collections
reservations_collection = db["reservations"]
clients_collection = db["clients"]
disabled_slots_collection = db["disabled_slots"]
cleaning_crew_collection = db["cleaning_crew"]