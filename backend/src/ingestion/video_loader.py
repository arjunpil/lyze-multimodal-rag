"""
video_loader.py
───────────────
Processes video files by:
  1. Sampling frames at a configurable interval for visual captioning
  2. Extracting + transcribing the audio track via Whisper

Each yielded Document is either a video frame (image modality)
or a transcript chunk (audio modality), both tagged with their
timestamp so queries can cite specific moments.
"""

import io
import subprocess
import tempfile
from pathlib import Path
from typing import Generator

import cv2
from PIL import Image

from .pdf_loader import Document
from .audio_loader import load_audio

SUPPORTED_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv", ".webm", ".m4v"}


def load_video(
    path: str | Path,
    frame_interval_seconds: int = 30,
    whisper_model: str = "base",
) -> Generator[Document, None, None]:
    """
    Yield Documents from a video file:
    - One image Document per sampled frame (for visual captioning)
    - Text Documents from the transcribed audio track

    Args:
        path: Path to video file
        frame_interval_seconds: How often to sample a frame (default: every 30s)
        whisper_model: Whisper model size for audio transcription
    """
    path = Path(path)

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported video format: {path.suffix}")

    # ── 1. Sample frames ──────────────────────────────────────────────────
    yield from _extract_frames(path, frame_interval_seconds)

    # ── 2. Extract audio and transcribe ───────────────────────────────────
    yield from _extract_and_transcribe_audio(path, whisper_model)


def _extract_frames(
    path: Path, interval_seconds: int
) -> Generator[Document, None, None]:
    """Sample frames from video at a fixed time interval."""
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    frame_step = int(fps * interval_seconds)

    frame_index = 0
    sampled = 0

    print(f"[video_loader] Sampling frames every {interval_seconds}s from {path.name}")

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_index % frame_step == 0:
            timestamp_s = frame_index / fps

            # Convert BGR (OpenCV) → RGB → JPEG bytes
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_img = Image.fromarray(rgb_frame)
            buf = io.BytesIO()
            pil_img.save(buf, format="JPEG", quality=80)
            image_bytes = buf.getvalue()

            yield Document(
                content="",           # filled in by captioner
                modality="video_frame",
                source=str(path),
                metadata={
                    "filename": path.name,
                    "frame_index": frame_index,
                    "timestamp_seconds": round(timestamp_s, 2),
                    "timestamp_label": _format_timestamp(timestamp_s),
                    "image_bytes": image_bytes,
                },
            )
            sampled += 1

        frame_index += 1

    cap.release()
    print(f"[video_loader] Sampled {sampled} frames")


def _extract_and_transcribe_audio(
    path: Path, whisper_model: str
) -> Generator[Document, None, None]:
    """Extract audio from video and run Whisper on it."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_path = Path(tmp.name)

    try:
        print(f"[video_loader] Extracting audio from {path.name}")
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", str(path),
                "-ar", "16000",        # Whisper expects 16kHz
                "-ac", "1",            # mono
                "-vn",                 # no video
                str(audio_path),
            ],
            check=True,
            capture_output=True,
        )

        for doc in load_audio(audio_path, model_name=whisper_model):
            # Override source to point to the original video, not the temp audio
            doc.source = str(path)
            doc.metadata["filename"] = path.name
            doc.modality = "video_audio"
            yield doc

    except subprocess.CalledProcessError as e:
        print(f"[video_loader] ffmpeg failed: {e.stderr.decode()}")
    finally:
        audio_path.unlink(missing_ok=True)


def _format_timestamp(seconds: float) -> str:
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"