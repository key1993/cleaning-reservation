import os
from pymongo import MongoClient



MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://amerkiwan7723:oPQwW3nr3url61yM@cluster0.6jzip7b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")
DB_NAME = os.environ.get("DB_NAME", "cleaning_reservation")

try:
    client = MongoClient(MONGO_URI)
    # Test the connection
    client.admin.command('ping')
    print("✅ MongoDB connection successful")
    db = client[DB_NAME]
    
    # Collections
    reservations_collection = db["reservations"]
    clients_collection = db["clients"]
    
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")
    # Create empty collections as fallback
    reservations_collection = None
    clients_collection = None