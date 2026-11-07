"""Structured JSONL logging for Medantrik Assist API (Task 12)."""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import threading
from typing import Any, Optional
import uuid

from rag.config import ROOT
from support.guardrails import mask_phone_numbers

LOG_FILE = ROOT / "evidence" / "masked_logs.jsonl"
_LOG_LOCK = threading.Lock()


def get_trace_id() -> str:
    """Generate a unique request trace ID."""
    return f"trc-{uuid.uuid4().hex[:12]}"


def log_request_event(
    *,
    trace_id: str,
    session_id: str,
    query: str,
    outcome: str,
    latency_ms: float,
    tokens: int = 0,
    cached: bool = False,
    status_code: int = 200,
    guardrails: Optional[list[str]] = None,
    extra: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    """Write exactly one structured, masked JSONL entry per request.

    Guarantees no raw PII (such as Indian phone numbers) enters the logs.
    """
    clean_query = mask_phone_numbers(query)
    record = {
        "trace_id": trace_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "latency_ms": round(latency_ms, 2),
        "tokens": tokens,
        "masked_query": clean_query,
        "outcome": outcome,
        "cached": cached,
        "status_code": status_code,
        "guardrails": guardrails or [],
    }
    if extra:
        record["extra"] = extra

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    line = json.dumps(record, sort_keys=True)
    with _LOG_LOCK:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    return record


def read_logged_events() -> list[dict[str, Any]]:
    """Read all recorded log entries."""
    if not LOG_FILE.exists():
        return []
    records = []
    with open(LOG_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
