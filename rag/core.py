"""RAG Core: SentenceTransformers embeddings, Chroma persistence, retrieval, and grounding."""
from __future__ import annotations
import os
from typing import Any
import chromadb
from chromadb.api.types import EmbeddingFunction, Documents, Embeddings
from sentence_transformers import SentenceTransformer

from rag.config import (
    CHROMA_PERSIST_DIR,
    COLLECTION_FIXED,
    COLLECTION_SENTENCE,
    DEFAULT_TOP_K,
    EMBEDDING_MODEL_NAME,
    ensure_runtime_dirs,
)


class SentenceTransformerEmbeddingFunction(EmbeddingFunction):
    """Local SentenceTransformers embedding wrapper for ChromaDB."""

    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        self.model = SentenceTransformer(model_name, local_files_only=True)

    def __call__(self, input: Documents) -> Embeddings:
        embeddings = self.model.encode(input, convert_to_numpy=True, normalize_embeddings=True)
        return embeddings.tolist()


_SHARED_EMBEDDER: SentenceTransformerEmbeddingFunction | None = None


def get_embedder() -> SentenceTransformerEmbeddingFunction:
    global _SHARED_EMBEDDER
    if _SHARED_EMBEDDER is None:
        _SHARED_EMBEDDER = SentenceTransformerEmbeddingFunction()
    return _SHARED_EMBEDDER


class RAGCore:
    def __init__(self, persist_dir=CHROMA_PERSIST_DIR):
        ensure_runtime_dirs()
        self.client = chromadb.PersistentClient(path=str(persist_dir))
        self.embedder = get_embedder()

        self.collection_fixed = self.client.get_or_create_collection(
            name=COLLECTION_FIXED,
            embedding_function=self.embedder,
            metadata={"hnsw:space": "cosine"},
        )
        self.collection_sentence = self.client.get_or_create_collection(
            name=COLLECTION_SENTENCE,
            embedding_function=self.embedder,
            metadata={"hnsw:space": "cosine"},
        )
        self.collections = {
            "fixed_overlap": self.collection_fixed,
            "sentence_based": self.collection_sentence,
        }

    def index_chunks(self, fixed_chunks: list[dict], sentence_chunks: list[dict]) -> dict[str, int]:
        """Index chunks into both Chroma collections."""
        # 1. Fixed overlap
        if fixed_chunks:
            self.collection_fixed.upsert(
                ids=[c["chunk_id"] for c in fixed_chunks],
                documents=[c["text"] for c in fixed_chunks],
                metadatas=[
                    {
                        "parent_doc_id": c["parent_doc_id"],
                        "title": c["title"],
                        "source_type": c["source_type"],
                        "url": c["url"],
                        "strategy": c["strategy"],
                    }
                    for c in fixed_chunks
                ],
            )

        # 2. Sentence based
        if sentence_chunks:
            self.collection_sentence.upsert(
                ids=[c["chunk_id"] for c in sentence_chunks],
                documents=[c["text"] for c in sentence_chunks],
                metadatas=[
                    {
                        "parent_doc_id": c["parent_doc_id"],
                        "title": c["title"],
                        "source_type": c["source_type"],
                        "url": c["url"],
                        "strategy": c["strategy"],
                    }
                    for c in sentence_chunks
                ],
            )

        return {
            "fixed_overlap_count": self.collection_fixed.count(),
            "sentence_based_count": self.collection_sentence.count(),
        }

    def retrieve(
        self,
        query: str,
        strategy: str = "fixed_overlap",
        top_k: int = DEFAULT_TOP_K,
    ) -> list[dict[str, Any]]:
        collection = self.collections.get(strategy, self.collection_fixed)
        results = collection.query(
            query_texts=[query],
            n_results=min(top_k, max(1, collection.count())),
            include=["documents", "metadatas", "distances"],
        )

        hits = []
        if results and results["ids"] and results["ids"][0]:
            ids = results["ids"][0]
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results["distances"][0]

            for chunk_id, text, meta, dist in zip(ids, docs, metas, distances):
                # For cosine distance: cosine_similarity = 1.0 - distance
                similarity = round(max(0.0, 1.0 - float(dist)), 4)
                hits.append({
                    "chunk_id": chunk_id,
                    "parent_doc_id": meta["parent_doc_id"],
                    "title": meta["title"],
                    "source_type": meta["source_type"],
                    "url": meta["url"],
                    "strategy": meta["strategy"],
                    "text": text,
                    "similarity": similarity,
                })

        hits.sort(key=lambda x: x["similarity"], reverse=True)
        return hits


def grounded_answer(hits: list[dict[str, Any]], threshold: float) -> dict[str, Any]:
    """Generate grounded answer strictly using retrieved chunks and empirical threshold."""
    if not hits or hits[0]["similarity"] < threshold:
        return {
            "outcome": "not_found",
            "answer": "I don't know based on the available verified information. The requested topic is not covered in the local knowledge base or product catalog.",
            "citations": [],
            "max_similarity": hits[0]["similarity"] if hits else 0.0,
            "threshold": threshold,
            "grounded": False,
        }

    # High-confidence hits above threshold
    relevant_hits = [h for h in hits if h["similarity"] >= threshold]
    excerpts = [h["text"] for h in relevant_hits]
    combined_answer = " ".join(excerpts[:2])

    seen_sources = set()
    citations = []
    for h in relevant_hits:
        src_key = (h["parent_doc_id"], h["title"])
        if src_key not in seen_sources:
            seen_sources.add(src_key)
            citations.append({
                "id": h["parent_doc_id"],
                "title": h["title"],
                "source_type": h["source_type"],
                "url": h["url"],
                "similarity": h["similarity"],
            })

    return {
        "outcome": "answered",
        "answer": combined_answer,
        "citations": citations,
        "max_similarity": hits[0]["similarity"],
        "threshold": threshold,
        "grounded": True,
    }
