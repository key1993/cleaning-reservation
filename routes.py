from flask import Blueprint, request, jsonify
from db import reservations_collection
from models import validate_reservation
from bson.objectid import ObjectId
import requests
import urllib.parse
import os

routes = Blueprint("routes", __name__)

WHATSAPP_PHONE = os.environ.get("WHATSAPP_PHONE", "+962796074185")
CALLMEBOT_API_KEY = os.environ.get("CALLMEBOT_API_KEY", "6312358")

def send_whatsapp_message(message):
    encoded = urllib.parse.quote(message)
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={encoded}&apikey={CALLMEBOT_API_KEY}"
    try:
        requests.get(url)
    except Exception as e:
        print("❌ WhatsApp failed:", e)

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

    msg = f"📢 New Reservation!\n👤 {data['user_id']}\n📅 {data['date']} at {data['time_slot']}\n📍 {data['longitude']}, {data['latitude']} – Panels: {data['number_of_panels']}"
    send_whatsapp_message(msg)

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

@app.route('/cancel', methods=['DELETE'])
def cancel_reservation():
    data = request.get_json()
    user_id = data.get('user_id')
    date = data.get('date')
    time_slot = data.get('time_slot')

    if not user_id or not date or not time_slot:
        return jsonify({'error': 'Missing required fields'}), 400

    result = reservations_collection.delete_one({
        'user_id': user_id,
        'date': date,
        'time_slot': time_slot
    })

    if result.deleted_count == 0:
        return jsonify({'message': 'No matching reservation found'}), 404

    send_whatsapp_message(f"❌ Reservation cancelled:\n🧑 User: {user_id}\n📅 Date: {date}\n🕒 Slot: {time_slot}")
    return jsonify({'message': 'Reservation cancelled successfully'}), 200
