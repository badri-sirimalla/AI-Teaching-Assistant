from flask import Blueprint, request, jsonify
import numpy as np

from models import Video, STATUS_READY
from services import rag_service, ollama_service


chat_bp = Blueprint("chat", __name__)


def make_json_safe(obj):
    """
    Convert NumPy/Pandas values into normal JSON-compatible
    Python values.
    """

    if isinstance(obj, dict):
        return {
            key: make_json_safe(value)
            for key, value in obj.items()
        }

    if isinstance(obj, list):
        return [
            make_json_safe(value)
            for value in obj
        ]

    if isinstance(obj, tuple):
        return [
            make_json_safe(value)
            for value in obj
        ]

    if isinstance(obj, np.integer):
        return int(obj)

    if isinstance(obj, np.floating):
        return float(obj)

    if isinstance(obj, np.ndarray):
        return obj.tolist()

    return obj


@chat_bp.route("/api/ask", methods=["POST"])
def ask():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )

    question = (
        data.get("question")
        or ""
    ).strip()

    video_id = data.get(
        "video_id"
    )

    # -----------------------------------------------------
    # Validate question
    # -----------------------------------------------------

    if not question:

        return jsonify({
            "error": "'question' is required."
        }), 400

    # -----------------------------------------------------
    # Validate selected video
    # -----------------------------------------------------

    if video_id is not None:

        try:
            video_id = int(video_id)

        except (
            TypeError,
            ValueError,
        ):

            return jsonify({
                "error": "Invalid video_id."
            }), 400

        video = Video.query.get(
            video_id
        )

        if not video:

            return jsonify({
                "error": (
                    f"Video {video_id} "
                    "not found."
                )
            }), 404

        if video.status != STATUS_READY:

            return jsonify({
                "error": (
                    f"Video '{video.title}' "
                    "is not ready yet "
                    f"(status: {video.status})."
                )
            }), 409

    # -----------------------------------------------------
    # Ask RAG
    # -----------------------------------------------------

    try:

        result = (
            rag_service.answer_question(
                question,
                video_id=video_id,
            )
        )

    except ollama_service.OllamaError as e:

        return jsonify({
            "error": str(e)
        }), 503

    except Exception as e:

        print(
            f"/api/ask error: {e}"
        )

        raise

    return jsonify(
        make_json_safe(result)
    )
