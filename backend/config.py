"""
Central configuration for the AI Teaching Assistant backend.

Every value can be overridden via environment variables
(see .env.example).
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# =========================================================
# ENVIRONMENT
# =========================================================

# backend/.env
load_dotenv(
    Path(__file__).parent / ".env"
)


# Project root = one level above backend/
PROJECT_ROOT = (
    Path(__file__).resolve().parent.parent
)

BACKEND_DIR = (
    Path(__file__).resolve().parent
)


class Config:

    # =====================================================
    # FLASK
    # =====================================================

    SECRET_KEY = os.getenv(
        "SECRET_KEY",
        "dev-secret-change-me"
    )

    MAX_CONTENT_LENGTH = (
        int(
            os.getenv(
                "MAX_UPLOAD_MB",
                "1024"
            )
        )
        * 1024
        * 1024
    )


    # =====================================================
    # SQLITE / SQLALCHEMY
    # =====================================================

    DB_PATH = (
        BACKEND_DIR
        / "data"
        / "app.db"
    )

    SQLALCHEMY_DATABASE_URI = (
        f"sqlite:///{DB_PATH}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False


    # =====================================================
    # DATA DIRECTORIES
    # =====================================================

    VIDEOS_DIR = Path(
        os.getenv(
            "VIDEOS_DIR",
            PROJECT_ROOT / "videos"
        )
    )

    AUDIOS_DIR = Path(
        os.getenv(
            "AUDIOS_DIR",
            PROJECT_ROOT / "audios"
        )
    )

    JSONS_DIR = Path(
        os.getenv(
            "JSONS_DIR",
            PROJECT_ROOT / "jsons"
        )
    )

    NEWJSONS_DIR = Path(
        os.getenv(
            "NEWJSONS_DIR",
            PROJECT_ROOT / "newjsons"
        )
    )

    EMBEDDINGS_PATH = Path(
        os.getenv(
            "EMBEDDINGS_PATH",
            PROJECT_ROOT / "embeddings.joblib"
        )
    )


    # =====================================================
    # VIDEO FRAME ANALYSIS
    # =====================================================

    # Frames extracted from uploaded videos for
    # visual/slide analysis.
    #
    # Example:
    # project_root/
    #     frames/
    #         video_1/
    #             frame_000001.jpg
    #             frame_000002.jpg
    #
    FRAMES_DIR = Path(
        os.getenv(
            "FRAMES_DIR",
            PROJECT_ROOT / "frames"
        )
    )


    # How often a key frame is extracted.
    #
    # 15 seconds is intentionally used instead of
    # analyzing every video frame because the application
    # is designed to run on CPU as well.
    FRAME_INTERVAL_SECONDS = int(
        os.getenv(
            "FRAME_INTERVAL_SECONDS",
            "15"
        )
    )


    # =====================================================
    # OLLAMA
    # =====================================================

    OLLAMA_URL = os.getenv(
        "OLLAMA_URL",
        "http://localhost:11434"
    )

    # Embedding model
    OLLAMA_EMBED_MODEL = os.getenv(
        "OLLAMA_EMBED_MODEL",
        "nomic-embed-text"
    )

    # Answer generation model
    OLLAMA_GENERATE_MODEL = os.getenv(
        "OLLAMA_GENERATE_MODEL",
        "qwen3:4b"
    )

    # Vision model used for analyzing selected
    # video frames / slides.
    #
    # Recommended for this project:
    #     qwen2.5vl:3b
    #
    # This model is kept separate from the answer
    # generation model.
    OLLAMA_VISION_MODEL = os.getenv(
        "OLLAMA_VISION_MODEL",
        "qwen2.5vl:3b"
    )


    # =====================================================
    # WHISPER
    # =====================================================

    # Base is faster than large models.
    WHISPER_MODEL = os.getenv(
        "WHISPER_MODEL",
        "base"
    )

    WHISPER_LANGUAGE = os.getenv(
        "WHISPER_LANGUAGE",
        "hi"
    )

    WHISPER_TASK = os.getenv(
        "WHISPER_TASK",
        "translate"
    )


    # =====================================================
    # CHUNKING
    # =====================================================

    CHUNK_GROUP_SIZE = int(
        os.getenv(
            "CHUNK_GROUP_SIZE",
            "5"
        )
    )


    # =====================================================
    # RETRIEVAL
    # =====================================================

    # Number of relevant transcript chunks sent to Qwen.
    TOP_K = int(
        os.getenv(
            "TOP_K",
            "3"
        )
    )

    # Minimum combined relevance score.
    #
    # Previous:
    #     0.35
    #
    # New:
    #     0.55
    #
    # This prevents weak/unrelated chunks from being
    # returned as references.
    SIMILARITY_THRESHOLD = float(
        os.getenv(
            "SIMILARITY_THRESHOLD",
            "0.55"
        )
    )


    # =====================================================
    # UPLOADS
    # =====================================================

    ALLOWED_VIDEO_EXTENSIONS = {
        "mp4",
        "mov",
        "mkv",
        "avi",
        "webm",
        "m4v",
    }


    # =====================================================
    # CORS
    # =====================================================

    FRONTEND_ORIGIN = os.getenv(
        "FRONTEND_ORIGIN",
        "http://localhost:5173"
    )