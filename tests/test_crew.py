"""Integration tests for CrewAI 3-agent crew kickoff, tools, and governance (Tasks 7 & 15)."""
import pytest
from rag.core import RAGCore
from support.crew import TicketTool, build_and_run_crew, orchestrate_support_query
from support.governance import BudgetExceededError, RequestBudget, RISK_CLASSIFICATION


@pytest.fixture(scope="module")
def rag_instance():
    return RAGCore()


def test_crew_rag_tool_invocation(rag_instance: RAGCore):
    events = []
    budget = RequestBudget()
    plan = {"policy_query": "What is the return and refund policy for orders?", "ticket_id": None}
    response, stages = build_and_run_crew(plan, events, budget, rag_instance, threshold=0.3221)

    assert response.outcome in ("answered", "not_found")
    # Verify tool was invoked
    tool_events = [e for e in events if e.get("event") == "tool_executed"]
    assert any(e["kind"] == "rag" for e in tool_events), "RAG tool must be invoked"


def test_crew_ticket_lookup_invocation(rag_instance: RAGCore):
    events = []
    budget = RequestBudget()
    plan = {"policy_query": "", "ticket_id": "MED-0003"}
    response, stages = build_and_run_crew(plan, events, budget, rag_instance, threshold=0.3221)

    assert response.ticket is not None
    assert response.ticket.record_id == "MED-0003"
    tool_events = [e for e in events if e.get("event") == "tool_executed"]
    assert any(e["kind"] == "ticket" for e in tool_events), "Ticket lookup tool must be invoked"


def test_least_autonomy_enforcement():
    events = []
    tool = TicketTool(events)
    # Direct execution without being designated Lookup Agent inside authorized context
    with pytest.raises(PermissionError) as exc:
        tool._run("MED-0001")
    assert "Only Lookup Agent is authorized" in str(exc.value)


def test_request_budget_rejection_on_oversize():
    oversized_input = "Tell me about OxySense " * 15000  # >60,000 tokens
    budget = RequestBudget(max_tokens=50000)
    with pytest.raises(BudgetExceededError) as exc:
        budget.check_input_size(oversized_input)
    assert "exceeds the per-request governance cap" in str(exc.value)


def test_risk_classification():
    assert RISK_CLASSIFICATION["level"] == "HIGH"
    assert "Medical Device" in RISK_CLASSIFICATION["domain"]
