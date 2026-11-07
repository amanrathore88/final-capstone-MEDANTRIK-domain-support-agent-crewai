"""FastAPI typed Pydantic models for Medantrik Assist (Task 11)."""
from __future__ import annotations
from typing import Any, Optional
from pydantic import BaseModel, Field

from support.models import Citation, SupportResponse, TicketInfo


class AskRequest(BaseModel):
    query: str = Field(..., description="Customer or clinician support question")
    session_id: Optional[str] = Field("default", description="Conversation session ID")


class AskResponse(BaseModel):
    trace_id: str
    session_id: str
    answer: str
    outcome: str
    citations: list[Citation] = Field(default_factory=list)
    ticket: Optional[TicketInfo] = None
    guardrails: list[str] = Field(default_factory=list)
    needs_human: bool = False
    review: Optional[dict[str, Any]] = None
    cached: bool = False
    latency_ms: float = 0.0
    governance: Optional[dict[str, Any]] = None


class ResetSessionRequest(BaseModel):
    session_id: str = Field(..., description="Conversation session to clear")


class ResetSessionResponse(BaseModel):
    session_id: str
    status: str = "reset"
    message: str = "Conversation history cleared for session."


class TicketCreateRequest(BaseModel):
    category: str
    severity: str
    customer_role: str
    subject: str
    description: str
    product_name: Optional[str] = "OxySense"


class DecisionRequest(BaseModel):
    decision: str = Field(..., description="Action: e.g. Approved, Rejected, Escalated to Specialist")
    notes: Optional[str] = Field("", description="Human reviewer notes")
    operator: Optional[str] = Field("Human Operator", description="Operator identifier")


class MetricsResponse(BaseModel):
    total_tickets: int
    escalated_count: int
    escalated_percentage: float
    categories: dict[str, int]
    statuses: dict[str, int]
    severities: Optional[dict[str, int]] = None


class HealthResponse(BaseModel):
    status: str
    version: str = "1.0.0"
    mock_llm: bool
    collections: dict[str, int]
    database_connected: bool
