"""
Database models.

Video tracks each uploaded video's processing status.

The actual transcript chunks + embeddings live in embeddings.joblib
(a pandas DataFrame), exactly like the original project.

Topics are stored separately in SQLite so the application can build
a topic map for each uploaded lecture without changing the existing
RAG/embedding structure.
"""

from datetime import datetime

from extensions import db


# Processing goes through these stages in order.
# "failed" can happen from any stage.
STATUS_UPLOADED = "uploaded"
STATUS_EXTRACTING_AUDIO = "extracting_audio"
STATUS_TRANSCRIBING = "transcribing"
STATUS_CHUNKING = "chunking"
STATUS_EMBEDDING = "embedding"
STATUS_READY = "ready"
STATUS_FAILED = "failed"


class Video(db.Model):
    __tablename__ = "videos"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    title = db.Column(
        db.String(255),
        nullable=False,
    )

    original_filename = db.Column(
        db.String(255),
        nullable=False,
    )

    stored_filename = db.Column(
        db.String(255),
        nullable=False,
    )

    status = db.Column(
        db.String(32),
        nullable=False,
        default=STATUS_UPLOADED,
    )

    error_message = db.Column(
        db.Text,
        nullable=True,
    )

    chunk_count = db.Column(
        db.Integer,
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
    )

    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "original_filename": self.original_filename,
            "status": self.status,
            "error_message": self.error_message,
            "chunk_count": self.chunk_count,
            "created_at": (
                self.created_at.isoformat()
                if self.created_at
                else None
            ),
            "updated_at": (
                self.updated_at.isoformat()
                if self.updated_at
                else None
            ),
        }


class Topic(db.Model):
    """
    A topic/section detected inside an uploaded lecture.

    The LLM will identify the topic title, but the actual timestamps
    will be mapped from transcript chunks. This means timestamps are
    never invented by the LLM.
    """

    __tablename__ = "topics"

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    video_id = db.Column(
        db.Integer,
        db.ForeignKey("videos.id"),
        nullable=False,
        index=True,
    )

    title = db.Column(
        db.String(255),
        nullable=False,
    )

    start_time = db.Column(
        db.Float,
        nullable=False,
    )

    end_time = db.Column(
        db.Float,
        nullable=False,
    )

    topic_order = db.Column(
        db.Integer,
        nullable=False,
    )

    # 0 = main topic
    # 1 = subtopic
    level = db.Column(
        db.Integer,
        nullable=False,
        default=0,
    )

    def to_dict(self):
        return {
            "id": self.id,
            "video_id": self.video_id,
            "title": self.title,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "topic_order": self.topic_order,
            "level": self.level,
        }