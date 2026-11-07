"""Integration and unit tests for FastAPI backend and logging (Tasks 11 & 12)."""
from __future__ import annotations
import json
from pathlib import Path
import re
import pytest
from fastapi.testclient import TestClient

from api.app import app
from api.logging import LOG_FILE, read_logged_events
from support.guardrails import INDIAN_PHONE_REGEX


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["mock_llm"] is True
    assert data["database_connected"] is True
    assert data["collections"]["fixed_overlap"] == 33
    assert data["collections"]["sentence_based"] == 60


def test_ask_endpoint_policy_query(client):
    req_body = {
        "query": "What is the demonstration response SLA for high-severity cases?",
        "session_id": "test-api-session-1",
    }
    res = client.post("/ask", json=req_body)
    assert res.status_code == 200
    data = res.json()
    assert data["trace_id"].startswith("trc-")
    assert data["session_id"] == "test-api-session-1"
    assert data["outcome"] == "answered"
    assert len(data["answer"]) > 20
    assert len(data["citations"]) > 0
    assert any("02_severity_sla" in c["id"] for c in data["citations"])
    assert data["latency_ms"] >= 0.0


def test_ask_endpoint_masks_phone_in_memory_and_logs(client):
    raw_phone = "+91 9876543210"
    query = f"My contact number is {raw_phone}. What is your ticket priority policy?"
    res = client.post("/ask", json={"query": query, "session_id": "test-api-phone"})
    assert res.status_code == 200
    data = res.json()
    assert "PII_PHONE_MASKING" in data["guardrails"]

    # Verify that raw_phone does NOT appear in the log file
    assert LOG_FILE.exists()
    logs = read_logged_events()
    phone_logs = [l for l in logs if l.get("session_id") == "test-api-phone"]
    assert len(phone_logs) >= 1
    for log_entry in phone_logs:
        assert raw_phone not in json.dumps(log_entry)
        assert "[PHONE_MASKED]" in log_entry["masked_query"]


def test_ask_endpoint_budget_rejection(client):
    huge_query = "Please explain the policy. " * 10000  # ~270,000 chars, ~67,500 tokens
    res = client.post("/ask", json={"query": huge_query, "session_id": "test-budget"})
    assert res.status_code == 413
    assert "exceeds" in res.json()["detail"].lower()


def test_reset_session_endpoint(client):
    # Establish a turn
    client.post("/ask", json={"query": "Hello support", "session_id": "test-reset-sess"})
    # Reset
    res = client.post("/reset-session", json={"session_id": "test-reset-sess"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "reset"
    assert data["session_id"] == "test-reset-sess"


def test_tickets_crud_and_decision(client):
    # 1. List tickets
    list_res = client.get("/tickets?limit=10")
    assert list_res.status_code == 200
    tickets = list_res.json()
    assert len(tickets) == 10
    assert tickets[0]["record_id"] == "MED-0001"

    # 2. Detail ticket
    det_res = client.get("/tickets/MED-0003")
    assert det_res.status_code == 200
    det = det_res.json()
    assert det["ticket"]["record_id"] == "MED-0003"
    assert len(det["audit_events"]) >= 1

    # 3. Create ticket
    new_t = {
        "category": "Billing Inquiry",
        "severity": "Medium",
        "customer_role": "Hospital Admin",
        "subject": "Invoice correction for sensor order",
        "description": "Please adjust invoice 1042.",
        "product_name": "OxySense",
    }
    create_res = client.post("/tickets", json=new_t)
    assert create_res.status_code == 200
    created = create_res.json()
    new_id = created["record_id"]
    assert new_id.startswith("MED-")

    # 4. Human Decision
    dec_body = {
        "decision": "Approved replacement shipment",
        "notes": "Verified hospital equipment warranty",
        "operator": "Senior Support Lead",
    }
    dec_res = client.post(f"/tickets/{new_id}/decision", json=dec_body)
    assert dec_res.status_code == 200
    dec_data = dec_res.json()
    assert dec_data["ticket"]["status"] == "Resolved"
    assert any("Approved replacement shipment" in a["details"] for a in dec_data["audit_events"])


def test_metrics_endpoint(client):
    res = client.get("/metrics")
    assert res.status_code == 200
    m = res.json()
    assert m["total_tickets"] >= 80
    assert m["escalated_count"] >= 14
    assert m["escalated_percentage"] > 0
    assert "Technical Issue" in m["categories"]
    assert "Open" in m["statuses"]


def test_knowledge_endpoint(client):
    res = client.get("/knowledge")
    assert res.status_code == 200
    data = res.json()
    # Verified public products
    products = data["verified_public"]["products"]
    prod_names = {p["name"] for p in products}
    assert "OxySense" in prod_names
    assert "NODex" in prod_names
    assert "Iron Lung" in prod_names

    # Synthetic policies
    policies = data["synthetic_policies"]
    assert len(policies) == 12
    slugs = {p["slug"] for p in policies}
    assert "01_ticket_priority" in slugs
    assert "12_ticket_retention" in slugs


def test_masked_jsonl_log_integrity():
    """Verify that every record in evidence/masked_logs.jsonl is well-formed with no raw phone numbers."""
    assert LOG_FILE.exists()
    records = read_logged_events()
    assert len(records) > 0
    for r in records:
        assert "trace_id" in r
        assert "timestamp" in r
        assert "latency_ms" in r
        assert "session_id" in r
        assert "outcome" in r
        assert "status_code" in r
        # Crucial: verify no unmasked Indian phone numbers
        masked_q = r.get("masked_query", "")
        matches = INDIAN_PHONE_REGEX.findall(masked_q)
        assert len(matches) == 0, f"Found raw phone number in log: {masked_q}"
