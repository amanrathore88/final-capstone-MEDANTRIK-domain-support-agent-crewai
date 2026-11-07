"""WebSocket integration tests including disconnect and reconnect validation (Task 11)."""
from __future__ import annotations
import pytest
from fastapi.testclient import TestClient

from api.app import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_websocket_chat_successful_flow(client):
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({
            "query": "Do priority test customers bypass safety checks?",
            "session_id": "ws-test-vip",
        })
        # 1. Staged progress notification
        msg1 = ws.receive_json()
        assert msg1["type"] == "stage"
        assert msg1["stage"] == "guardrails"

        # 2. Final response
        msg2 = ws.receive_json()
        assert msg2["type"] == "response"
        assert msg2["session_id"] == "ws-test-vip"
        assert msg2["response"]["outcome"] == "answered"
        assert len(msg2["response"]["answer"]) > 20
        assert any("10_vip_handling" in c["id"] for c in msg2["response"]["citations"])


def test_websocket_ticket_lookup(client):
    with client.websocket_connect("/ws/chat") as ws:
        ws.send_json({
            "query": "Check ticket MED-0003 status",
            "session_id": "ws-test-lookup",
        })
        msg1 = ws.receive_json()
        assert msg1["type"] == "stage"

        msg2 = ws.receive_json()
        assert msg2["type"] == "response"
        ticket = msg2["response"]["ticket"]
        assert ticket is not None
        assert ticket["record_id"] == "MED-0003"
        assert "escalation_score" in ticket


def test_websocket_budget_rejection(client):
    with client.websocket_connect("/ws/chat") as ws:
        huge_query = "Excessive token test string. " * 10000
        ws.send_json({
            "query": huge_query,
            "session_id": "ws-oversize",
        })
        msg = ws.receive_json()
        assert msg["type"] == "error"
        assert msg["error_code"] == "BUDGET_EXCEEDED"


def test_websocket_disconnect_and_subsequent_client(client):
    """Verify that a client disconnecting abruptly does not crash the server for subsequent clients."""
    # Client 1 connects and disconnects cleanly
    with client.websocket_connect("/ws/chat") as ws1:
        ws1.send_json({"query": "Hello from client 1", "session_id": "client-1"})
        stage = ws1.receive_json()
        assert stage["type"] == "stage"
        resp = ws1.receive_json()
        assert resp["type"] == "response"
        # Context exit triggers disconnect

    # Client 2 connects immediately afterwards
    with client.websocket_connect("/ws/chat") as ws2:
        ws2.send_json({"query": "Hello from client 2", "session_id": "client-2"})
        stage2 = ws2.receive_json()
        assert stage2["type"] == "stage"
        resp2 = ws2.receive_json()
        assert resp2["type"] == "response"
        assert resp2["session_id"] == "client-2"
