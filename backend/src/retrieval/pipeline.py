"""
pipeline.py
───────────
The core RAG pipeline: embed query → retrieve chunks → generate answer.

This is what everything else feeds into. Give it a question,
get back a grounded answer with source citations.
"""

import os
from dataclasses import dataclass, field
from typing import Any

from ..embeddings.embedder import embed_one
from .store import VectorStore


@dataclass
class RetrievedChunk:
    content: str
    modality: str
    source: str
    score: float
    metadata: dict = field(default_factory=dict)

    def citation(self) -> str:
        """Human-readable source citation."""
        import os
        filename = os.path.basename(self.source)
        parts = [f"[{self.modality.upper()}] {filename}"]

        if "page" in self.metadata:
            parts.append(f"page {self.metadata['page']}")
        if "timestamp_label" in self.metadata:
            parts.append(f"@ {self.metadata['timestamp_label']}")

        return " — ".join(parts)


@dataclass
class RAGResponse:
    answer: str
    chunks: list[RetrievedChunk]
    query: str

    def formatted(self) -> str:
        """Pretty-print the answer with citations."""
        lines = [
            f"📝 Answer\n{'─'*60}",
            self.answer,
            f"\n📚 Sources ({len(self.chunks)} chunks retrieved)\n{'─'*60}",
        ]
        for i, chunk in enumerate(self.chunks, 1):
            lines.append(f"{i}. {chunk.citation()} (score: {chunk.score})")
            lines.append(f"   {chunk.content[:200]}{'...' if len(chunk.content) > 200 else ''}")
        return "\n".join(lines)


class RAGPipeline:
    def __init__(
        self,
        store: VectorStore,
        embed_provider: str = "ollama",
        embed_model: str = "nomic-embed-text",
        llm_provider: str = "ollama",
        llm_model: str = "mistral",
        top_k: int = 5,
    ):
        self.store = store
        self.embed_provider = embed_provider
        self.embed_model = embed_model
        self.llm_provider = llm_provider
        self.llm_model = llm_model
        self.top_k = top_k

    def query(
        self,
        question: str,
        modality_filter: str | None = None,
        source_filter: str | None = None,
    ) -> RAGResponse:
        """
        Full RAG pipeline:
        1. Embed the question
        2. Retrieve top-k relevant chunks
        3. Generate a grounded answer
        """
        # 1. Embed
        query_vec = embed_one(question, provider=self.embed_provider, model=self.embed_model)

        # 2. Retrieve
        raw_results = self.store.search(
            query_vector=query_vec,
            top_k=self.top_k,
            modality_filter=modality_filter,
            source_filter=source_filter,
        )

        chunks = [
            RetrievedChunk(
                content=r.get("content", ""),
                modality=r.get("modality", "unknown"),
                source=r.get("source", ""),
                score=r.get("score", 0.0),
                metadata={k: v for k, v in r.items() if k not in ("content", "modality", "source", "score")},
            )
            for r in raw_results
        ]

        # 3. Generate
        answer = self._generate(question, chunks)

        return RAGResponse(answer=answer, chunks=chunks, query=question)

    def _generate(self, question: str, chunks: list[RetrievedChunk]) -> str:
        """Build a prompt from retrieved chunks and call the LLM."""
        if not chunks:
            return "I couldn't find any relevant information to answer your question."

        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            context_parts.append(
                f"[Source {i} — {chunk.citation()}]\n{chunk.content}"
            )
        context = "\n\n".join(context_parts)

        prompt = f"""You are a helpful assistant answering questions based on provided context.
The context comes from multiple file types: documents, images (described as captions), audio transcripts, and video frames.

Context:
{context}

Question: {question}

Answer based only on the context above. Cite sources by their number (e.g. [Source 1]).
If the context doesn't contain enough information, say so clearly."""

        if self.llm_provider == "ollama":
            return self._generate_ollama(prompt)
        elif self.llm_provider == "openai":
            return self._generate_openai(prompt)
        elif self.llm_provider == "anthropic":
            return self._generate_anthropic(prompt)
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")

    def _generate_ollama(self, prompt: str) -> str:
        import ollama
        resp = ollama.chat(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp["message"]["content"].strip()

    def _generate_openai(self, prompt: str) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        resp = client.chat.completions.create(
            model=self.llm_model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
        )
        return resp.choices[0].message.content.strip()

    def _generate_anthropic(self, prompt: str) -> str:
        import anthropic
        client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        resp = client.messages.create(
            model=self.llm_model,
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.content[0].text.strip()


    def _generate_gemini(self, prompt: str) -> str:
        import google.generativeai as genai
        import os
        genai.configure(api_key=os.environ["GEMINI_API_KEY"])
        m = genai.GenerativeModel(self.llm_model)
        response = m.generate_content(prompt)
        return response.text.strip()