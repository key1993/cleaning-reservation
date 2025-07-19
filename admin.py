from flask import Blueprint, render_template
from db import reservations_collection

admin = Blueprint("admin", __name__)

@admin.route("/admin")
def admin_dashboard():
    reservations = list(reservations_collection.find().sort("date", 1))
    for r in reservations:
        r["_id"] = str(r["_id"])
    return render_template("admin.html", reservations=reservations)
