from pymongo import MongoClient

MONGO_URI = "mongodb+srv://amerkiwan7723:oPQwW3nr3url61yM@cluster0.6jzip7b.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["cleaning_reservations"]
reservations_collection = db["reservations"]
