"""
Lyze Backend — main.py
FastAPI server that handles file ingestion and RAG queries.
Runs locally on http://localhost:8000
"""

import os
import sys
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# ── Add src to path ──────────────────────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent))

from src.ingestion.pdf_loader import load_pdf
from src.ingestion.image_loader import load_image, SUPPORTED_EXTENSIONS as IMAGE_EXTS
from src.ingestion.audio_loader import load_audio, SUPPORTED_EXTENSIONS as AUDIO_EXTS
from src.ingestion.video_loader import load_video, SUPPORTED_EXTENSIONS as VIDEO_EXTS
from src.embeddings.captioner import caption_document
from src.embeddings.embedder import embed
from src.retrieval.store import VectorStore
from src.retrieval.pipeline import RAGPipeline

app = FastAPI(title="Lyze API", version="1.0.0")

# Allow requests from the React dev server and any local origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Initialize store and pipeline ────────────────────────────────────────────
store = VectorStore(
    url=os.getenv("QDRANT_URL", "http://localhost:6333"),
    collection=os.getenv("QDRANT_COLLECTION", "multimodal_rag"),
)

pipeline = RAGPipeline(
    store=store,
    embed_provider=os.getenv("EMBED_PROVIDER", "ollama"),
    embed_model=os.getenv("EMBED_MODEL", "nomic-embed-text"),
    llm_provider=os.getenv("LLM_PROVIDER", "ollama"),
    llm_model=os.getenv("LLM_MODEL", "mistral"),
)


def get_file_type(suffix: str) -> str | None:
    s = suffix.lower()
    if s == ".pdf":      return "pdf"
    if s in IMAGE_EXTS:  return "image"
    if s in AUDIO_EXTS:  return "audio"
    if s in VIDEO_EXTS:  return "video"
    return None


# ── Models ────────────────────────────────────────────────────────────────────
class QueryRequest(BaseModel):
    question: str
    top_k: int = 5
    modality_filter: str | None = None


class QueryResponse(BaseModel):
    answer: str
    sources: list[dict]


class StatsResponse(BaseModel):
    total_chunks: int
    status: str


# ── Routes ────────────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "ok", "message": "Lyze backend running"}


@app.get("/stats", response_model=StatsResponse)
def stats():
    return {"total_chunks": store.count(), "status": "ready"}


@app.post("/ingest")
async def ingest(file: UploadFile = File(...)):
    """Ingest a single file into the vector store."""
    suffix = Path(file.filename).suffix
    file_type = get_file_type(suffix)

    if not file_type:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {suffix}")

    contents = await file.read()

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(contents)
        tmp_path = Path(tmp.name)

    try:
        # Load documents
        if file_type == "pdf":
            docs = list(load_pdf(tmp_path))
        elif file_type == "image":
            docs = list(load_image(tmp_path))
        elif file_type == "audio":
            docs = list(load_audio(tmp_path, model_name=os.getenv("WHISPER_MODEL", "base")))
        elif file_type == "video":
            docs = list(load_video(tmp_path, whisper_model=os.getenv("WHISPER_MODEL", "base")))

        # Override source to use original filename
        for d in docs:
            d.source = file.filename

        # Caption images
        vision_provider = os.getenv("VISION_PROVIDER", "ollama")
        vision_model    = os.getenv("VISION_MODEL", "llava")
        for doc in docs:
            if doc.metadata.get("image_bytes"):
                try:
                    caption_document(doc, provider=vision_provider, model=vision_model)
                except Exception:
                    doc.content = "[Image: caption unavailable]"

        # Embed and store
        all_docs = [d for d in docs if d.content]
        if not all_docs:
            return {"filename": file.filename, "chunks": 0, "message": "No content extracted"}

        vectors = embed(
            [d.content for d in all_docs],
            provider=os.getenv("EMBED_PROVIDER", "ollama"),
            model=os.getenv("EMBED_MODEL", "nomic-embed-text"),
        )
        payloads = [
            {
                "content":  d.content,
                "modality": d.modality,
                "source":   d.source,
                **{k: v for k, v in d.metadata.items() if k != "image_bytes"},
            }
            for d in all_docs
        ]
        store.upsert(vectors, payloads)

        return {
            "filename": file.filename,
            "chunks":   len(all_docs),
            "total":    store.count(),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        tmp_path.unlink(missing_ok=True)


@app.post("/query", response_model=QueryResponse)
def query(req: QueryRequest):
    """Query the RAG pipeline."""
    if not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    try:
        pipeline.top_k = req.top_k
        response = pipeline.query(
            req.question,
            modality_filter=req.modality_filter,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    sources = []
    for chunk in response.chunks:
        sources.append({
            "citation": chunk.citation(),
            "modality": chunk.modality,
            "source":   chunk.source,
            "score":    chunk.score,
            "preview":  chunk.content[:300],
            "metadata": {k: v for k, v in chunk.metadata.items()
                         if k not in ("image_bytes",)},
        })

    return QueryResponse(answer=response.answer, sources=sources)


@app.delete("/clear")
def clear_store():
    """Clear all documents from the vector store."""
    try:
        from qdrant_client.models import Filter
        store.client.delete_collection(store.collection)
        store._ensure_collection()
        return {"status": "cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    print("\n  Lyze backend starting on http://localhost:8000\n")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)
