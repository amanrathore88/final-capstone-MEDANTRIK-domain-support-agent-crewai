"""Tests for LangChain session memory isolation, multi-turn carrying, and response caching (Tasks 8 & 16)."""
import pytest
from support.cache import SHARED_CACHE, normalize_query, record_cache_evidence
from support.crew import orchestrate_support_query
from support.session import (
    generate_memory_transcripts,
    get_session_history,
    record_turn,
    reset_session,
    resolve_session_context,
)


def fast_test_orchestrator(query: str, session_id: str = "default"):
    """Deterministic fast orchestrator for unit-testing session memory resolution."""
    augmented, ticket_id = resolve_session_context(session_id, query)
    if ticket_id == "MED-0003":
        resp = {
            "answer": "Ticket MED-0003 for NODex is currently Escalated.",
            "ticket": {"record_id": "MED-0003", "status": "Escalated"},
            "outcome": "answered",
        }
    else:
        resp = {
            "answer": "No ticket context found for this request.",
            "ticket": None,
            "outcome": "not_found",
        }
    record_turn(session_id, query, resp["answer"])
    return {"session_id": session_id, "response": resp}


def fast_cache_orchestrator(query: str, session_id: str = "default"):
    """Deterministic fast orchestrator for unit-testing cache hit/miss behavior."""
    cached = SHARED_CACHE.get(query)
    if cached:
        return {"response": cached["response"], "tool_calls": [], "cached": True}
    res = {
        "answer": "Under this fictional demo policy, unused items can be returned within 7 days.",
        "outcome": "answered",
        "guardrails": [],
    }
    SHARED_CACHE.set(query, {"response": res})
    return {"response": res, "tool_calls": [{"tool": "rag_lookup"}], "cached": False}


def test_session_context_resolution():
    sess_id = "test-session-turn-carry"
    reset_session(sess_id)

    # Turn 1
    record_turn(sess_id, "Check ticket MED-0003 status", "Ticket MED-0003 is currently Escalated.")

    # Turn 2: uses 'it' referring to MED-0003
    augmented, ticket_id = resolve_session_context(sess_id, "Why was it escalated?")
    assert ticket_id == "MED-0003"
    assert "referring to ticket MED-0003" in augmented


def test_session_isolation():
    sess_a = "session-a-private"
    sess_b = "session-b-fresh"
    reset_session(sess_a)
    reset_session(sess_b)

    record_turn(sess_a, "My ticket is MED-0003", "Recorded ticket MED-0003.")

    # Session B should have no memory of Session A's ticket
    augmented, ticket_id = resolve_session_context(sess_b, "Why was it escalated?")
    assert ticket_id is None
    assert get_session_history(sess_b).messages == []


def test_memory_transcripts_generation():
    report = generate_memory_transcripts(fast_test_orchestrator)
    assert report["multi_turn_session"]["context_carried_successfully"] is True
    assert report["isolated_fresh_session"]["isolated_from_prior_session"] is True


def test_normalized_response_caching():
    SHARED_CACHE.clear()
    q = "What is the return and refund policy?"
    mock_resp = {
        "response": {"answer": "Demo refund policy excerpt.", "outcome": "answered", "guardrails": []},
        "review": {"approved": True, "reason": "Verified"},
    }

    # Set cache
    SHARED_CACHE.set(q, mock_resp)

    # Lookup with varying casing and extra spaces
    variations = [
        "what is the return and refund policy?",
        "  WHAT IS THE RETURN AND REFUND POLICY?  ",
        "What is the return, and refund policy!",
    ]
    for v in variations:
        cached = SHARED_CACHE.get(v)
        assert cached is not None, f"Failed normalized lookup for variation: '{v}'"

    assert SHARED_CACHE.hits == 3


def test_cache_skips_private_tickets():
    SHARED_CACHE.clear()
    ticket_resp = {
        "response": {"answer": "Ticket MED-0003 info", "outcome": "answered", "guardrails": []},
        "ticket": {"record_id": "MED-0003"},
    }
    SHARED_CACHE.set("Check MED-0003", ticket_resp)
    assert SHARED_CACHE.get("Check MED-0003") is None
    assert SHARED_CACHE.stats()["cached_entries"] == 0


def test_cache_evidence_recording():
    evidence = record_cache_evidence(fast_cache_orchestrator)
    assert evidence["verification"]["cache_hit_proven"] is True
    assert evidence["verification"]["private_ticket_caching_blocked"] is True


@pytest.mark.integration
def test_end_to_end_orchestration_integration():
    """Real end-to-end orchestration pipeline test (RAG + CrewAI + AutoGen + Session + Cache)."""
    res = orchestrate_support_query("What is the return and refund policy for orders?", session_id="int-test-1")
    assert res["response"]["outcome"] in ("answered", "not_found")
    assert "review" in res
    assert "governance" in res
