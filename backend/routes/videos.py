from flask import Blueprint, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from models import Video, Topic
from config import Config
from extensions import db
from services import rag_service


videos_bp = Blueprint("videos", __name__)


# =========================================================
# LIST ALL VIDEOS
# =========================================================

@videos_bp.route("/api/videos", methods=["GET"])
def list_videos():
    videos = Video.query.order_by(
        Video.created_at.desc()
    ).all()

    return jsonify([
        video.to_dict()
        for video in videos
    ])


# =========================================================
# VIDEO STATUS
# =========================================================

@videos_bp.route(
    "/api/videos/<int:video_id>/status",
    methods=["GET"]
)
def video_status(video_id):
    video = Video.query.get(video_id)

    if not video:
        return jsonify({
            "error": "Video not found."
        }), 404

    return jsonify(
        video.to_dict()
    )


# =========================================================
# GET VIDEO TOPICS
# =========================================================

@videos_bp.route(
    "/api/videos/<int:video_id>/topics",
    methods=["GET"]
)
def get_video_topics(video_id):
    """
    Return the AI-detected topics for one lecture.

    Topics are returned in chronological order.
    """

    video = Video.query.get(video_id)

    if not video:
        return jsonify({
            "error": "Video not found."
        }), 404

    topics = (
        Topic.query
        .filter_by(
            video_id=video_id
        )
        .order_by(
            Topic.topic_order.asc()
        )
        .all()
    )

    return jsonify({
        "video_id": video_id,
        "topics": [
            topic.to_dict()
            for topic in topics
        ]
    })


# =========================================================
# SERVE VIDEO FILE
# =========================================================

@videos_bp.route(
    "/api/videos/<int:video_id>/file",
    methods=["GET"]
)
def serve_video(video_id):
    """
    Serve the actual uploaded lecture video.

    The frontend uses this endpoint to display the video
    associated with a retrieved RAG source.
    """

    video = Video.query.get(video_id)

    if not video:
        return jsonify({
            "error": "Video not found."
        }), 404

    if not video.stored_filename:
        return jsonify({
            "error": "Video file information is missing."
        }), 404

    video_path = (
        Config.VIDEOS_DIR
        / video.stored_filename
    )

    if not video_path.exists():
        return jsonify({
            "error": "Video file not found on the server."
        }), 404

    return send_from_directory(
        Config.VIDEOS_DIR,
        video.stored_filename,
        conditional=True
    )


# =========================================================
# DELETE VIDEO
# =========================================================

@videos_bp.route(
    "/api/videos/<int:video_id>",
    methods=["DELETE"]
)
def delete_video(video_id):
    video = Video.query.get(video_id)

    if not video:
        return jsonify({
            "error": "Video not found."
        }), 404

    try:
        # -----------------------------------------------------
        # Delete this video's topic map
        # -----------------------------------------------------

        Topic.query.filter_by(
            video_id=video_id
        ).delete(
            synchronize_session=False
        )

        # -----------------------------------------------------
        # Save information before deleting database record
        # -----------------------------------------------------

        stored_filename = video.stored_filename
        title = video.title

        safe_title = (
            secure_filename(title)
            or f"video-{video_id}"
        )

        # Current pipeline creates WAV audio files.
        audio_path = (
            Config.AUDIOS_DIR
            / f"{video_id}_{safe_title}.wav"
        )

        video_path = (
            Config.VIDEOS_DIR
            / stored_filename
        )

        # -----------------------------------------------------
        # Remove this video's embeddings
        # from the RAG index
        # -----------------------------------------------------

        removed_chunks = (
            rag_service.remove_video_from_index(
                str(video_id)
            )
        )

        # -----------------------------------------------------
        # Delete uploaded video file
        # -----------------------------------------------------

        if video_path.exists():
            video_path.unlink()

        # -----------------------------------------------------
        # Delete generated audio file
        # -----------------------------------------------------

        if audio_path.exists():
            audio_path.unlink()

        # -----------------------------------------------------
        # Delete database record
        # -----------------------------------------------------

        db.session.delete(video)

        db.session.commit()

        return jsonify({
            "message": "Video deleted successfully.",
            "video_id": video_id,
            "removed_chunks": removed_chunks
        }), 200

    except Exception as e:
        db.session.rollback()

        return jsonify({
            "error": f"Could not delete video: {str(e)}"
        }), 500