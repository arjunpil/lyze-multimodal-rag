"""
pdf_loader.py
─────────────
Extracts text chunks and embedded images from PDF files.
Each chunk carries metadata: source file, page number, modality.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import Generator
from dataclasses import dataclass, field


@dataclass
class Document:
    """A single chunk of content extracted from any modality."""
    content: str                  # text or image caption
    modality: str                 # "text" | "image" | "audio" | "video_frame"
    source: str                   # original file path
    metadata: dict = field(default_factory=dict)


def load_pdf(path: str | Path) -> Generator[Document, None, None]:
    """
    Yield Document chunks from a PDF file.

    Extracts:
    - Text per page, split into overlapping chunks
    - Embedded images (returned as raw bytes for captioning downstream)
    """
    path = Path(path)
    doc = fitz.open(str(path))

    for page_num, page in enumerate(doc, start=1):
        # ── Text extraction ──────────────────────────────────────────────
        text = page.get_text("text").strip()
        if text:
            for chunk in _chunk_text(text):
                yield Document(
                    content=chunk,
                    modality="text",
                    source=str(path),
                    metadata={"page": page_num, "filename": path.name},
                )

        # ── Embedded image extraction ────────────────────────────────────
        for img_index, img in enumerate(page.get_images(full=True)):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            ext = base_image["ext"]

            yield Document(
                content="",          # filled in by captioner
                modality="image",
                source=str(path),
                metadata={
                    "page": page_num,
                    "filename": path.name,
                    "image_index": img_index,
                    "image_ext": ext,
                    "image_bytes": image_bytes,   # raw bytes, not stored in vector DB
                },
            )

    doc.close()


def _chunk_text(text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
    """Split text into overlapping chunks by word count."""
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        chunks.append(chunk)
        start += chunk_size - overlap
    return chunks