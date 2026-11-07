"""Executable script to chunk knowledge base and product catalog, then index into Chroma."""
import json
from pathlib import Path
import sys

# Ensure root is on path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.chunking import chunk_fixed_overlap, chunk_sentence_based, load_raw_documents
from rag.core import RAGCore


def rebuild():
    print("Loading documents...")
    docs = load_raw_documents()
    print(f"Loaded {len(docs)} documents.")

    fixed_chunks = chunk_fixed_overlap(docs)
    sentence_chunks = chunk_sentence_based(docs)
    print(f"Generated {len(fixed_chunks)} fixed chunks and {len(sentence_chunks)} sentence chunks.")

    print("Indexing into ChromaDB collections...")
    rag = RAGCore()
    stats = rag.index_chunks(fixed_chunks, sentence_chunks)
    print("Chroma index counts:", stats)

    evidence_dir = ROOT / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "raw_documents_count": len(docs),
        "fixed_chunks_count": len(fixed_chunks),
        "sentence_chunks_count": len(sentence_chunks),
        "chroma_fixed_collection_count": stats["fixed_overlap_count"],
        "chroma_sentence_collection_count": stats["sentence_based_count"],
        "model": "all-MiniLM-L6-v2",
        "sample_fixed_chunk": fixed_chunks[0],
        "sample_sentence_chunk": sentence_chunks[0],
    }
    with open(evidence_dir / "index_stats.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print("Index stats saved to evidence/index_stats.json")
    return report


if __name__ == "__main__":
    rebuild()
