"""Unit tests for SQLite database schema, seeding, and auditing."""
from pathlib import Path
import pytest
from database.db import Database, compute_escalation_score


@pytest.fixture
def test_db(tmp_path: Path):
    db_file = tmp_path / "test_medantrik.db"
    return Database(db_file)


def test_db_seeding_and_counts(test_db: Database):
    metrics = test_db.get_metrics()
    assert metrics["total_tickets"] == 80
    assert metrics["escalated_percentage"] == 17.5
    assert metrics["open_tickets"] == 17
    assert metrics["knowledge_topics"] == 12


def test_get_ticket_by_id(test_db: Database):
    t = test_db.get_ticket("MED-0001")
    assert t is not None
    assert t["record_id"] == "MED-0001"
    assert t["category"] == "Account Access"
    assert t["status"] == "In Progress"
    assert isinstance(t["escalation_score"], float)
    assert t["synthetic"] is True


def test_create_demo_ticket_and_audit(test_db: Database):
    new_t = test_db.create_ticket(
        category="Technical Issue",
        subject="OxySense calibration failure report",
        product="OxySense",
        status="Open",
        escalated=True,
        actor="clinician_user",
        details="User reported abnormal purity drift",
    )
    assert new_t["record_id"] == "MED-0081"
    assert new_t["category"] == "Technical Issue"
    assert new_t["escalated"] is True

    audit = test_db.get_audit_events("MED-0081")
    assert len(audit) == 1
    assert audit[0]["action"] == "CREATED"
    assert audit[0]["to_status"] == "Open"
    assert audit[0]["actor"] == "clinician_user"


def test_status_update_and_audit_trail(test_db: Database):
    updated = test_db.update_ticket_status(
        "MED-0001",
        "Resolved",
        actor="operator_sarah",
        details="Provided password reset link after verification",
    )
    assert updated["status"] == "Resolved"

    events = test_db.get_audit_events("MED-0001")
    assert len(events) >= 2  # SEEDED + STATUS_CHANGE
    last_event = events[-1]
    assert last_event["action"] == "STATUS_CHANGE"
    assert last_event["from_status"] == "In Progress"
    assert last_event["to_status"] == "Resolved"
    assert last_event["actor"] == "operator_sarah"


def test_sessions_and_messages(test_db: Database):
    session_id = "sess-test-123"
    test_db.create_session(session_id, customer_name="Dr. Mehta")
    sess = test_db.get_session(session_id)
    assert sess is not None
    assert sess["customer_name"] == "Dr. Mehta"

    test_db.add_message(session_id, "user", "What is NODex?")
    test_db.add_message(session_id, "assistant", "NODex is a compact respiratory device.", sources=[{"id": "nodex", "type": "public"}])

    msgs = test_db.get_messages(session_id)
    assert len(msgs) == 2
    assert msgs[0]["role"] == "user"
    assert msgs[1]["sources"] == [{"id": "nodex", "type": "public"}]


def test_escalation_score_formula():
    # score = 0.50*escalated + 0.30*(days/30) + 0.20*(reopen/3)
    s1 = compute_escalation_score(escalated=False, days_since_created=0, reopen_count=0)
    assert s1 == 0.0

    s2 = compute_escalation_score(escalated=True, days_since_created=30, reopen_count=3)
    assert s2 == 1.0

    s3 = compute_escalation_score(escalated=True, days_since_created=15, reopen_count=0)
    assert s3 == 0.50 + 0.15 == 0.65
