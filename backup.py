"""
Ebsher Pi Backup — Flask Blueprint
───────────────────────────────────
Receives encrypted .ebsherbackup files from Raspberry Pi instances and
stores them permanently in MongoDB GridFS (survives Render.com deploys/restarts).

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
    """Receive a .ebsherbackup file from a Raspberry Pi."""
    if "backup" not in request.files:
        return jsonify({"error": 'No file field named "backup"'}), 400

    file = request.files["backup"]
    if not file.filename.lower().endswith(".ebsherbackup"):
        return jsonify({"error": "Expected a .ebsherbackup file"}), 400

    safe_name = os.path.basename(file.filename)
    data = file.read()

    fs = _fs()
    file_id = fs.put(
        data,
        filename=safe_name,
        content_type="application/octet-stream",
        uploaded_at=datetime.utcnow().isoformat(),
        size_bytes=len(data),
    )

    _prune_old_backups(keep=10)

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
    """Return metadata for all stored backups, newest first."""
    fs = _fs()
    files = sorted(
        fs.find(),
        key=lambda f: f.upload_date,
        reverse=True,
    )
    entries = []
    for f in files:
        entries.append({
            "file_id": str(f._id),
            "filename": f.filename,
            "size_bytes": f.length,
            "uploaded_at": f.upload_date.isoformat(),
        })
    return jsonify({"backups": entries, "count": len(entries)})


@backup.route("/backup/download/<file_id>", methods=["GET"])
@_admin_required
def download_backup(file_id: str):
    """Stream a specific backup file to the browser."""
    fs = _fs()
    try:
        f = fs.get(ObjectId(file_id))
    except Exception:
        return jsonify({"error": "Backup not found"}), 404

    return Response(
        f.read(),
        mimetype="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{f.filename}"'},
    )


@backup.route("/backup/latest/download", methods=["GET"])
@_admin_required
def download_latest_backup():
    """Stream the most recent backup file to the browser."""
    fs = _fs()
    files = sorted(fs.find(), key=lambda f: f.upload_date, reverse=True)
    if not files:
        return jsonify({"error": "No backups found"}), 404
    f = files[0]
    return Response(
        f.read(),
        mimetype="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{f.filename}"'},
    )


@backup.route("/backup/delete/<file_id>", methods=["DELETE", "POST"])
@_admin_required
def delete_backup(file_id: str):
    """Delete a specific backup from GridFS."""
    fs = _fs()
    try:
        fs.delete(ObjectId(file_id))
    except Exception:
        return jsonify({"error": "Backup not found or already deleted"}), 404
    return jsonify({"success": True, "deleted": file_id})


# ── Internal helpers ───────────────────────────────────────────────────────────

def _prune_old_backups(keep: int = 10) -> None:
    """Delete oldest backups beyond the `keep` limit."""
    fs = _fs()
    files = sorted(fs.find(), key=lambda f: f.upload_date, reverse=True)
    for old in files[keep:]:
        try:
            fs.delete(old._id)
        except Exception:
            pass
