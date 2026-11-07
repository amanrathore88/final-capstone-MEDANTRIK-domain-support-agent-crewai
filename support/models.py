"""Pydantic schemas for structured support responses, tickets, verdicts, and stages."""
from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field


class Citation(BaseModel):
    id: str
    title: str
    source_type: Literal["SYNTHETIC_DEMO_POLICY", "PUBLIC_VERIFIED_FACT"]
    url: str
    similarity: float | None = None


class TicketInfo(BaseModel):
    record_id: str
    category: str
    status: str
    resolution_time_hours: int
    days_since_created: int
    escalated: bool
    product: str
    reopen_count: int = 0
    subject: str
    escalation_score: float
    recommended_review: bool = False


class SupportResponse(BaseModel):
    answer: str
    outcome: Literal["answered", "partial", "not_found", "clarification", "refused", "escalated"]
    citations: list[Citation] = Field(default_factory=list)
    ticket: TicketInfo | None = None
    guardrails: list[str] = Field(default_factory=list)
    needs_human: bool = False
    trace_id: str | None = None


class VerdictModel(BaseModel):
    approved: bool
    final_answer: str
    reason: str


class StageResult(BaseModel):
    kind: str
    requested: bool = True
    data: dict[str, Any] = Field(default_factory=dict)
