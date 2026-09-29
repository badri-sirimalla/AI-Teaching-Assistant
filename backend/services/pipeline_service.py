"""
Video processing pipeline.

Flow:

    Video
      ↓
    Audio extraction
      ↓
    Whisper transcription
      ↓
    Transcript chunks
      ↓
    Embeddings
      ↓
    RAG index
      ↓
    READY

Important:
- Transcript timestamps come from faster-whisper.
- No visual/frame processing is performed.
- No topic detection is performed.
- RAG and embedding behavior is preserved.
"""

import time

from werkzeug.utils import secure_filename

from config import Config
from extensions import db

from models import (
    Video,
    STATUS_EXTRACTING_AUDIO,
    STATUS_TRANSCRIBING,
    STATUS_CHUNKING,
    STATUS_EMBEDDING,
    STATUS_READY,
    STATUS_FAILED,
)

from services import (
    video_service,
    rag_service,
)


# ============================================================
# STATUS HELPERS
# ============================================================


def _set_status(
    app,
    video_id,
    status,
    error_message=None,
    chunk_count=None,
):
    """
    Safely update video status inside
    a Flask application context.
    """

    with app.app_context():

        video = Video.query.get(video_id)

        if not video:
            return

        video.status = status

        if error_message is not None:
            video.error_message = error_message

        if chunk_count is not None:
            video.chunk_count = chunk_count

        db.session.commit()


def _video_exists(app, video_id):
    """
    Check whether the video still exists.

    Database access is performed inside
    a Flask application context.
    """

    with app.app_context():

        video = Video.query.get(video_id)

        return video is not None


# ============================================================
# MAIN PROCESSING PIPELINE
# ============================================================


def process_video(app, video_id: int):
    """
    Process one uploaded video.

    Processing flow:

        Video
          ↓
        Audio
          ↓
        Whisper
          ↓
        Transcript chunks
          ↓
        Embeddings
          ↓
        RAG index
          ↓
        READY
    """

    # ========================================================
    # GET VIDEO INFORMATION
    # ========================================================

    with app.app_context():

        video = Video.query.get(video_id)

        if not video:

            print(
                f"Video {video_id} no longer exists."
            )

            return

        video_path = (
            Config.VIDEOS_DIR
            / video.stored_filename
        )

        number = str(video.id)
        title = video.title

    safe_title = (
        secure_filename(title)
        or f"video-{number}"
    )

    # video_service.py creates PCM WAV.
    audio_path = (
        Config.AUDIOS_DIR
        / f"{number}_{safe_title}.wav"
    )

    added = 0

    # ========================================================
    # TOTAL PIPELINE TIMER
    # ========================================================

    total_start = time.perf_counter()

    try:

        # ====================================================
        # INITIAL VIDEO CHECK
        # ====================================================

        if not _video_exists(
            app,
            video_id,
        ):

            print(
                f"Video {video_id} no longer exists."
            )

            return

        if not video_path.exists():

            raise RuntimeError(
                "Uploaded video file does not exist: "
                f"{video_path}"
            )

        # ====================================================
        # STEP 1: AUDIO EXTRACTION
        # ====================================================

        _set_status(
            app,
            video_id,
            STATUS_EXTRACTING_AUDIO,
        )

        print()
        print("=" * 70)
        print("STEP 1: AUDIO EXTRACTION")
        print("=" * 70)
        print(f"Video ID : {video_id}")
        print(f"Input    : {video_path}")
        print(f"Output   : {audio_path}")
        print("=" * 70)

        step_start = time.perf_counter()

        video_service.convert_to_audio(
            video_path,
            audio_path,
        )

        step_time = (
            time.perf_counter()
            - step_start
        )

        print(
            f"[TIME] Audio extraction: "
            f"{step_time:.2f} seconds"
        )

        print(
            "Audio extraction completed successfully."
        )

        # ====================================================
        # CHECK VIDEO STILL EXISTS
        # ====================================================

        if not _video_exists(
            app,
            video_id,
        ):

            print(
                f"Video {video_id} was deleted "
                "after audio extraction."
            )

            if audio_path.exists():
                audio_path.unlink()

            return

        # ====================================================
        # STEP 2: WHISPER TRANSCRIPTION
        # ====================================================

        _set_status(
            app,
            video_id,
            STATUS_TRANSCRIBING,
        )

        print()
        print("=" * 70)
        print("STEP 2: WHISPER TRANSCRIPTION")
        print("=" * 70)
        print(f"Video ID : {video_id}")
        print(f"Audio    : {audio_path}")
        print("=" * 70)

        step_start = time.perf_counter()

        raw_chunks = (
            video_service.transcribe_audio(
                audio_path=audio_path,
                number=number,
                title=title,
                video_id=video_id,
            )
        )

        step_time = (
            time.perf_counter()
            - step_start
        )

        print(
            f"[TIME] Whisper transcription: "
            f"{step_time:.2f} seconds"
        )

        if not raw_chunks:

            raise RuntimeError(
                "Transcription produced no speech "
                "segments for this video."
            )

        print(
            f"Transcription produced "
            f"{len(raw_chunks)} raw segments."
        )

        # ====================================================
        # STEP 3: CHUNKING
        # ====================================================

        if not _video_exists(
            app,
            video_id,
        ):

            print(
                f"Video {video_id} was deleted "
                "during transcription."
            )

            return

        _set_status(
            app,
            video_id,
            STATUS_CHUNKING,
        )

        print()
        print("=" * 70)
        print("STEP 3: CHUNKING")
        print("=" * 70)
        print(
            f"Raw segments : {len(raw_chunks)}"
        )
        print("=" * 70)

        step_start = time.perf_counter()

        merged_chunks = (
            video_service.merge_chunks(
                raw_chunks
            )
        )

        step_time = (
            time.perf_counter()
            - step_start
        )

        print(
            f"[TIME] Chunking: "
            f"{step_time:.3f} seconds"
        )

        if not merged_chunks:

            raise RuntimeError(
                "Chunking produced no chunks."
            )

        print(
            f"Created {len(merged_chunks)} "
            "merged transcript chunks."
        )

        # ====================================================
        # STEP 4: EMBEDDINGS / RAG INDEX
        # ====================================================

        if not _video_exists(
            app,
            video_id,
        ):

            print(
                f"Video {video_id} was deleted "
                "before embedding."
            )

            return

        _set_status(
            app,
            video_id,
            STATUS_EMBEDDING,
        )

        print()
        print("=" * 70)
        print("STEP 4: CREATING EMBEDDINGS / RAG INDEX")
        print("=" * 70)
        print(f"Video ID : {video_id}")
        print(
            f"Chunks   : {len(merged_chunks)}"
        )
        print("=" * 70)

        step_start = time.perf_counter()

        added = (
            rag_service.add_chunks_to_index(
                merged_chunks
            )
        )

        step_time = (
            time.perf_counter()
            - step_start
        )

        print(
            f"[TIME] Embedding/index building: "
            f"{step_time:.2f} seconds"
        )

        print(
            f"Added {added} chunk(s) "
            "to the RAG index."
        )

        # ====================================================
        # FINAL EXISTENCE CHECK
        # ====================================================

        if not _video_exists(
            app,
            video_id,
        ):

            print(
                f"Video {video_id} was deleted "
                "before processing completed."
            )

            return

        # ====================================================
        # TOTAL PROCESSING TIME
        # ====================================================

        total_time = (
            time.perf_counter()
            - total_start
        )

        # ====================================================
        # STEP 5: READY
        # ====================================================

        _set_status(
            app,
            video_id,
            STATUS_READY,
            chunk_count=added,
        )

        print()
        print("=" * 70)
        print("VIDEO PROCESSING COMPLETED")
        print("=" * 70)
        print(f"Video ID : {video_id}")
        print(f"Title    : {title}")
        print(f"Chunks   : {added}")
        print(f"Audio    : {audio_path}")
        print(
            f"TOTAL PROCESSING TIME: "
            f"{total_time:.2f} seconds"
        )
        print(
            f"TOTAL PROCESSING TIME: "
            f"{total_time / 60:.2f} minutes"
        )
        print("=" * 70)

    except Exception as e:

        total_time = (
            time.perf_counter()
            - total_start
        )

        print()
        print("=" * 70)
        print("VIDEO PROCESSING FAILED")
        print("=" * 70)
        print(f"Video ID : {video_id}")
        print(f"Error    : {e}")
        print(
            f"Elapsed  : "
            f"{total_time:.2f} seconds"
        )
        print("=" * 70)

        # ----------------------------------------------------
        # Do not try to update a deleted video.
        # ----------------------------------------------------

        if not _video_exists(
            app,
            video_id,
        ):

            return

        _set_status(
            app,
            video_id,
            STATUS_FAILED,
            error_message=str(e),
        )

    finally:

        # ----------------------------------------------------
        # Clean up SQLAlchemy session for this
        # background processing thread.
        # ----------------------------------------------------

        with app.app_context():

            db.session.remove()