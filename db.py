from pymongo import MongoClient
import os

MONGO_URI = "mongodb+srv://amerkiwan7723:oPQwW3nr3url61yM@cluster0.6jzip7b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(os.environ.get("MONGO_URI"))
db = client.get_default_database()
reservations_collection = db["reservations"]
