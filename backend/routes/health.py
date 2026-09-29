from flask import Blueprint, jsonify

from config import Config
from services import ollama_service

health_bp = Blueprint("health", __name__)


@health_bp.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "ollama_reachable": ollama_service.health_check(),
        "ollama_url": Config.OLLAMA_URL,
        "embed_model": Config.OLLAMA_EMBED_MODEL,
        "generate_model": Config.OLLAMA_GENERATE_MODEL,
    })
