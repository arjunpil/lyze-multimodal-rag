"""
audio_loader.py
───────────────
Transcribes audio files using OpenAI Whisper (runs locally).
Yields text chunks with timestamp metadata.
Supported formats: MP3, WAV, M4A, FLAC, OGG, WEBM
"""

from pathlib import Path
from typing import Generator
import whisper

from .pdf_loader import Document, _chunk_text

SUPPORTED_EXTENSIONS = {".mp3", ".wav", ".m4a", ".flac", ".ogg", ".webm"}

# Module-level model cache so we only load once per session
_whisper_model = None


def _get_model(model_name: str = "base") -> whisper.Whisper:
    global _whisper_model
    if _whisper_model is None:
        print(f"[audio_loader] Loading Whisper model: {model_name}")
        _whisper_model = whisper.load_model(model_name)
    return _whisper_model


def load_audio(
    path: str | Path,
    model_name: str = "base",
    language: str | None = None,
) -> Generator[Document, None, None]:
    """
    Transcribe an audio file and yield Document chunks.

    Each chunk includes segment-level timestamps in metadata so
    the retrieval system can tell you *where* in the audio the
    relevant content appears.
    """
    path = Path(path)

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported audio format: {path.suffix}")

    model = _get_model(model_name)

    print(f"[audio_loader] Transcribing: {path.name}")
    result = model.transcribe(
        str(path),
        language=language,
        verbose=False,
    )

    segments = result.get("segments", [])
    full_text = result.get("text", "").strip()

    if not segments:
        # Fallback: yield full transcript as a single chunk
        for chunk in _chunk_text(full_text):
            yield Document(
                content=chunk,
                modality="audio",
                source=str(path),
                metadata={"filename": path.name},
            )
        return

    # Group segments into chunks, preserving start/end timestamps
    current_text = []
    current_start = segments[0]["start"]
    word_count = 0

    for seg in segments:
        seg_words = seg["text"].split()
        current_text.extend(seg_words)
        word_count += len(seg_words)
        current_end = seg["end"]

        if word_count >= 400:
            yield Document(
                content=" ".join(current_text),
                modality="audio",
                source=str(path),
                metadata={
                    "filename": path.name,
                    "start_seconds": round(current_start, 2),
                    "end_seconds": round(current_end, 2),
                    "timestamp_label": _format_timestamp(current_start),
                },
            )
            current_text = []
            current_start = current_end
            word_count = 0

    # Yield any remaining text
    if current_text:
        yield Document(
            content=" ".join(current_text),
            modality="audio",
            source=str(path),
            metadata={
                "filename": path.name,
                "start_seconds": round(current_start, 2),
                "end_seconds": round(segments[-1]["end"], 2),
                "timestamp_label": _format_timestamp(current_start),
            },
        )


def _format_timestamp(seconds: float) -> str:
    """Convert seconds to MM:SS label."""
    m = int(seconds // 60)
    s = int(seconds % 60)
    return f"{m:02d}:{s:02d}"