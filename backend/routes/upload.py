import threading
import uuid
from pathlib import Path

from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename

from config import Config
from extensions import db
from models import Video
from services import pipeline_service

upload_bp = Blueprint("upload", __name__)


def _allowed_file(filename: str) -> bool:
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    return ext in Config.ALLOWED_VIDEO_EXTENSIONS


@upload_bp.route("/api/upload", methods=["POST"])
def upload_video():
    if "file" not in request.files:
        return jsonify({"error": "No file part in the request. Send it as multipart form field 'file'."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not _allowed_file(file.filename):
        allowed = ", ".join(sorted(Config.ALLOWED_VIDEO_EXTENSIONS))
        return jsonify({"error": f"Unsupported file type. Allowed: {allowed}"}), 400

    original_filename = secure_filename(file.filename)
    if not original_filename:
        return jsonify({"error": "Invalid filename."}), 400

    # Title: user-provided, or derived from the filename
    title = request.form.get("title", "").strip()
    if not title:
        title = Path(original_filename).stem

    # Unique stored filename so two uploads with the same name never collide
    ext = original_filename.rsplit(".", 1)[-1].lower()
    stored_filename = f"{uuid.uuid4().hex}.{ext}"

    Config.VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
    dest_path = Config.VIDEOS_DIR / stored_filename
    file.save(dest_path)

    video = Video(
        title=title,
        original_filename=original_filename,
        stored_filename=stored_filename,
    )
    db.session.add(video)
    db.session.commit()

    # Kick off the (potentially slow) pipeline in the background so this
    # request returns immediately; the frontend polls
    # GET /api/videos/<id>/status for progress.
    app = current_app._get_current_object()
    thread = threading.Thread(target=pipeline_service.process_video, args=(app, video.id), daemon=True)
    thread.start()

    return jsonify(video.to_dict()), 202
