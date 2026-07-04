from flask import Blueprint, render_template, session, redirect, request, url_for, jsonify, make_response
from db import reservations_collection, clients_collection, cleaning_crew_collection
from bson import ObjectId
from functools import wraps
from datetime import datetime, timedelta
import json

admin = Blueprint("admin", __name__)


def _json_safe(value):
    """Convert BSON/Datetime objects to JSON-safe values recursively."""
    if isinstance(value, dict):
        return {k: _json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_safe(v) for v in value]
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    return value

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
        cleaning_crew = list(cleaning_crew_collection.find().sort("created_at", -1))
        
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

        # Note: overdue-payment auto-disable is handled by the daily scheduled job
        # (scheduled_payment_reminders -> process_payment_reminders in routes.py),
        # not here, so that manually re-enabling an account from this dashboard sticks
        # instead of being immediately reverted on the next page load.

        # Poll each client's Brain (HA) for Pi reachability + grid/solar input_booleans
        try:
            from ha_client_health import refresh_all_clients_health

            refresh_all_clients_health(clients_collection)
            clients = list(clients_collection.find())
        except Exception as health_err:
            print(f"⚠️ Client health poll failed: {health_err}")

        for r in reservations:
            r["_id"] = str(r["_id"])
        for crew in cleaning_crew:
            crew["_id"] = str(crew["_id"])
        return render_template("admin.html", reservations=reservations, clients=clients, cleaning_crew=cleaning_crew)
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

@admin.route("/admin/disable_crew_account/<crew_id>", methods=["POST"])
@admin_login_required
def disable_crew_account(crew_id):
    """Disable a cleaning crew member's Firebase account"""
    try:
        from firebase_service import disable_firebase_user
        
        crew = cleaning_crew_collection.find_one({"_id": ObjectId(crew_id)})
        if not crew:
            return jsonify({"success": False, "error": "Crew member not found"}), 404
        
        firebase_uid = crew.get("firebase_uid")
        if not firebase_uid:
            return jsonify({"success": False, "error": "Crew member does not have a Firebase account linked"}), 400
        
        if disable_firebase_user(firebase_uid):
            cleaning_crew_collection.update_one(
                {"_id": ObjectId(crew_id)},
                {"$set": {"account_disabled": True, "account_disabled_date": datetime.now().strftime("%Y-%m-%d")}}
            )
            return jsonify({"success": True, "message": "Crew account disabled successfully"}), 200
        else:
            return jsonify({"success": False, "error": "Failed to disable Firebase account"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@admin.route("/admin/enable_crew_account/<crew_id>", methods=["POST"])
@admin_login_required
def enable_crew_account(crew_id):
    """Enable a cleaning crew member's Firebase account"""
    try:
        from firebase_service import enable_firebase_user
        
        crew = cleaning_crew_collection.find_one({"_id": ObjectId(crew_id)})
        if not crew:
            return jsonify({"success": False, "error": "Crew member not found"}), 404
        
        firebase_uid = crew.get("firebase_uid")
        if not firebase_uid:
            return jsonify({"success": False, "error": "Crew member does not have a Firebase account linked"}), 400
        
        if enable_firebase_user(firebase_uid):
            cleaning_crew_collection.update_one(
                {"_id": ObjectId(crew_id)},
                {"$set": {"account_disabled": False}, "$unset": {"account_disabled_date": ""}}
            )
            return jsonify({"success": True, "message": "Crew account enabled successfully"}), 200
        else:
            return jsonify({"success": False, "error": "Failed to enable Firebase account"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@admin.route("/admin/delete_crew_firebase_account/<crew_id>", methods=["POST"])
@admin_login_required
def delete_crew_firebase_account(crew_id):
    """Delete a cleaning crew member's Firebase account"""
    try:
        from firebase_service import delete_firebase_user
        
        crew = cleaning_crew_collection.find_one({"_id": ObjectId(crew_id)})
        if not crew:
            return jsonify({"success": False, "error": "Crew member not found"}), 404
        
        firebase_uid = crew.get("firebase_uid")
        if not firebase_uid:
            return jsonify({"success": False, "error": "Crew member does not have a Firebase account linked"}), 400
        
        ok, err = delete_firebase_user(firebase_uid)
        if ok:
            cleaning_crew_collection.update_one(
                {"_id": ObjectId(crew_id)},
                {"$unset": {"firebase_uid": "", "account_disabled": "", "account_disabled_date": ""}}
            )
            return jsonify({"success": True, "message": "Firebase account deleted successfully"}), 200
        return jsonify({"success": False, "error": err or "Failed to delete Firebase account"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@admin.route("/admin/reset_crew_password/<crew_id>", methods=["POST"])
@admin_login_required
def reset_crew_password(crew_id):
    """Reset password for a cleaning crew member's Firebase account"""
    try:
        from firebase_service import reset_firebase_user_password
        
        crew = cleaning_crew_collection.find_one({"_id": ObjectId(crew_id)})
        if not crew:
            return jsonify({"success": False, "error": "Crew member not found"}), 404
        
        firebase_uid = crew.get("firebase_uid")
        if not firebase_uid:
            return jsonify({"success": False, "error": "Crew member does not have a Firebase account linked"}), 400
        
        temp_password = reset_firebase_user_password(firebase_uid)
        
        if temp_password:
            crew_name = crew.get("full_name", "Unknown")
            return jsonify({
                "success": True,
                "message": f"Password reset successfully for {crew_name}",
                "temp_password": temp_password,
                "note": "Please share this temporary password with the crew member. They should change it after logging in."
            }), 200
        else:
            return jsonify({"success": False, "error": "Failed to reset password"}), 500
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@admin.route("/admin/delete_crew/<crew_id>", methods=["POST"])
@admin_login_required
def delete_crew(crew_id):
    """Delete a cleaning crew member"""
    try:
        crew = cleaning_crew_collection.find_one({"_id": ObjectId(crew_id)})
        if not crew:
            return jsonify({"success": False, "error": "Crew member not found"}), 404
        
        # Optionally delete Firebase account first
        firebase_uid = crew.get("firebase_uid")
        if firebase_uid:
            from firebase_service import delete_firebase_user
            delete_firebase_user(firebase_uid)  # best-effort; crew row is removed regardless
        
        cleaning_crew_collection.delete_one({"_id": ObjectId(crew_id)})
        return jsonify({"success": True, "message": "Crew member deleted successfully"}), 200
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@admin.route("/admin/generate_ebsher_code", methods=["POST"])
@admin_login_required
def generate_ebsher_code():
    """Generate a one-time registration code for crew members"""
    try:
        from firebase_service import generate_ebsher_code as generate_code
        
        result = generate_code()
        
        if result.get("success"):
            return jsonify({
                "success": True,
                "code": result.get("code"),
                "expires_at": result.get("expires_at"),
                "expires_in_minutes": result.get("expires_in_minutes", 5),
                "message": f"Code generated successfully. Valid for 5 minutes."
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": result.get("error", "Failed to generate code")
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Internal server error: {str(e)}"
        }), 500


@admin.route("/admin/client_backup/<client_id>", methods=["GET"])
@admin_login_required
def download_client_backup(client_id):
    """Download one client backup JSON with latest baseline snapshots."""
    try:
        client = clients_collection.find_one({"_id": ObjectId(client_id)})
        if not client:
            return jsonify({"success": False, "error": "Client not found"}), 404

        # Try live refresh of baseline values before export.
        try:
            from routes import fetch_client_backup_baselines

            baseline = fetch_client_backup_baselines(client)
            clients_collection.update_one(
                {"_id": client["_id"]},
                {
                    "$set": {
                        "backup_home_monthly_baseline": baseline.get("home_monthly_baseline"),
                        "backup_solar_monthly_baseline": baseline.get("solar_monthly_baseline"),
                        "backup_baselines_updated_at": datetime.utcnow(),
                        "backup_baselines_account_id": baseline.get("account_id"),
                        "backup_home_baseline_fetch_ok": baseline.get("home_fetch_ok"),
                        "backup_solar_baseline_fetch_ok": baseline.get("solar_fetch_ok"),
                        "backup_home_baseline_fetch_error": baseline.get("home_fetch_error"),
                        "backup_solar_baseline_fetch_error": baseline.get("solar_fetch_error"),
                    }
                },
            )
            client = clients_collection.find_one({"_id": ObjectId(client_id)}) or client
        except Exception as baseline_error:
            print(f"⚠️ Backup baseline refresh failed for {client_id}: {baseline_error}")

        payload = {
            "exported_at": datetime.utcnow().isoformat(),
            "client": _json_safe(client),
        }
        body = json.dumps(payload, indent=2, ensure_ascii=True)
        file_hint = str(client.get("account_number") or client_id).replace(" ", "_")
        filename = f"client_backup_{file_hint}.json"

        response = make_response(body)
        response.headers["Content-Type"] = "application/json; charset=utf-8"
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@admin.route("/admin/update_client_pi/<client_id>", methods=["POST"])
@admin_login_required
def update_client_pi(client_id):
    """Assign (or unassign) a Raspberry Pi to a client record."""
    pi_id = (request.get_json() or {}).get("pi_id", "")
    try:
        clients_collection.update_one(
            {"_id": ObjectId(client_id)},
            {"$set": {"pi_id": pi_id}},
        )
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
