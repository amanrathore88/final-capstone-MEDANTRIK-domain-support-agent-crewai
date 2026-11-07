"""Unit tests verifying dataset design constraints and determinism (Task 1)."""
from dataset import (
    CATEGORIES,
    HOUR_BOUNDS,
    N_TICKETS,
    PRODUCTS,
    SEED,
    STATUSES,
    SUPPORT_TICKETS,
    generate_support_tickets,
    validate,
)


def test_dataset_determinism():
    run_a = generate_support_tickets(seed=SEED, count=N_TICKETS)
    run_b = generate_support_tickets(seed=SEED, count=N_TICKETS)
    assert run_a == run_b, "Dataset generation must be strictly deterministic across calls"


def test_dataset_size_and_uniqueness():
    assert len(SUPPORT_TICKETS) >= 40
    assert len(SUPPORT_TICKETS) == 80
    ids = [t["record_id"] for t in SUPPORT_TICKETS]
    assert len(ids) == len(set(ids)), "Ticket IDs must be unique"
    assert all(t["record_id"].startswith("MED-") for t in SUPPORT_TICKETS)


def test_category_representation():
    report = validate(SUPPORT_TICKETS)
    cat_counts = report["category_counts"]
    for cat in CATEGORIES:
        assert cat in cat_counts, f"Category '{cat}' must be present"
        assert cat_counts[cat] >= 3, f"Category '{cat}' must have at least 3 tickets, got {cat_counts[cat]}"


def test_status_representation():
    report = validate(SUPPORT_TICKETS)
    status_counts = report["status_counts"]
    for st in STATUSES:
        assert st in status_counts, f"Status '{st}' must be present"
        assert status_counts[st] >= 1, f"Status '{st}' must have at least 1 ticket, got {status_counts[st]}"


def test_escalated_ratio_band():
    report = validate(SUPPORT_TICKETS)
    ratio = report["escalated_pct"]
    assert 10.0 <= ratio <= 30.0, f"Escalated percentage must land between 10% and 30%, got {ratio}%"
    assert ratio == 17.5


def test_field_ranges_and_integrity():
    for t in SUPPORT_TICKETS:
        assert 0 <= t["days_since_created"] <= 30
        assert t["product"] in PRODUCTS
        lo, hi = HOUR_BOUNDS[t["category"]]
        assert lo <= t["resolution_time_hours"] <= hi
        assert t["synthetic"] is True
        assert t["reopen_count"] in (0, 1, 2, 3)
