from flask import Blueprint, request, jsonify, redirect, render_template, session
from db import reservations_collection, clients_collection, db
from models import validate_reservation
from bson.objectid import ObjectId

import requests
import urllib.parse
import os
from datetime import datetime, timedelta

def login_required(f):
    """Decorator to require user login for protected routes"""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

clients_collection = db['clients']

routes = Blueprint("routes", __name__)

WHATSAPP_PHONE = os.environ.get("WHATSAPP_PHONE", "+962796074185")
CALLMEBOT_API_KEY = os.environ.get("CALLMEBOT_API_KEY", "6312358")

def send_whatsapp_message(message):
    encoded = urllib.parse.quote(message)
    url = f"https://api.callmebot.com/whatsapp.php?phone={WHATSAPP_PHONE}&text={encoded}&apikey={CALLMEBOT_API_KEY}"
    try:
        response = requests.get(url)
        print("✅ WhatsApp sent:", response.status_code, response.text)
    except Exception as e:
        print("❌ WhatsApp failed:", e)

@routes.route("/")
def home():
    return render_template("index.html")

@routes.route("/reservations", methods=["POST"])
@login_required
def create_reservation():
    data = request.json
    
    # Automatically set user_id from session
    data["user_id"] = session.get("user_id")
    
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
    data["created_at"] = datetime.utcnow()
    result = reservations_collection.insert_one(data)

    msg = (
        f"📢 New Enquiry!\n"
        f"👤 {data.get('user_id', 'Unknown')}\n"
        f"📅 {data.get('date', 'N/A')} at {data.get('time_slot', 'N/A')}\n"
        f"📍 {data.get('longitude', 'N/A')}, {data.get('latitude', 'N/A')} – Panels: {data.get('number_of_panels', 'N/A')}"
    )
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
    return redirect('/admin')

@routes.route('/delete/<id>', methods=['POST'])
def delete_reservation(id):
    try:
        reservation = reservations_collection.find_one({"_id": ObjectId(id)})
        if not reservation:
            return jsonify({"error": "Reservation not found"}), 404

        reservations_collection.delete_one({"_id": ObjectId(id)})

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

        # Deny if already approved
        if reservation.get("status") == "Confirmed":
            return jsonify({"error": "Cost access denied: reservation already approved"}), 403

        # Ensure creation time is stored
        created_at = reservation.get("created_at")
        if not created_at:
            return jsonify({"error": "Missing creation timestamp"}), 400

        # Convert from string if needed (MongoDB might store as ISO string)
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)

        # Check time window: only valid for 3 minutes after creation
        if datetime.utcnow() > created_at + timedelta(minutes=600):
            return jsonify({"error": "Reservation Expired"}), 403

        cost = reservation.get("cost")
        if cost is None:
            return jsonify({"message": "Cost not set"}), 200

        return jsonify({"cost": f"{cost} JOD"})

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 400

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
            f"👤 {reservation.get('user_id', 'Unknown')}\n"
            f"📅 Date: {reservation.get('date', 'N/A')} at {reservation.get('time_slot', 'N/A')}\n"
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

@routes.route("/my_reservations")
@login_required
def my_reservations():
    user_id = session.get("user_id")
    reservations = list(reservations_collection.find({"user_id": user_id}))
    for r in reservations:
        r["_id"] = str(r["_id"])
    return jsonify(reservations)

@routes.route("/register_client", methods=["POST"])
def register_client():
    data = request.json
    required_fields = ["full_name", "signup_date", "phone", "location", "system_type", "ha_url", "ha_token"]


    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    clients_collection.insert_one(data)

    return jsonify({"message": "Client registered successfully"}), 200


@routes.route('/clients')
def show_clients():
    clients = list(clients_collection.find())
    return render_template('clients.html', clients=clients)


@routes.route("/admin")
def admin_panel():
    reservations = list(reservations_collection.find())
    clients = list(clients_collection.find())
    return render_template("admin.html", reservations=reservations, clients=clients)
@routes.route("/delete_client/<id>", methods=["POST"])
def delete_client(id):
    try:
        clients_collection.delete_one({"_id": ObjectId(id)})
        return redirect("/admin")
    except Exception:
        return jsonify({"error": "Failed to delete client"}), 400

@routes.route("/update_subscription/<id>", methods=["POST"])
def update_subscription(id):
    new_type = request.form.get("subscription_type")
    if new_type not in ["monthly", "yearly"]:
        return jsonify({"error": "Invalid subscription type"}), 400
    clients_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"subscription_type": new_type}}
    )
    return redirect("/admin")


@routes.route("/update_payment_method/<client_id>", methods=["POST"])
def update_payment_method(client_id):
    payment_method = request.form.get("payment_method")
    if payment_method not in ["monthly", "yearly"]:
        return redirect("/admin")

    now = datetime.now()
    next_payment = now + timedelta(days=30 if payment_method == "monthly" else 365)
    formatted_next_payment = next_payment.strftime("%Y-%m-%d")

    clients_collection.update_one(
        {"_id": ObjectId(client_id)},
        {"$set": {"payment_method": payment_method, "next_payment_date": formatted_next_payment}}
    )
    return redirect("/admin")

@routes.route("/check_payment_reminders")
def check_payment_reminders():
    today_str = datetime.now().strftime("%Y-%m-%d")
    clients = list(clients_collection.find({"next_payment_date": today_str}))

    for c in clients:
        name = c.get("full_name", "Unknown")
        phone = c.get("phone", "Unknown")
        payment_method = c.get("payment_method", "Unknown")
        msg = f"💰 Payment Reminder\nClient: {name}\nPhone: {phone}\nMethod: {payment_method}\nPlease proceed with the payment today."
        send_whatsapp_message(msg)

    return jsonify({"message": f"✅ {len(clients)} reminder(s) sent."})
