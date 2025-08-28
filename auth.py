from flask import Blueprint, request, jsonify, session, redirect, url_for, render_template
from werkzeug.security import generate_password_hash, check_password_hash
from db import db
from bson import ObjectId
from functools import wraps
from datetime import datetime

auth = Blueprint("auth", __name__)

# Get users collection
users_collection = db['users']

def login_required(f):
    """Decorator to require user login for protected routes"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            return jsonify({"error": "Login required"}), 401
        return f(*args, **kwargs)
    return decorated_function

@auth.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    
    data = request.json if request.is_json else request.form
    
    # Validate required fields
    required_fields = ["username", "password", "email", "full_name", "phone"]
    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required fields"}), 400
    
    # Check if username already exists
    if users_collection.find_one({"username": data["username"]}):
        return jsonify({"error": "Username already exists"}), 409
    
    # Check if email already exists
    if users_collection.find_one({"email": data["email"]}):
        return jsonify({"error": "Email already exists"}), 409
    
    # Create user document
    user_data = {
        "username": data["username"],
        "password": generate_password_hash(data["password"]),
        "email": data["email"],
        "full_name": data["full_name"],
        "phone": data["phone"],
        "created_at": datetime.utcnow(),
        "is_active": True
    }
    
    result = users_collection.insert_one(user_data)
    
    return jsonify({"message": "User registered successfully", "user_id": str(result.inserted_id)}), 201

@auth.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    
    data = request.json if request.is_json else request.form
    
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"error": "Username and password required"}), 400
    
    # Find user by username
    user = users_collection.find_one({"username": username})
    
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid username or password"}), 401
    
    if not user.get("is_active", True):
        return jsonify({"error": "Account is deactivated"}), 403
    
    # Store user info in session
    session["user_id"] = str(user["_id"])
    session["username"] = user["username"]
    session["full_name"] = user["full_name"]
    
    return jsonify({"message": "Login successful", "user": {
        "username": user["username"],
        "full_name": user["full_name"],
        "email": user["email"]
    }}), 200

@auth.route("/logout")
def logout():
    session.clear()
    return jsonify({"message": "Logout successful"}), 200

@auth.route("/profile")
@login_required
def profile():
    user_id = session.get("user_id")
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    
    if not user:
        session.clear()
        return jsonify({"error": "User not found"}), 404
    
    return jsonify({
        "username": user["username"],
        "email": user["email"],
        "full_name": user["full_name"],
        "phone": user["phone"],
        "created_at": user["created_at"].isoformat() if user.get("created_at") else None
    }), 200

@auth.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@auth.route("/change_password", methods=["POST"])
@login_required
def change_password():
    data = request.json if request.is_json else request.form
    
    current_password = data.get("current_password")
    new_password = data.get("new_password")
    
    if not current_password or not new_password:
        return jsonify({"error": "Current and new password required"}), 400
    
    user_id = session.get("user_id")
    user = users_collection.find_one({"_id": ObjectId(user_id)})
    
    if not check_password_hash(user["password"], current_password):
        return jsonify({"error": "Current password is incorrect"}), 401
    
    # Update password
    users_collection.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"password": generate_password_hash(new_password)}}
    )
    
    return jsonify({"message": "Password changed successfully"}), 200