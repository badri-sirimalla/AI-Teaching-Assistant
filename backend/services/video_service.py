"""
Video processing service.

Responsibilities:
- Extract audio from uploaded videos.
- Convert audio to mono 16 kHz WAV.
- Transcribe audio using faster-whisper.
- Preserve real transcript timestamps.
- Merge transcript segments into RAG chunks.

Important:
- This service does NOT generate timestamps using an LLM.
- Video timestamps come directly from the actual transcript/video timeline.
- No visual/frame analysis is performed here.
"""

import math
import subprocess
from pathlib import Path

from config import Config


# =========================================================
# WHISPER MODEL CACHE
# =========================================================

_whisper_model = None
_whisper_device = None
_whisper_compute_type = None


def _get_whisper_model():
    """
    Load faster-whisper only once.

    CPU:
        int8

    CUDA:
        float16
    """

    global _whisper_model
    global _whisper_device
    global _whisper_compute_type

    if _whisper_model is not None:
        return _whisper_model

    from faster_whisper import WhisperModel

    # -----------------------------------------------------
    # Detect CUDA support
    # -----------------------------------------------------

    try:
        import ctranslate2

        supported_types = (
            ctranslate2.get_supported_compute_types("cuda")
        )

        cuda_available = "CUDA" in supported_types

    except Exception:
        cuda_available = False

    if cuda_available:
        _whisper_device = "cuda"
        _whisper_compute_type = "float16"
    else:
        _whisper_device = "cpu"
        _whisper_compute_type = "int8"

    print("=" * 60)
    print("Loading faster-whisper model")
    print(f"Model         : {Config.WHISPER_MODEL}")
    print(f"Device        : {_whisper_device}")
    print(f"Compute type  : {_whisper_compute_type}")
    print("=" * 60)

    try:

        _whisper_model = WhisperModel(
            Config.WHISPER_MODEL,
            device=_whisper_device,
            compute_type=_whisper_compute_type,
            cpu_threads=4,
            num_workers=1,
        )

    except Exception as e:

        # -------------------------------------------------
        # CUDA fallback
        # -------------------------------------------------

        if _whisper_device == "cuda":

            print("=" * 60)
            print("CUDA initialization failed.")
            print("Falling back to CPU int8.")
            print(f"Error: {e}")
            print("=" * 60)

            _whisper_device = "cpu"
            _whisper_compute_type = "int8"

            _whisper_model = WhisperModel(
                Config.WHISPER_MODEL,
                device="cpu",
                compute_type="int8",
                cpu_threads=4,
                num_workers=1,
            )

        else:

            raise RuntimeError(
                "Could not load faster-whisper "
                f"model: {e}"
            )

    print("=" * 60)
    print("faster-whisper model loaded successfully.")
    print("=" * 60)

    return _whisper_model


# =========================================================
# AUDIO EXTRACTION
# =========================================================


def convert_to_audio(
    video_path: Path,
    audio_path: Path,
):
    """
    Extract audio from a video.

    Output:
        Mono
        16 kHz
        PCM 16-bit WAV
    """

    video_path = Path(video_path)
    audio_path = Path(audio_path)

    audio_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if not video_path.exists():
        raise RuntimeError(
            "Video file does not exist: "
            f"{video_path}"
        )

    print("=" * 60)
    print("Starting audio extraction")
    print(f"Input : {video_path}")
    print(f"Output: {audio_path}")
    print("=" * 60)

    command = [
        "ffmpeg",
        "-y",
        "-hide_banner",
        "-loglevel",
        "error",

        "-i",
        str(video_path),

        "-vn",
        "-map",
        "0:a:0",

        "-ac",
        "1",
        "-ar",
        "16000",

        "-c:a",
        "pcm_s16le",

        str(audio_path),
    ]

    try:

        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    except FileNotFoundError:

        raise RuntimeError(
            "FFmpeg was not found. "
            "Make sure FFmpeg is installed "
            "and available in PATH."
        )

    except Exception as e:

        raise RuntimeError(
            f"Could not start FFmpeg: {e}"
        )

    if result.returncode != 0:

        error_text = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Unknown FFmpeg error."
        )

        raise RuntimeError(
            "ffmpeg failed to extract audio:\n"
            f"{error_text}"
        )

    if not audio_path.exists():

        raise RuntimeError(
            "FFmpeg completed but the "
            "audio file was not created."
        )

    file_size = audio_path.stat().st_size

    if file_size == 0:

        raise RuntimeError(
            "FFmpeg created an empty audio file."
        )

    print("=" * 60)
    print("Audio extraction completed successfully.")
    print(f"Audio file size: {file_size:,} bytes")
    print("=" * 60)


# =========================================================
# TRANSCRIPTION
# =========================================================


def transcribe_audio(
    audio_path: Path,
    number: str,
    title: str,
    video_id: int = None,
):
    """
    Transcribe audio using faster-whisper.

    Existing project configuration is preserved:

        WHISPER_LANGUAGE=hi
        WHISPER_TASK=translate

    This means Hindi speech is translated to English
    while the original segment timing is preserved.
    """

    audio_path = Path(audio_path)

    if not audio_path.exists():

        raise RuntimeError(
            "Audio file does not exist: "
            f"{audio_path}"
        )

    model = _get_whisper_model()

    print("=" * 60)
    print("Starting faster-whisper transcription")
    print(f"Audio        : {audio_path}")
    print(f"Model        : {Config.WHISPER_MODEL}")
    print(f"Device       : {_whisper_device}")
    print(f"Compute type : {_whisper_compute_type}")
    print(f"Language     : {Config.WHISPER_LANGUAGE}")
    print(f"Task         : {Config.WHISPER_TASK}")
    print(f"Video ID     : {video_id}")
    print("=" * 60)

    try:

        segments, info = model.transcribe(

            str(audio_path),

            language=(
                Config.WHISPER_LANGUAGE
            ),

            task=(
                Config.WHISPER_TASK
            ),

            beam_size=1,

            best_of=1,

            temperature=0,

            condition_on_previous_text=False,

            word_timestamps=False,

            vad_filter=True,

            vad_parameters={
                "min_silence_duration_ms": 500,
            },
        )

    except Exception as e:

        raise RuntimeError(
            "faster-whisper "
            f"transcription failed: {e}"
        )

    chunks = []

    segment_count = 0

    for segment in segments:

        text = segment.text.strip()

        if not text:
            continue

        start = float(segment.start)
        end = float(segment.end)

        chunks.append({

            "video_id": (
                int(video_id)
                if video_id is not None
                else None
            ),

            "number": str(number),

            "title": title,

            "start": start,

            "end": end,

            "text": text,
        })

        segment_count += 1

    print("=" * 60)
    print("Transcription completed.")
    print(f"Segments : {segment_count}")

    if hasattr(info, "duration"):

        print(
            f"Duration : "
            f"{info.duration:.2f} seconds"
        )

    print("=" * 60)

    return chunks


# =========================================================
# MERGE TRANSCRIPT SEGMENTS
# =========================================================


def merge_chunks(
    chunks,
    group_size: int = None,
):
    """
    Merge Whisper segments into larger RAG chunks.

    Uses:

        Config.CHUNK_GROUP_SIZE

    unless group_size is explicitly supplied.

    Important:
    The start timestamp comes from the first real
    Whisper segment and the end timestamp comes from
    the last real Whisper segment.
    """

    if group_size is None:

        group_size = (
            Config.CHUNK_GROUP_SIZE
        )

    if not chunks:

        return []

    if group_size <= 0:

        raise ValueError(
            "CHUNK_GROUP_SIZE must be "
            "greater than 0."
        )

    merged = []

    total_chunks = len(chunks)

    number_of_groups = math.ceil(
        total_chunks / group_size
    )

    for group_index in range(
        number_of_groups
    ):

        start_index = (
            group_index * group_size
        )

        end_index = min(
            (
                group_index + 1
            ) * group_size,
            total_chunks,
        )

        group = chunks[
            start_index:end_index
        ]

        if not group:
            continue

        first = group[0]
        last = group[-1]

        merged.append({

            "video_id": first.get(
                "video_id"
            ),

            "number": first[
                "number"
            ],

            "title": first[
                "title"
            ],

            "start": float(
                first["start"]
            ),

            "end": float(
                last["end"]
            ),

            "text": " ".join(
                chunk["text"]
                for chunk in group
            ),
        })

    return merged