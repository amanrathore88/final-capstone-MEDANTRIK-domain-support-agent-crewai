"""Original seeded synthetic ticket generator for Medantrik Assist capstone.

No real customers, transactions or company support records are used.
Run: python seed_code/dataset.py
"""
from __future__ import annotations
from collections import Counter
import json
import random

SEED = 20261107
N_TICKETS = 80
CATEGORIES = (
    'Billing', 'Technical Issue', 'Account Access', 'Product Defect', 'General Inquiry'
)
STATUSES = ('Open', 'In Progress', 'Escalated', 'Resolved', 'Closed')
PRODUCTS = ('OxySense', 'NODex', 'Iron Lung')
CATEGORY_WEIGHTS = (14, 34, 12, 22, 18)
STATUS_WEIGHTS = (22, 26, 12, 22, 18)
HOUR_BOUNDS = {
    'Billing': (2, 72),
    'Technical Issue': (2, 144),
    'Account Access': (1, 48),
    'Product Defect': (8, 168),
    'General Inquiry': (1, 24),
}
SUBJECTS = {
    'Billing': ('Demo quote clarification', 'Invoice reference enquiry', 'Synthetic payment receipt query'),
    'Technical Issue': ('Connectivity issue reported', 'Device power indicator issue', 'Product training request'),
    'Account Access': ('Demo portal sign-in issue', 'Verification request', 'Password reset question'),
    'Product Defect': ('Unexpected device behavior reported', 'Equipment inspection requested', 'Error indicator reported'),
    'General Inquiry': ('Product availability question', 'Schedule a demo', 'Brochure request'),
}


def generate_support_tickets(seed: int = SEED, count: int = N_TICKETS) -> list[dict]:
    """Generate tickets from independent RNG draws without hand-editing rows."""
    rng = random.Random(seed)
    tickets = []
    for i in range(count):
        category = rng.choices(CATEGORIES, weights=CATEGORY_WEIGHTS, k=1)[0]
        status = rng.choices(STATUSES, weights=STATUS_WEIGHTS, k=1)[0]
        age = rng.randint(0, 30)
        lo, hi = HOUR_BOUNDS[category]
        resolution_time_hours = rng.randint(lo, hi)
        escalated = status == 'Escalated' or rng.random() < 0.085
        reopen_count = rng.choices([0, 1, 2, 3], weights=[72, 18, 8, 2], k=1)[0]
        subject = rng.choice(SUBJECTS[category])
        ticket = {
            'record_id': f'MED-{i+1:04d}',
            'category': category,
            'status': status,
            'resolution_time_hours': resolution_time_hours,
            'days_since_created': age,
            'escalated': escalated,
            'product': rng.choice(PRODUCTS),
            'reopen_count': reopen_count,
            'subject': subject,
            'synthetic': True,
        }
        tickets.append(ticket)
    return tickets


def validate(tickets: list[dict]) -> dict:
    categories = Counter(t['category'] for t in tickets)
    statuses = Counter(t['status'] for t in tickets)
    ratio = 100 * sum(t['escalated'] for t in tickets) / len(tickets)
    assert len(tickets) >= 40
    assert all(categories[c] >= 3 for c in CATEGORIES), categories
    assert all(statuses[s] >= 1 for s in STATUSES), statuses
    assert 10 <= ratio <= 30, ratio
    assert len({t['record_id'] for t in tickets}) == len(tickets)
    assert all(0 <= t['days_since_created'] <= 30 for t in tickets)
    return {'seed': SEED, 'total': len(tickets), 'category_counts': dict(categories),
            'status_counts': dict(statuses), 'escalated_pct': round(ratio, 2)}


SUPPORT_TICKETS = generate_support_tickets()
DATASET_REPORT = validate(SUPPORT_TICKETS)

if __name__ == '__main__':
    print(json.dumps(DATASET_REPORT, indent=2))
    print('Sample records:')
    print(json.dumps(SUPPORT_TICKETS[:3], indent=2))
