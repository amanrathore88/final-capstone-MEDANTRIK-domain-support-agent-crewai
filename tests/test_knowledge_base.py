"""Unit tests verifying knowledge-base structure and catalog integrity (Task 2)."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "knowledge_base"
CATALOG_PATH = ROOT / "data" / "product_catalog.json"

REQUIRED_TOPICS = [
    "01_ticket_priority",
    "02_severity_sla",
    "03_escalation_matrix",
    "04_refund_compensation",
    "05_communication_channels",
    "06_business_hours",
    "07_repeat_complaints",
    "08_service_credit",
    "09_feedback",
    "10_vip_handling",
    "11_outage_communication",
    "12_ticket_retention",
]


def count_sentences(text: str) -> int:
    # Remove markdown headers and blockquotes
    cleaned = []
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#") or line.startswith(">"):
            continue
        if line:
            cleaned.append(line)
    body = " ".join(cleaned)
    # Match sentences ending with period, question mark or exclamation mark
    sentences = [s.strip() for s in re.split(r"[.!?]+", body) if s.strip()]
    return len(sentences)


def test_knowledge_base_completeness():
    files = list(KB_DIR.glob("*.md"))
    assert len(files) >= 12, f"Expected >= 12 policy files, found {len(files)}"
    stem_names = [f.stem for f in files]
    for req in REQUIRED_TOPICS:
        assert req in stem_names, f"Missing required policy document: {req}"


def test_sentence_counts_and_disclaimer():
    for f in KB_DIR.glob("*.md"):
        content = f.read_text(encoding="utf-8")
        assert "SYNTHETIC CAPSTONE POLICY" in content, f"{f.name} must include the synthetic policy banner"
        s_count = count_sentences(content)
        assert 2 <= s_count <= 5, f"{f.name} has {s_count} sentences; required 2–5 sentences"


def test_public_catalog_integrity():
    assert CATALOG_PATH.exists(), "Product catalog JSON must exist"
    with open(CATALOG_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "products" in data
    prod_ids = [p["id"] for p in data["products"]]
    assert "oxysense" in prod_ids
    assert "nodex" in prod_ids
    assert "iron_lung" in prod_ids
    assert "company" in data
    assert "Medantrik" in data["company"]["name"]
    assert "contact" in data
    assert "hours_status" in data["contact"]
