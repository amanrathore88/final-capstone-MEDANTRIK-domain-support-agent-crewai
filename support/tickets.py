"""Support ticket lookup tool with empirical escalation scoring (Task 6)."""
from __future__ import annotations
from typing import Any
from database.db import Database, compute_escalation_score
from support.models import TicketInfo

REVIEW_THRESHOLD = 0.366667  # 80th percentile of days_since_created/escalation distribution in seed dataset


def check_support_ticket_status(record_id: str, db: Database | None = None) -> dict[str, Any]:
    """Look up a synthetic ticket by record_id and compute its escalation score."""
    clean_id = record_id.strip().upper()
    if not clean_id.startswith("MED-"):
        clean_id = f"MED-{clean_id.zfill(4)}"

    database = db or Database()
    ticket_dict = database.get_ticket(clean_id)

    if not ticket_dict:
        return {
            "found": False,
            "record_id": clean_id,
            "error": f"Ticket {clean_id} was not found in the synthetic dataset.",
        }

    score = compute_escalation_score(
        escalated=ticket_dict["escalated"],
        days_since_created=ticket_dict["days_since_created"],
        reopen_count=ticket_dict.get("reopen_count", 0),
    )

    recommended_review = score > REVIEW_THRESHOLD

    info = TicketInfo(
        record_id=ticket_dict["record_id"],
        category=ticket_dict["category"],
        status=ticket_dict["status"],
        resolution_time_hours=ticket_dict["resolution_time_hours"],
        days_since_created=ticket_dict["days_since_created"],
        escalated=ticket_dict["escalated"],
        product=ticket_dict["product"],
        reopen_count=ticket_dict.get("reopen_count", 0),
        subject=ticket_dict["subject"],
        escalation_score=score,
        recommended_review=recommended_review,
    )

    return {
        "found": True,
        "record_id": clean_id,
        "ticket": info.model_dump(),
        "escalation_score": score,
        "review_threshold": REVIEW_THRESHOLD,
        "recommended_review": recommended_review,
        "summary": f"Ticket {clean_id} for {info.product} ({info.category}) is currently {info.status}. Age: {info.days_since_created} days, Reopens: {info.reopen_count}, Escalation score: {score:.4f} (Review recommended: {recommended_review}).",
    }
