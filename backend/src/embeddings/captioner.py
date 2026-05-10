"""
captioner.py
────────────
Generates text captions for image Documents using a vision LLM.
Supports: Ollama (LLaVA), OpenAI (GPT-4o), Anthropic (Claude).

The caption replaces doc.content so the image becomes searchable
via standard text embeddings — no multimodal embedding model needed.
"""

import base64
import os
from typing import Literal

from src.ingestion.pdf_loader import Document  # reuse the Document dataclass

Provider = Literal["ollama", "openai", "anthropic"]

CAPTION_PROMPT = (
    "Describe this image in detail. Focus on: what is shown, any text visible, "
    "charts or diagrams and what data they convey, key visual elements, and "
    "the likely context or purpose of the image. Be thorough but concise."
)


def caption_document(doc: Document, provider: Provider = "ollama", model: str = "llava") -> Document:
    """
    Given an image Document (with image_bytes in metadata),
    generate a caption and store it in doc.content.
    Returns the updated Document.
    """
    image_bytes = doc.metadata.get("image_bytes")
    if not image_bytes:
        raise ValueError("Document has no image_bytes in metadata")

    b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    if provider == "ollama":
        caption = _caption_ollama(b64, model)
    elif provider == "openai":
        caption = _caption_openai(b64, model)
    elif provider == "anthropic":
        caption = _caption_anthropic(b64, model)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    doc.content = caption
    # Remove raw bytes from metadata — not needed after captioning
    doc.metadata.pop("image_bytes", None)
    return doc


def _caption_ollama(b64: str, model: str) -> str:
    import ollama
    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": CAPTION_PROMPT,
                "images": [b64],
            }
        ],
    )
    return response["message"]["content"].strip()


def _caption_openai(b64: str, model: str = "gpt-4o") -> str:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": CAPTION_PROMPT},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
                    },
                ],
            }
        ],
        max_tokens=300,
    )
    return response.choices[0].message.content.strip()


def _caption_anthropic(b64: str, model: str = "claude-3-5-sonnet-20241022") -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    response = client.messages.create(
        model=model,
        max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/jpeg",
                            "data": b64,
                        },
                    },
                    {"type": "text", "text": CAPTION_PROMPT},
                ],
            }
        ],
    )
    return response.content[0].text.strip()


def _caption_gemini(b64: str, model: str = "gemini-1.5-flash") -> str:
    import google.generativeai as genai
    import os, base64
    genai.configure(api_key=os.environ["GEMINI_API_KEY"])
    m = genai.GenerativeModel(model)
    import PIL.Image, io
    img = PIL.Image.open(io.BytesIO(base64.b64decode(b64)))
    response = m.generate_content([CAPTION_PROMPT, img])
    return response.text.strip()