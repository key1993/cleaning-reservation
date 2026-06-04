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
    return gridfs.GridFS(backup.db)  # type: ignore[arg-type]


def _files_col():
    """Direct access to fs.files — works in all PyMongo versions."""
    return backup.db["fs.files"]  # type: ignore[index]


# ── Auth helpers ───────────────────────────────────────────────────────────────

def _token_required(f):
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
    try:
        if "backup" not in request.files:
            return jsonify({"error": 'No file field named "backup"'}), 400

        file = request.files["backup"]
        if not file.filename.lower().endswith(".ebsherbackup"):
            return jsonify({"error": "Expected a .ebsherbackup file"}), 400

        pi_id = request.form.get("pi_id", "").strip()
        pi_name = request.form.get("pi_name", "Unknown Pi").strip()
        safe_name = os.path.basename(file.filename)
        data = file.read()

        fs = _fs()

        # Delete previous backup for this Pi using direct collection query
        # (avoids gridfs.GridFS.find() filter issues across PyMongo versions)
        if pi_id:
            for old in list(_files_col().find({"pi_id": pi_id}, {"_id": 1})):
                try:
                    fs.delete(old["_id"])
                except Exception:
                    pass

        file_id = fs.put(
            data,
            filename=safe_name,
            content_type="application/octet-stream",
            uploaded_at=datetime.utcnow().isoformat(),
            size_bytes=len(data),
            pi_id=pi_id or None,
            pi_name=pi_name,
        )

        return jsonify({
            "success": True,
            "file_id": str(file_id),
            "filename": safe_name,
            "size_bytes": len(data),
            "stored_at": datetime.utcnow().isoformat(),
        })
    except Exception as exc:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(exc)}), 500


# ── Admin UI routes ────────────────────────────────────────────────────────────

@backup.route("/backup/list", methods=["GET"])
@_admin_required
def list_backups():
    """Return one backup entry per registered Pi, newest first."""
    entries = []
    for doc in _files_col().find({}).sort("uploadDate", -1):
        entries.append({
            "file_id": str(doc["_id"]),
            "filename": doc.get("filename", ""),
            "size_bytes": doc.get("length", 0),
            "uploaded_at": doc.get("uploadDate", datetime.utcnow()).isoformat(),
            "pi_id": doc.get("pi_id"),
            "pi_name": doc.get("pi_name", "Unknown Pi"),
        })
    return jsonify({"backups": entries, "count": len(entries)})


@backup.route("/backup/pis", methods=["GET"])
@_admin_required
def list_pis():
    """Return all registered Pi devices (for client-Pi assignment dropdowns)."""
    seen = {}
    for doc in _files_col().find(
        {"pi_id": {"$exists": True, "$ne": None}},
        {"pi_id": 1, "pi_name": 1, "uploadDate": 1},
    ).sort("uploadDate", -1):
        pi_id = doc.get("pi_id")
        if pi_id and pi_id not in seen:
            seen[pi_id] = {
                "pi_id": pi_id,
                "pi_name": doc.get("pi_name", "Unknown Pi"),
                "last_backup": doc.get("uploadDate", datetime.utcnow()).isoformat(),
            }
    return jsonify({"pis": list(seen.values())})


@backup.route("/backup/download/<pi_id>", methods=["GET"])
@_admin_required
def download_backup(pi_id: str):
    """Stream a Pi's backup file to the browser."""
    doc = _files_col().find_one(
        {"pi_id": pi_id},
        sort=[("uploadDate", -1)],
    )
    if not doc:
        return jsonify({"error": "No backup found for this Pi"}), 404
    f = _fs().get(doc["_id"])
    filename = doc.get("filename", "backup.ebsherbackup")
    return Response(
        f.read(),
        mimetype="application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@backup.route("/backup/delete/<pi_id>", methods=["DELETE", "POST"])
@_admin_required
def delete_backup(pi_id: str):
    """Delete the stored backup for a specific Pi."""
    fs = _fs()
    docs = list(_files_col().find({"pi_id": pi_id}, {"_id": 1}))
    if not docs:
        return jsonify({"error": "No backup found for this Pi"}), 404
    for doc in docs:
        try:
            fs.delete(doc["_id"])
        except Exception:
            pass
    return jsonify({"success": True, "deleted_pi": pi_id})
