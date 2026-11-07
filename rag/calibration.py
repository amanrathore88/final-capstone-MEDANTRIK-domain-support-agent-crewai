"""Empirical similarity calibration for grounded generation threshold (Task 4)."""
from __future__ import annotations
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag.core import RAGCore

CALIBRATION_QUERIES = [
    {
        "id": "in_01",
        "type": "in_domain",
        "query": "What is the severity SLA response time for critical issues?",
        "expected_doc": "02_severity_sla",
    },
    {
        "id": "in_02",
        "type": "in_domain",
        "query": "Can I get a refund or compensation for an order?",
        "expected_doc": "04_refund_compensation",
    },
    {
        "id": "in_03",
        "type": "in_domain",
        "query": "What kind of device is OxySense and what does it monitor?",
        "expected_doc": "product_oxysense",
    },
    {
        "id": "out_01",
        "type": "out_of_domain",
        "query": "How do I make chocolate chip cookies from scratch?",
        "expected_doc": None,
    },
    {
        "id": "out_02",
        "type": "out_of_domain",
        "query": "What was the score of the cricket match yesterday?",
        "expected_doc": None,
    },
]


def run_calibration() -> dict:
    rag = RAGCore()
    results = {"fixed_overlap": [], "sentence_based": []}

    for item in CALIBRATION_QUERIES:
        for strategy in ["fixed_overlap", "sentence_based"]:
            hits = rag.retrieve(item["query"], strategy=strategy, top_k=1)
            sim = hits[0]["similarity"] if hits else 0.0
            top_doc = hits[0]["parent_doc_id"] if hits else None
            results[strategy].append({
                "id": item["id"],
                "type": item["type"],
                "query": item["query"],
                "top_1_similarity": sim,
                "top_1_doc": top_doc,
            })

    thresholds = {}
    analysis = {}

    for strategy, rows in results.items():
        in_sims = [r["top_1_similarity"] for r in rows if r["type"] == "in_domain"]
        out_sims = [r["top_1_similarity"] for r in rows if r["type"] == "out_of_domain"]

        min_in = min(in_sims)
        max_out = max(out_sims)
        # Threshold chosen midway between the highest out-of-domain and lowest in-domain
        chosen_threshold = round((min_in + max_out) / 2.0, 4)

        thresholds[strategy] = chosen_threshold
        analysis[strategy] = {
            "min_in_domain_similarity": min_in,
            "max_out_of_domain_similarity": max_out,
            "margin": round(min_in - max_out, 4),
            "chosen_threshold": chosen_threshold,
            "clusters_separated": min_in > max_out,
        }

    report = {
        "queries": CALIBRATION_QUERIES,
        "results_by_strategy": results,
        "analysis": analysis,
        "recommended_strategy": "fixed_overlap",
        "recommended_threshold": thresholds["fixed_overlap"],
    }

    out_file = ROOT / "evidence" / "calibration.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    rep = run_calibration()
    print("Calibration complete:")
    print(json.dumps(rep["analysis"], indent=2))
