from flask import Blueprint, render_template, session, redirect, request, url_for
from db import reservations_collection
from bson import ObjectId

admin = Blueprint("admin", __name__)

@admin.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form["username"] == "admin" and request.form["password"] == "admin":
            session["logged_in"] = True
            return redirect("/admin")
        else:
            return "❌ Invalid credentials", 403
    return '''
        <form method="post">
            <h2>Admin Login</h2>
            <input name="username" placeholder="Username"><br>
            <input name="password" type="password" placeholder="Password"><br>
            <button type="submit">Login</button>
        </form>
    '''

@admin.route("/admin")
def admin_dashboard():
    if not session.get("logged_in"):
        return redirect(url_for("admin.login"))

    # Clear session every time to force re-login
    session.pop("logged_in", None)

    reservations = list(reservations_collection.find().sort("date", 1))
    for r in reservations:
        r["_id"] = str(r["_id"])
    return render_template("admin.html", reservations=reservations)

@admin.route("/update_status", methods=["POST"])
def update_status():
    if not session.get("logged_in"):
        return redirect(url_for("admin.login"))

    reservation_id = request.form["reservation_id"]
    new_status = request.form["status"]
    reservations_collection.update_one(
        {"_id": ObjectId(reservation_id)},
        {"$set": {"status": new_status}}
    )
    return redirect("/admin")
