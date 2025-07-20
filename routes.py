from flask import Blueprint, request, jsonify, redirect
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

    msg = f"📢 New Enquiry!\n👤 {data['user_id']}\n📅 {data['date']} at {data['time_slot']}\n📍 {data['longitude']}, {data['latitude']} – Panels: {data['number_of_panels']}"
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
    try:
        r = reservations_collection.find_one({"_id": ObjectId(id)})
    except:
        return jsonify({"error": "Invalid ID format"}), 400
    if not r:
        return jsonify({"error": "Not found"}), 404
    r["_id"] = str(r["_id"])
    return jsonify(r)

@routes.route('/update_status', methods=['POST'])
def update_status():
    reservation_id = request.form['reservation_id']
    new_status = request.form['status']
    reservations_collection.update_one(
        {'_id': ObjectId(reservation_id)},
        {'$set': {'status': new_status}}
    )
    return redirect('/admin')  # ✅ Fixed redirect


@routes.route('/delete/<id>', methods=['POST'])
def delete_reservation(id):
    try:
        reservation = reservations_collection.find_one({"_id": ObjectId(id)})
        if not reservation:
            return jsonify({"error": "Reservation not found"}), 404

        reservations_collection.delete_one({"_id": ObjectId(id)})

        # WhatsApp message
        msg = (
            f"❌ Reservation Deleted:\n"
            f"👤 User: {reservation.get('user_id', 'Unknown')}\n"
            f"📅 Date: {reservation.get('date', 'N/A')} at {reservation.get('time_slot', 'N/A')}\n"
            f"📍 {reservation.get('longitude', 'N/A')}, {reservation.get('latitude', 'N/A')} – Panels: {reservation.get('number_of_panels', 'N/A')}"
        )
        send_whatsapp_message(msg)

        return jsonify({"message": "Reservation deleted"}), 200

    except Exception as e:
        return jsonify({"error": "Invalid reservation ID"}), 400
@routes.route('/update_cost', methods=['POST'])
def update_cost():
    reservation_id = request.form['reservation_id']
    cost = float(request.form['cost'])
    reservations_collection.update_one(
        {'_id': ObjectId(reservation_id)},
        {'$set': {'cost': cost}}
    )
    return redirect('/admin')

@routes.route('/cost/<id>', methods=['GET'])
def get_cost(id):
    try:
        reservation = reservations_collection.find_one({"_id": ObjectId(id)})
        if not reservation:
            return jsonify({"error": "Reservation not found"}), 404
        cost = reservation.get("cost")
        if cost is None:
            return jsonify({"message": "Cost not set"}), 200
        return jsonify({"cost": f"{cost} JOD"})
    except:
        return jsonify({"error": "Invalid ID format"}), 400

@routes.route('/approve/<id>', methods=['POST'])
def approve_reservation(id):
    try:
        reservation = reservations_collection.find_one({"_id": ObjectId(id)})
        if not reservation:
            return jsonify({"error": "Reservation not found"}), 404

        reservations_collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'status': 'Confirmed'}}
        )

        msg = (
            f"✅ Reservation Confirmed!\n"
            f"👤 User: {reservation.get('user_id', 'Unknown')}\n"
            f"📅 Date: {reservation.get('date', 'N/A')} at {reservation.get('time_slot', 'N/A')}\n"
            f"📍 Location: {reservation.get('longitude', 'N/A')}, {reservation.get('latitude', 'N/A')}\n"
            f"🔢 Panels: {reservation.get('number_of_panels', 'N/A')}"
        )
        send_whatsapp_message(msg)

        return jsonify({"message": "Reservation confirmed"}), 200

    except Exception as e:
        return jsonify({"error": "Invalid ID"}), 400

@routes.route('/deny/<id>', methods=['POST'])
def deny_reservation(id):
    try:
        reservation = reservations_collection.find_one({"_id": ObjectId(id)})
        if not reservation:
            return jsonify({"error": "Reservation not found"}), 404

        reservations_collection.update_one(
            {'_id': ObjectId(id)},
            {'$set': {'status': 'Canceled'}}
        )

        msg = (
            f"❌ Reservation Canceled\n"
            f"👤 User: {reservation.get('user_id', 'Unknown')}\n"
            f"🆔 ID: {id}"
        )
        send_whatsapp_message(msg)

        return jsonify({"message": "Reservation canceled"}), 200

    except Exception as e:
        return jsonify({"error": "Invalid ID"}), 400


