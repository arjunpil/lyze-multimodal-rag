"""
embedder.py
───────────
Converts text content into embedding vectors.
All modalities are embedded as text (images via their captions).

Supports: Ollama (nomic-embed-text), OpenAI (text-embedding-3-small),
          SentenceTransformers (fully offline fallback).
"""

import os
from typing import Literal

Provider = Literal["ollama", "openai", "sentence_transformers"]

# Cache for sentence_transformers model
_st_model = None


def embed(texts: list[str], provider: Provider = "ollama", model: str = "nomic-embed-text") -> list[list[float]]:
    """
    Embed a list of strings and return a list of float vectors.
    Batch-processes for efficiency.
    """
    if not texts:
        return []

    if provider == "ollama":
        return _embed_ollama(texts, model)
    elif provider == "openai":
        return _embed_openai(texts, model)
    elif provider == "sentence_transformers":
        return _embed_sentence_transformers(texts, model)
    else:
        raise ValueError(f"Unknown embed provider: {provider}")


def embed_one(text: str, provider: Provider = "ollama", model: str = "nomic-embed-text") -> list[float]:
    """Convenience wrapper for embedding a single string."""
    return embed([text], provider=provider, model=model)[0]


def _embed_ollama(texts: list[str], model: str) -> list[list[float]]:
    import ollama
    vectors = []
    for text in texts:
        resp = ollama.embeddings(model=model, prompt=text)
        vectors.append(resp["embedding"])
    return vectors


def _embed_openai(texts: list[str], model: str = "text-embedding-3-small") -> list[list[float]]:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    response = client.embeddings.create(input=texts, model=model)
    return [item.embedding for item in response.data]


def _embed_sentence_transformers(texts: list[str], model: str = "all-MiniLM-L6-v2") -> list[list[float]]:
    global _st_model
    from sentence_transformers import SentenceTransformer
    if _st_model is None:
        print(f"[embedder] Loading SentenceTransformer: {model}")
        _st_model = SentenceTransformer(model)
    vectors = _st_model.encode(texts, convert_to_numpy=True)
    return vectors.tolist()