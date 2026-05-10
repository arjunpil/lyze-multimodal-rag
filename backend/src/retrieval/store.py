"""
store.py
────────
Thin wrapper around Qdrant for storing and searching multimodal embeddings.

Each point in Qdrant stores:
  - vector: the embedding of the text/caption content
  - payload: {content, modality, source, ...metadata}

This keeps retrieval dead simple: one collection, one search call,
results come back with full provenance attached.
"""

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
    Filter,
    FieldCondition,
    MatchValue,
)

DEFAULT_COLLECTION = "multimodal_rag"
DEFAULT_VECTOR_SIZE = 768   # nomic-embed-text; change to 1536 for OpenAI


class VectorStore:
    def __init__(
        self,
        url: str = "http://localhost:6333",
        collection: str = DEFAULT_COLLECTION,
        vector_size: int = DEFAULT_VECTOR_SIZE,
    ):
        self.client = QdrantClient(":memory:")
        self.collection = collection
        self.vector_size = vector_size
        self._ensure_collection()

    def _ensure_collection(self):
        """Create the collection if it doesn't already exist."""
        existing = [c.name for c in self.client.get_collections().collections]
        if self.collection not in existing:
            print(f"[store] Creating collection: {self.collection}")
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(
                    size=self.vector_size,
                    distance=Distance.COSINE,
                ),
            )

    def upsert(self, vectors: list[list[float]], payloads: list[dict[str, Any]]):
        """Store a batch of vectors with their associated payloads."""
        assert len(vectors) == len(payloads), "vectors and payloads must be same length"

        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vec,
                payload=payload,
            )
            for vec, payload in zip(vectors, payloads)
        ]

        self.client.upsert(collection_name=self.collection, points=points)
        print(f"[store] Upserted {len(points)} points")

    def search(
        self,
        query_vector: list[float],
        top_k: int = 5,
        modality_filter: str | None = None,
        source_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Search for the most semantically similar chunks.

        Args:
            query_vector: Embedded query vector
            top_k: Number of results to return
            modality_filter: Limit results to a specific modality
                             ("text" | "image" | "audio" | "video_frame" | "video_audio")
            source_filter: Limit results to a specific source file path

        Returns:
            List of payloads with an added 'score' field (0–1, higher = more similar)
        """
        query_filter = None
        conditions = []

        if modality_filter:
            conditions.append(
                FieldCondition(key="modality", match=MatchValue(value=modality_filter))
            )
        if source_filter:
            conditions.append(
                FieldCondition(key="source", match=MatchValue(value=source_filter))
            )
        if conditions:
            query_filter = Filter(must=conditions)

        results = self.client.search(
            collection_name=self.collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )

        return [
            {**hit.payload, "score": round(hit.score, 4)}
            for hit in results
        ]

    def delete_source(self, source_path: str):
        """Remove all points originating from a specific file."""
        self.client.delete(
            collection_name=self.collection,
            points_selector=Filter(
                must=[FieldCondition(key="source", match=MatchValue(value=source_path))]
            ),
        )
        print(f"[store] Deleted all points from: {source_path}")

    def count(self) -> int:
        """Return total number of stored chunks."""
        return self.client.count(collection_name=self.collection).count