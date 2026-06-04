"""
Ebsher Pi Backup — Flask Blueprint
───────────────────────────────────
Receives encrypted .ebsherbackup files from Raspberry Pi instances and
stores them permanently in MongoDB GridFS (survives Render.com deploys/restarts).

One backup is kept per Pi (identified by pi_id). Each new upload replaces
the previous backup for that Pi automatically.

Auth:
  - Upload endpoint  → X-Backup-Token header (shared secret set in BACKUP_TOKEN env var)
  - Admin endpoints  → session["admin_logged_in"] (same as the rest of admin panel)

Required env vars:
  BACKUP_TOKEN    Shared secret that the Pi must send in X-Backup-Token header
"""

import os
from datetime import datetime
from functools import wraps

import gridfs
from bson import ObjectId
from flask import (
    Blueprint,
    Response,
    jsonify,
    redirect,
    request,
    session,
    url_for,
)

backup = Blueprint("backup", __name__)

# Injected by app.py (same pattern as routes/admin blueprints)
backup.db = None  # type: ignore[attr-defined]


def _fs():
    """Return a GridFS bucket bound to the current db."""
    return gridfs.GridFS(backup.db)  # type: ignore[arg-type]


# ── Auth helpers ───────────────────────────────────────────────────────────────

def _token_required(f):
    """Pi-facing: validate X-Backup-Token header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        expected = os.environ.get("BACKUP_TOKEN", "")
        if not expected:
            return jsonify({"error": "BACKUP_TOKEN not configured on server"}), 500
        token = request.headers.get("X-Backup-Token", "")
        if token != expected:
            return jsonify({"error": "Invalid backup token"}), 401
        return f(*args, **kwargs)
    return decorated


def _admin_required(f):
    """Admin UI: require admin session (mirrors admin.py decorator)."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin.login"))
        return f(*args, **kwargs)
    return decorated


# ── Pi → Server ────────────────────────────────────────────────────────────────

@backup.route("/backup/upload", methods=["POST"])
@_token_required
def upload_backup():
    """Receive a .ebsherbackup file from a Raspberry Pi.

    Form fields:
      backup  — the .ebsherbackup file
      pi_id   — unique Pi identifier (UUID, auto-generated on the Pi)
      pi_name — human-readable label (e.g. "Office Pi")

    Each upload replaces the previous backup for that pi_id (one backup per Pi).
    """
    if "backup" not in request.files:
        return jsonify({"error": 'No file field named "backup"'}), 400

    file = request.files["backup"]
    if not file.filename.lower().endswith(".ebsherbackup"):
        return jsonify({"error": "Expected a .ebsherbackup file"}), 400

    pi_id = request.form.get("pi_id", "").strip()
    pi_name = request.form.get("pi_name", "Unknown Pi").strip()

    if not pi_id:
        return jsonify({"error": "pi_id is required"}), 400

    safe_name = os.path.basename(file.filename)
    data = file.read()

    fs = _fs()

    # Delete the previous backup for this Pi — one backup per Pi
    for old in list(fs.find({"pi_id": pi_id})):
        try:
            fs.delete(old._id)
        except Exception:
            pass

    file_id = fs.put(
        data,
        filename=safe_name,
        content_type="application/octet-stream",
        uploaded_at=datetime.utcnow().isoformat(),
        size_bytes=len(data),
        pi_id=pi_id,
        pi_name=pi_name,
    )

    return jsonify({
        "success": True,
        "file_id": str(file_id),
        "filename": safe_name,
        "size_bytes": len(data),
        "stored_at": datetime.utcnow().isoformat(),
    })


# ── Admin UI routes ────────────────────────────────────────────────────────────

@backup.route("/backup/list", methods=["GET"])
@_admin_required
def list_backups():
    """Return one backup entry per registered Pi, newest first."""
    fs = _fs()
    files = sorted(fs.find(), key=lambda f: f.upload_date, reverse=True)
    entries = []
    for f in files:
        entries.append({
            "file_id": str(f._id),
            "filename": f.filename,
            "size_bytes": f.length,
            "uploaded_at": f.upload_date.isoformat(),
            "pi_id": getattr(f, "pi_id", None),
            "pi_name": getattr(f, "pi_name", "Unknown Pi"),
        })
    return jsonify({"backups": entries, "count": len(entries)})


@backup.route("/backup/pis", methods=["GET"])
@_admin_required
def list_pis():
    """Return all registered Pi devices (used to populate client-Pi assignment dropdowns)."""
    fs = _fs()
    seen: dict = {}
    for f in fs.find():
        pi_id = getattr(f, "pi_id", None)
        if pi_id and pi_id not in seen:
            seen[pi_id] = {
                "pi_id": pi_id,
                "pi_name": getattr(f, "pi_name", "Unknown Pi"),
                "last_backup": f.upload_date.isoformat(),
            }
    return jsonify({"pis": list(seen.values())})


@backup.route("/backup/download/<pi_id>", methods=["GET"])
@_admin_required
def download_backup(pi_id: str):
    """Stream a Pi's backup file to the browser (identified by pi_id)."""
    fs = _fs()
    files = list(fs.find({"pi_id": pi_id}))
    if not files:
        return jsonify({"error": "No backup found for this Pi"}), 404
    f = max(files, key=lambda x: x.upload_date)
    return Response(
        f.read(),
        mimetype="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{f.filename}"'},
    )


@backup.route("/backup/delete/<pi_id>", methods=["DELETE", "POST"])
@_admin_required
def delete_backup(pi_id: str):
    """Delete the stored backup for a specific Pi."""
    fs = _fs()
    files = list(fs.find({"pi_id": pi_id}))
    if not files:
        return jsonify({"error": "No backup found for this Pi"}), 404
    for f in files:
        try:
            fs.delete(f._id)
        except Exception:
            pass
    return jsonify({"success": True, "deleted_pi": pi_id})
