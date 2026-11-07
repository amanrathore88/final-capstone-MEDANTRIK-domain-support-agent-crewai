"""Tests for ticket lookup tool, escalation scoring, and thresholds (Task 6)."""
from support.tickets import REVIEW_THRESHOLD, check_support_ticket_status


def test_ticket_lookup_existing_record():
    result = check_support_ticket_status("MED-0003")
    assert result["found"] is True
    assert result["record_id"] == "MED-0003"
    t = result["ticket"]
    assert t["product"] == "NODex"
    assert t["category"] == "Technical Issue"
    assert t["status"] == "Escalated"
    assert 0.0 <= result["escalation_score"] <= 1.0
    assert result["review_threshold"] == REVIEW_THRESHOLD


def test_ticket_lookup_missing_record():
    result = check_support_ticket_status("MED-9999")
    assert result["found"] is False
    assert "not found" in result["error"].lower()


def test_escalation_recommendation_logic():
    # MED-0003: escalated=True, age=29, reopen=0 -> score = 0.50 + 0.30*(29/30) = 0.79 > 0.366667
    res_high = check_support_ticket_status("MED-0003")
    assert res_high["recommended_review"] is True
    assert res_high["escalation_score"] > REVIEW_THRESHOLD

    # MED-0001: escalated=False, age=25, reopen=0 -> score = 0.30*(25/30) = 0.25 <= 0.366667
    res_low = check_support_ticket_status("MED-0001")
    assert res_low["escalation_score"] <= REVIEW_THRESHOLD
    assert res_low["recommended_review"] is False
