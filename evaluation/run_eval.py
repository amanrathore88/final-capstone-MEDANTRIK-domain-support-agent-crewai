"""Execute 15-case evaluation suite and produce evidence/evaluation_results.json (Task 13)."""
from __future__ import annotations
import json
from pathlib import Path
import time
from typing import Any

from evaluation.judge import ResponseJudge
from rag.config import ROOT
from support.crew import orchestrate_support_query


def run_full_evaluation() -> dict[str, Any]:
    cases_file = ROOT / "data" / "evaluation_cases.json"
    with open(cases_file, "r", encoding="utf-8") as f:
        cases_data = json.load(f)
    cases = cases_data["cases"]

    judge = ResponseJudge()
    results: list[dict[str, Any]] = []

    print(f"Executing evaluation across {len(cases)} cases...")
    for c in cases:
        t0 = time.time()
        # Ensure fresh session per eval case
        sess_id = f"eval-session-{c['id']}"
        system_output = orchestrate_support_query(c["query"], session_id=sess_id)
        eval_score = judge.evaluate_case(c, system_output)
        latency = (time.time() - t0) * 1000
        eval_score["latency_ms"] = round(latency, 2)
        results.append(eval_score)
        print(f"  [{c['id']}] {c['topic'][:35]:35s} | Acc: {eval_score['scores']['accuracy']} "
              f"Grd: {eval_score['scores']['grounding']} Cmp: {eval_score['scores']['completeness']} "
              f"Saf: {eval_score['scores']['safety']} | Avg: {eval_score['average']}")

    total = len(results)
    avg_accuracy = round(sum(r["scores"]["accuracy"] for r in results) / total, 3)
    avg_grounding = round(sum(r["scores"]["grounding"] for r in results) / total, 3)
    avg_completeness = round(sum(r["scores"]["completeness"] for r in results) / total, 3)
    avg_safety = round(sum(r["scores"]["safety"] for r in results) / total, 3)
    global_avg = round((avg_accuracy + avg_grounding + avg_completeness + avg_safety) / 4.0, 3)

    summary = {
        "benchmark": "Medantrik Assist 15-Case Evaluation Suite",
        "total_cases": total,
        "metrics_average": {
            "accuracy": avg_accuracy,
            "grounding": avg_grounding,
            "completeness": avg_completeness,
            "safety": avg_safety,
            "overall": global_avg,
        },
        "cases": results,
    }

    out_file = ROOT / "evidence" / "evaluation_results.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("\n--- Evaluation Summary ---")
    print(f"Total Cases:     {total}")
    print(f"Avg Accuracy:    {avg_accuracy} / 5.0")
    print(f"Avg Grounding:   {avg_grounding} / 5.0")
    print(f"Avg Completeness:{avg_completeness} / 5.0")
    print(f"Avg Safety:      {avg_safety} / 5.0")
    print(f"Overall Average: {global_avg} / 5.0")
    print(f"Saved to:        {out_file}")

    return summary


if __name__ == "__main__":
    run_full_evaluation()
