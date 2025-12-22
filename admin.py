from flask import Blueprint, render_template, session, redirect, request, url_for, jsonify
from db import reservations_collection, clients_collection
from bson import ObjectId
from functools import wraps
from datetime import datetime, timedelta

admin = Blueprint("admin", __name__)

def admin_login_required(f):
    """Decorator to require admin login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        
        # Check session timeout (5 minutes) - client-side handles most of this
        # But we also check server-side for security
        login_time_str = session.get("admin_login_time")
        if login_time_str:
            try:
                login_time = datetime.fromisoformat(login_time_str)
                if datetime.now() - login_time > timedelta(minutes=5):
                    # Session expired - logout
                    session.pop("admin_logged_in", None)
                    session.pop("admin_username", None)
                    session.pop("admin_login_time", None)
                    return redirect(url_for("admin.login"))
                else:
                    # Reset login time on each request to extend session
                    session["admin_login_time"] = datetime.now().isoformat()
            except Exception as e:
                print(f"Error checking session timeout: {e}")
        
        return f(*args, **kwargs)
    return decorated_function

@admin.route("/login", methods=["GET", "POST"])
def login():
    # If already logged in, redirect to admin panel
    if session.get("admin_logged_in"):
        return redirect(url_for("admin.admin_dashboard"))
    
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        
        # Check credentials (you can change these or use database)
        if username == "admin" and password == "admin":
            session["admin_logged_in"] = True
            session["admin_username"] = username
            session["admin_login_time"] = datetime.now().isoformat()
            return redirect(url_for("admin.admin_dashboard"))
        else:
            return render_template("admin_login.html", error="Invalid username or password")
    
    return render_template("admin_login.html")

@admin.route("/admin")
@admin_login_required
def admin_dashboard():
    try:
        reservations = list(reservations_collection.find().sort("date", 1))
        clients = list(clients_collection.find())
        
        # Auto-link Firebase accounts for clients with email but no firebase_uid
        from firebase_service import get_firebase_user_by_email
        for client in clients:
            if client.get("email") and not client.get("firebase_uid"):
                try:
                    firebase_user = get_firebase_user_by_email(client["email"])
                    if firebase_user:
                        clients_collection.update_one(
                            {"_id": client["_id"]},
                            {"$set": {"firebase_uid": firebase_user.uid}}
                        )
                        print(f"✅ Auto-linked Firebase account for {client.get('full_name')} ({client.get('email')})")
                except Exception as e:
                    print(f"⚠️ Could not auto-link Firebase for {client.get('email')}: {e}")
        
        # Refresh clients list after auto-linking
        clients = list(clients_collection.find())
        
        # Check payment status and auto-disable Firebase/widget if overdue
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")
        for client in clients:
            next_payment = client.get("next_payment_date")
            if next_payment:
                try:
                    payment_date = datetime.strptime(next_payment, "%Y-%m-%d")
                    if payment_date < today:
                        # Payment is overdue - check if payment was confirmed
                        # Check if there's a payment confirmation (we'll check if payment_date was updated recently)
                        # For now, if overdue, disable Firebase and widget
                        firebase_uid = client.get("firebase_uid")
                        if firebase_uid:
                            from firebase_service import disable_firebase_user
                            # Disable Firebase account if not already disabled
                            if not client.get("account_disabled", False):
                                if disable_firebase_user(firebase_uid):
                                    clients_collection.update_one(
                                        {"_id": client["_id"]},
                                        {"$set": {
                                            "account_disabled": True,
                                            "account_disabled_date": today_str
                                        }}
                                    )
                                    print(f"🔒 Auto-disabled Firebase for overdue client: {client.get('full_name')}")
                            
                            # Disable widget if not already disabled
                            if not client.get("external_widget_disabled", False):
                                clients_collection.update_one(
                                    {"_id": client["_id"]},
                                    {"$set": {"external_widget_disabled": True}}
                                )
                                # Send disable request to external widget
                                try:
                                    import requests
                                    ha_url = client.get("ha_url", "").rstrip("/")
                                    ha_token = client.get("ha_token", "")
                                    if ha_url and ha_token:
                                        widget_url = f"{ha_url}/api/widget/disable"
                                        widget_payload = {
                                            "client_id": str(client["_id"]),
                                            "client_name": client.get("full_name", "Unknown"),
                                            "disabled": True,
                                            "ha_token": ha_token,
                                            "timestamp": datetime.utcnow().isoformat()
                                        }
                                        requests.post(
                                            widget_url,
                                            json=widget_payload,
                                            headers={"Content-Type": "application/json"},
                                            timeout=10
                                        )
                                        print(f"🔒 Auto-disabled widget for overdue client: {client.get('full_name')}")
                                except Exception as widget_error:
                                    print(f"⚠️ Could not disable widget for {client.get('full_name')}: {widget_error}")
                except Exception as e:
                    print(f"⚠️ Error checking payment status for {client.get('full_name')}: {e}")
        
        # Refresh clients list again after auto-disable
        clients = list(clients_collection.find())
        
        for r in reservations:
            r["_id"] = str(r["_id"])
        return render_template("admin.html", reservations=reservations, clients=clients)
    except Exception as e:
        print(f"Error in admin dashboard: {e}")
        return render_template("error.html", error_message=f"Error loading admin dashboard: {str(e)}"), 500

@admin.route("/admin/logout")
@admin_login_required
def logout():
    session.pop("admin_logged_in", None)
    session.pop("admin_username", None)
    session.pop("admin_login_time", None)
    return redirect(url_for("admin.login"))

@admin.route("/update_status", methods=["POST"])
@admin_login_required
def update_status():
    reservation_id = request.form["reservation_id"]
    new_status = request.form["status"]
    reservations_collection.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"status": new_status}}
    )
    return redirect("/admin")

@admin.route("/admin/test_firebase_connection", methods=["GET"])
@admin_login_required
def test_firebase_connection():
    """Test Firebase connection and list users (for debugging)"""
    try:
        from firebase_service import firebase_app
        from firebase_admin import auth
        
        if firebase_app is None:
            return jsonify({
                "success": False,
                "error": "Firebase is not initialized",
                "details": "Check FIREBASE_CREDENTIALS_PATH or FIREBASE_CREDENTIALS_JSON environment variable"
            }), 500
        
        # Try to list a few users to verify connection
        try:
            # List users (limited to 10 for testing)
            page = auth.list_users(max_results=10)
            users = []
            for user in page.users:
                users.append({
                    "uid": user.uid,
                    "email": user.email,
                    "disabled": user.disabled,
                    "email_verified": user.email_verified
                })
            
            return jsonify({
                "success": True,
                "message": "Firebase connection successful",
                "users_found": len(users),
                "users": users
            }), 200
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Firebase connection test failed: {str(e)}",
                "error_type": type(e).__name__
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error testing Firebase: {str(e)}"
        }), 500
