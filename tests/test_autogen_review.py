"""Tests for 2-agent AutoGen RoundRobinGroupChat review stage (Task 14)."""
import asyncio
from support.models import Citation, StageResult, SupportResponse, VerdictModel
from support.review import record_review_evidence, run_autogen_review


def test_autogen_review_approves_grounded_draft():
    stage = StageResult(
        kind="rag",
        data={
            "outcome": "answered",
            "answer": "OxySense is an inline oxygen analyzer.",
            "citations": [{"id": "product_oxysense", "title": "OxySense", "source_type": "PUBLIC_VERIFIED_FACT", "url": "https://medantrik.com"}],
        },
    )
    draft = SupportResponse(
        answer="OxySense is an inline oxygen analyzer.",
        outcome="answered",
        citations=[Citation(id="product_oxysense", title="OxySense", source_type="PUBLIC_VERIFIED_FACT", url="https://medantrik.com")],
    )
    result = asyncio.run(run_autogen_review(draft, [stage]))
    assert result["approved"] is True
    assert result["speakers"] == ["Policy_Compliance_Reviewer", "Final_Editor"]
    assert result["max_turns"] == 2
    assert "matches verified evidence" in result["reason"].lower()


def test_autogen_review_revises_ungrounded_draft():
    stage = StageResult(
        kind="rag",
        data={
            "outcome": "answered",
            "answer": "OxySense is an inline oxygen analyzer.",
            "citations": [{"id": "product_oxysense", "title": "OxySense", "source_type": "PUBLIC_VERIFIED_FACT", "url": "https://medantrik.com"}],
        },
    )
    unsupported_draft = SupportResponse(
        answer="OxySense offers a 100% cure rate and unconditional lifetime warranty replacement within 1 hour.",
        outcome="answered",
        citations=[Citation(id="product_oxysense", title="OxySense", source_type="PUBLIC_VERIFIED_FACT", url="https://medantrik.com")],
    )
    result = asyncio.run(run_autogen_review(unsupported_draft, [stage]))
    assert result["approved"] is False
    assert "100% cure rate" not in result["final_answer"]
    assert "replaced ungrounded" in result["reason"].lower()


def test_record_review_evidence():
    ev = record_review_evidence()
    assert ev["verification"]["approved_case_proven"] is True
    assert ev["verification"]["revised_case_proven"] is True
    assert ev["verification"]["two_agent_round_robin"] is True
