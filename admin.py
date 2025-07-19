from flask import Blueprint, render_template, session, redirect, request, url_for
from db import reservations_collection

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

    reservations = list(reservations_collection.find().sort("date", 1))
    for r in reservations:
        r["_id"] = str(r["_id"])
    return render_template("admin.html", reservations=reservations)
