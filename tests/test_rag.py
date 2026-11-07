"""Unit and integration tests for RAG core, chunking, calibration, and grounding (Tasks 3, 4, 5)."""
from pathlib import Path
import pytest
from rag.chunking import chunk_fixed_overlap, chunk_sentence_based, load_raw_documents
from rag.core import RAGCore, grounded_answer


@pytest.fixture(scope="module")
def rag_instance():
    return RAGCore()


def test_document_loading_and_counts():
    docs = load_raw_documents()
    assert len(docs) >= 16  # 12 policies + company profile + 3 products
    types = {d["source_type"] for d in docs}
    assert "SYNTHETIC_DEMO_POLICY" in types
    assert "PUBLIC_VERIFIED_FACT" in types


def test_dual_chunking_strategies():
    docs = load_raw_documents()
    fixed = chunk_fixed_overlap(docs)
    sentence = chunk_sentence_based(docs)

    assert len(fixed) > 0
    assert len(sentence) > 0
    assert len(sentence) > len(fixed), "Sentence chunking should produce more fine-grained units"
    assert all("chunk_id" in c and "parent_doc_id" in c for c in fixed)
    assert all("chunk_id" in c and "parent_doc_id" in c for c in sentence)


def test_chroma_collections_populated(rag_instance: RAGCore):
    assert rag_instance.collection_fixed.count() >= 30
    assert rag_instance.collection_sentence.count() >= 50


def test_in_domain_retrieval_and_similarity(rag_instance: RAGCore):
    query = "What is the severity SLA response time for critical issues?"
    hits = rag_instance.retrieve(query, strategy="fixed_overlap", top_k=3)
    assert len(hits) > 0
    assert hits[0]["parent_doc_id"] == "02_severity_sla"
    assert hits[0]["similarity"] >= 0.35, f"Expected similarity >= 0.35, got {hits[0]['similarity']}"


def test_out_of_domain_retrieval_below_threshold(rag_instance: RAGCore):
    unrelated_query = "How do I make chocolate chip cookies from scratch?"
    hits = rag_instance.retrieve(unrelated_query, strategy="fixed_overlap", top_k=3)
    assert len(hits) > 0
    top_sim = hits[0]["similarity"]
    # Empirical threshold is ~0.3221; unrelated query should score well below 0.30
    assert top_sim < 0.28, f"Out of domain query scored too high: {top_sim}"


def test_grounded_answer_fallback_on_unrelated(rag_instance: RAGCore):
    unrelated_query = "What was the score of the cricket match yesterday?"
    hits = rag_instance.retrieve(unrelated_query, strategy="fixed_overlap", top_k=3)
    threshold = 0.3221
    answer = grounded_answer(hits, threshold)
    assert answer["outcome"] == "not_found"
    assert answer["grounded"] is False
    assert len(answer["citations"]) == 0
    assert "I don't know based on the available verified information" in answer["answer"]


def test_grounded_answer_success_with_citations(rag_instance: RAGCore):
    query = "Can I get a refund or compensation for an order?"
    hits = rag_instance.retrieve(query, strategy="fixed_overlap", top_k=3)
    threshold = 0.3221
    answer = grounded_answer(hits, threshold)
    assert answer["outcome"] == "answered"
    assert answer["grounded"] is True
    assert len(answer["citations"]) > 0
    assert answer["citations"][0]["id"] == "04_refund_compensation"
    assert answer["citations"][0]["source_type"] == "SYNTHETIC_DEMO_POLICY"
