"""
image_loader.py
───────────────
Loads standalone image files and prepares them for captioning.
Supported formats: JPEG, PNG, WEBP, BMP, TIFF
"""

from pathlib import Path
from typing import Generator
from PIL import Image
import io

from .pdf_loader import Document

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def load_image(path: str | Path) -> Generator[Document, None, None]:
    """
    Yield a single Document for an image file.
    The content field is left empty — the captioner fills it in.
    Raw image bytes are stored in metadata for the captioner to use.
    """
    path = Path(path)

    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"Unsupported image format: {path.suffix}")

    img = Image.open(path)

    # Normalize to RGB (handles RGBA, palette, etc.)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Store as JPEG bytes for the captioner
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    image_bytes = buf.getvalue()

    yield Document(
        content="",           # filled in by captioner
        modality="image",
        source=str(path),
        metadata={
            "filename": path.name,
            "width": img.width,
            "height": img.height,
            "image_bytes": image_bytes,
        },
    )