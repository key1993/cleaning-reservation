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

@admin.route("/test_firebase_connection", methods=["GET"])
@admin_login_required
def test_firebase_connection():
    """Test Firebase connection and list users (for debugging)"""
    try:
        from firebase_service import firebase_app, auth
        
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
