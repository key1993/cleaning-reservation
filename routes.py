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

@routes.route("/test")
def test():
    return "Application is working! Database status: " + ("Connected" if reservations_collection is not None else "Not Connected")

@routes.route("/reservations", methods=["POST"])
def create_reservation():
    data = request.json
    
    # Use user_id from request data if provided, otherwise use session or default to "Guest"
    if "user_id" not in data:
        data["user_id"] = session.get("user_id", "Guest")
    
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
        f"👤 User ID: {data.get('user_id', 'Unknown')}\n"
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
            f"👤 User ID: {reservation.get('user_id', 'Unknown')}\n"
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
            f"👤 User ID: {reservation.get('user_id', 'Unknown')}\n"
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
    required_fields = ["full_name", "signup_date", "phone", "location", "system_type", "ha_url", "ha_token", "subscription_type"]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400

    # Calculate initial next payment date based on signup date and subscription type
    signup_date = datetime.strptime(data["signup_date"], "%Y-%m-%d")
    subscription_type = data.get("subscription_type", "monthly")
    
    if subscription_type == "monthly":
        next_payment_date = signup_date + timedelta(days=30)
    else:  # yearly
        next_payment_date = signup_date + timedelta(days=365)
    
    data["next_payment_date"] = next_payment_date.strftime("%Y-%m-%d")
    data["subscription_type"] = subscription_type

    clients_collection.insert_one(data)

    return jsonify({"message": "Client registered successfully"}), 200


@routes.route('/clients')
def show_clients():
    clients = list(clients_collection.find())
    return render_template('clients.html', clients=clients)


@routes.route("/admin")
def admin_panel():
    try:
        if reservations_collection is None or clients_collection is None:
            return render_template("error.html", error_message="Database connection error. Please check your MongoDB connection."), 500
        
        reservations = list(reservations_collection.find())
        clients = list(clients_collection.find())
        return render_template("admin.html", reservations=reservations, clients=clients)
    except Exception as e:
        print(f"Error in admin panel: {e}")
        return render_template("error.html", error_message=f"Error loading admin panel: {str(e)}"), 500
@routes.route("/delete_client/<id>", methods=["POST"])
def delete_client(id):
    try:
        clients_collection.delete_one({"_id": ObjectId(id)})
        return redirect("/admin")
    except Exception:
        return jsonify({"error": "Failed to delete client"}), 400

@routes.route("/delete_clients_bulk", methods=["POST"])
def delete_clients_bulk():
    """Delete multiple clients at once"""
    try:
        data = request.json
        client_ids = data.get("client_ids", [])
        
        if not client_ids:
            return jsonify({"success": False, "error": "No clients selected"}), 400
        
        # Convert string IDs to ObjectId
        object_ids = [ObjectId(client_id) for client_id in client_ids]
        
        # Delete all selected clients
        result = clients_collection.delete_many({"_id": {"$in": object_ids}})
        
        return jsonify({
            "success": True,
            "message": f"Successfully deleted {result.deleted_count} client(s)"
        }), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@routes.route("/update_subscription/<id>", methods=["POST"])
def update_subscription(id):
    new_type = request.form.get("subscription_type")
    if new_type not in ["monthly", "yearly"]:
        return jsonify({"error": "Invalid subscription type"}), 400
    
    # Get current client data
    client = clients_collection.find_one({"_id": ObjectId(id)})
    if not client:
        return jsonify({"error": "Client not found"}), 404
    
    # Calculate next payment date based on signup date and subscription type
    signup_date = datetime.strptime(client.get("signup_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
    
    if new_type == "monthly":
        # Calculate months since signup and add to get next payment
        months_since_signup = (datetime.now().year - signup_date.year) * 12 + (datetime.now().month - signup_date.month)
        next_payment_date = signup_date + timedelta(days=30 * (months_since_signup + 1))
    else:  # yearly
        # Calculate years since signup and add to get next payment
        years_since_signup = datetime.now().year - signup_date.year
        next_payment_date = signup_date + timedelta(days=365 * (years_since_signup + 1))
    
    formatted_next_payment = next_payment_date.strftime("%Y-%m-%d")
    
    clients_collection.update_one(
        {"_id": ObjectId(id)},
        {"$set": {
            "subscription_type": new_type,
            "next_payment_date": formatted_next_payment
        }}
    )
    return redirect("/admin")

@routes.route("/confirm_payment", methods=["POST"])
def confirm_payment():
    data = request.json
    client_id = data.get("clientId")
    subscription_type = data.get("subscriptionType")
    
    if not client_id or not subscription_type:
        return jsonify({"success": False, "error": "Missing required data"}), 400
    
    try:
        # Get current client data
        client = clients_collection.find_one({"_id": ObjectId(client_id)})
        if not client:
            return jsonify({"success": False, "error": "Client not found"}), 404
        
        # Calculate new next payment date based on current next_payment_date
        current_next_payment = datetime.strptime(client.get("next_payment_date", datetime.now().strftime("%Y-%m-%d")), "%Y-%m-%d")
        
        if subscription_type == "monthly":
            new_next_payment = current_next_payment + timedelta(days=30)
        else:  # yearly
            new_next_payment = current_next_payment + timedelta(days=365)
        
        formatted_new_payment = new_next_payment.strftime("%Y-%m-%d")
        
        # Update the client's next payment date
        clients_collection.update_one(
            {"_id": ObjectId(client_id)},
            {"$set": {"next_payment_date": formatted_new_payment}}
        )
        
        # Send WhatsApp confirmation message
        client_name = client.get("full_name", "Unknown")
        msg = (
            f"✅ Payment Confirmed!\n"
            f"👤 Client: {client_name}\n"
            f"📅 Next Payment: {formatted_new_payment}\n"
            f"💰 Subscription: {subscription_type.capitalize()}"
        )
        send_whatsapp_message(msg)
        
        return jsonify({"success": True, "message": "Payment confirmed and next payment date updated"}), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

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

def process_payment_reminders():
    """
    Core function to check and send payment reminders.
    Can be called by scheduler or manually via route.
    Returns a dict with results.
    """
    today = datetime.now()
    
    # Check for clients whose payment is due in 2 days
    two_days_from_now = today + timedelta(days=2)
    two_days_str = two_days_from_now.strftime("%Y-%m-%d")
    
    clients_due_soon = list(clients_collection.find({"next_payment_date": two_days_str}))
    
    # Also check for overdue payments
    today_str = today.strftime("%Y-%m-%d")
    overdue_clients = list(clients_collection.find({"next_payment_date": {"$lt": today_str}}))
    
    total_reminders = 0
    
    # Send reminders for payments due in 2 days
    for c in clients_due_soon:
        name = c.get("full_name", "Unknown")
        phone = c.get("phone", "Unknown")
        subscription_type = c.get("subscription_type", "Unknown")
        next_payment = c.get("next_payment_date", "Unknown")
        
        msg = (
            f"⚠️ Payment Due Soon!\n"
            f"👤 Client: {name}\n"
            f"📱 Phone: {phone}\n"
            f"💰 Subscription: {subscription_type.capitalize()}\n"
            f"📅 Due Date: {next_payment}\n"
            f"⏰ Payment is due in 2 days!"
        )
        send_whatsapp_message(msg)
        total_reminders += 1
    
    # Send reminders for overdue payments
    for c in overdue_clients:
        name = c.get("full_name", "Unknown")
        phone = c.get("phone", "Unknown")
        subscription_type = c.get("subscription_type", "Unknown")
        next_payment = c.get("next_payment_date", "Unknown")
        
        days_overdue = (today - datetime.strptime(next_payment, "%Y-%m-%d")).days
        
        msg = (
            f"🚨 PAYMENT OVERDUE!\n"
            f"👤 Client: {name}\n"
            f"📱 Phone: {phone}\n"
            f"💰 Subscription: {subscription_type.capitalize()}\n"
            f"📅 Due Date: {next_payment}\n"
            f"⏰ Overdue by: {days_overdue} day(s)"
        )
        send_whatsapp_message(msg)
        total_reminders += 1
    
    return {
        "message": f"✅ {total_reminders} reminder(s) sent.",
        "due_soon": len(clients_due_soon),
        "overdue": len(overdue_clients),
        "total": total_reminders
    }

@routes.route("/check_payment_reminders")
def check_payment_reminders():
    """Route endpoint for checking payment reminders (manual trigger)"""
    result = process_payment_reminders()
    return jsonify(result)

@routes.route("/send_payment_reminders")
def send_payment_reminders():
    """Manual trigger for payment reminders (for testing)"""
    return check_payment_reminders()
