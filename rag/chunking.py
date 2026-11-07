"""Dual chunking strategies: fixed-size with overlap and sentence-based."""
from __future__ import annotations
import json
from pathlib import Path
import re
from typing import Any

from rag.config import ROOT


def load_raw_documents() -> list[dict[str, Any]]:
    """Load both synthetic demo policies and verified public product facts."""
    docs = []

    # 1. 12 Synthetic Demo Policies
    kb_dir = ROOT / "knowledge_base"
    for path in sorted(kb_dir.glob("*.md")):
        raw = path.read_text(encoding="utf-8")
        lines = [line.strip() for line in raw.splitlines() if line.strip()]
        title = lines[0].lstrip("#").strip() if lines else path.stem
        # Body text without title and blockquote
        body_lines = [l for l in lines if not l.startswith("#") and not l.startswith(">")]
        content = " ".join(body_lines)

        docs.append({
            "doc_id": path.stem,
            "title": title,
            "source_type": "SYNTHETIC_DEMO_POLICY",
            "url": f"local://knowledge_base/{path.name}",
            "text": content,
        })

    # 2. Public Verified Product Facts
    catalog_path = ROOT / "data" / "product_catalog.json"
    if catalog_path.exists():
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)

        company = catalog.get("company", {})
        docs.append({
            "doc_id": "medantrik_company_overview",
            "title": "Medantrik Company Profile",
            "source_type": "PUBLIC_VERIFIED_FACT",
            "url": company.get("official_site", "https://medantrik.com/"),
            "text": f"Medantrik Medtech Pvt. Ltd. is an {company.get('incubation', 'IIT Kanpur-incubated')} deep-tech health startup focused on {company.get('focus', 'respiratory medtech')}. Registered office at {company.get('office', 'Noida, UP')}.",
        })

        for p in catalog.get("products", []):
            docs.append({
                "doc_id": f"product_{p['id']}",
                "title": f"Medantrik {p['name']} Overview",
                "source_type": "PUBLIC_VERIFIED_FACT",
                "url": p.get("source", "https://medantrik.com/?p=1930"),
                "text": f"Medantrik {p['name']} is a {p['kind']}. {p['safe_description']} Available support intents include {', '.join(p.get('support_intents', []))}.",
            })

    return docs


def split_sentences(text: str) -> list[str]:
    """Clean sentence boundary splitter."""
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    return [s.strip() for s in sentences if len(s.strip()) > 10]


def chunk_fixed_overlap(
    docs: list[dict[str, Any]],
    chunk_size: int = 240,
    chunk_overlap: int = 50,
) -> list[dict[str, Any]]:
    """Overlapping character window with word-boundary awareness."""
    chunks = []
    for doc in docs:
        text = doc["text"]
        start = 0
        idx = 0
        while start < len(text):
            end = start + chunk_size
            if end >= len(text):
                chunk_text = text[start:].strip()
            else:
                # Find nearest space to avoid cutting words
                split_at = text.rfind(" ", start, end)
                if split_at > start:
                    end = split_at
                chunk_text = text[start:end].strip()

            if chunk_text:
                chunks.append({
                    "chunk_id": f"{doc['doc_id']}_fix_{idx:02d}",
                    "parent_doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "source_type": doc["source_type"],
                    "url": doc["url"],
                    "strategy": "fixed_overlap",
                    "text": chunk_text,
                })
                idx += 1

            if end >= len(text):
                break
            start = max(start + 1, end - chunk_overlap)

    return chunks


def chunk_sentence_based(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sentence-boundary chunking: every chunk is one self-contained sentence."""
    chunks = []
    for doc in docs:
        sentences = split_sentences(doc["text"])
        for idx, s in enumerate(sentences):
            chunks.append({
                "chunk_id": f"{doc['doc_id']}_sen_{idx:02d}",
                "parent_doc_id": doc["doc_id"],
                "title": doc["title"],
                "source_type": doc["source_type"],
                "url": doc["url"],
                "strategy": "sentence_based",
                "text": s,
            })
    return chunks
