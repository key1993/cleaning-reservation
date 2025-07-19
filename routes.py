from flask import Blueprint, request, jsonify
from db import reservations_collection
from models import validate_reservation
from bson.objectid import ObjectId
import requests
import os
import urllib.parse

routes = Blueprint("routes", __name__)

def send_whatsapp_message(user_id, date, time_slot):
    # Placeholder - Fill in with Twilio or WhatsApp Cloud API details
    print(f"WhatsApp Message: New reservation by {user_id} on {date} at {time_slot}")

@routes.route("/reservations", methods=["POST"])
def create_reservation():
    data = request.json
    is_valid, msg = validate_reservation(data)
    if not is_valid:
        return jsonify({"error": msg}), 400

    conflict = reservations_collection.find_one({
        "date": data["date"],
        "time_slot": data["time_slot"]
    })
    if conflict:
        return jsonify({"error": "Time slot already booked"}), 409

    data["status"] = "pending"
    result = reservations_collection.insert_one(data)
    send_whatsapp_message(data["user_id"], data["date"], data["time_slot"])
    return jsonify({"message": "Reservation created", "id": str(result.inserted_id)})

@routes.route("/reservations", methods=["GET"])
def list_reservations():
    reservations = list(reservations_collection.find())
    for r in reservations:
        r["_id"] = str(r["_id"])
    return jsonify(reservations)

@routes.route("/reservations/<id>", methods=["GET"])
def get_reservation(id):
    r = reservations_collection.find_one({"_id": ObjectId(id)})
    if not r:
        return jsonify({"error": "Not found"}), 404
    r["_id"] = str(r["_id"])
    return jsonify(r)

@routes.route("/reservations/<id>", methods=["DELETE"])
def cancel_reservation(id):
    result = reservations_collection.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        return jsonify({"error": "Not found"}), 404
    return jsonify({"message": "Reservation canceled"})
def send_whatsapp_message(user_id, date, time_slot):
    phone = "+962796074185"  # Replace with your full number, e.g., +9627XXXXXXX
    apikey = "6312358"
    text = f"📢 New Cleaning Reservation!\n👤 User: {user_id}\n📅 Date: {date}\n🕒 Time: {time_slot}"
    encoded_text = urllib.parse.quote(text)

    url = f"https://api.callmebot.com/whatsapp.php?phone={phone}&text={encoded_text}&apikey={apikey}"
    try:
        response = requests.get(url)
        print("✅ WhatsApp sent:", response.status_code)
    except Exception as e:
        print("❌ WhatsApp failed:", e)
