"""FastAPI backend with HTTP endpoints and WebSocket support (Task 11)."""
from __future__ import annotations
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import time
from typing import Any, Optional

from fastapi import FastAPI, HTTPException, Query, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.logging import get_trace_id, log_request_event
from api.models import (
    AskRequest,
    AskResponse,
    DecisionRequest,
    HealthResponse,
    MetricsResponse,
    ResetSessionRequest,
    ResetSessionResponse,
    TicketCreateRequest,
)
from database.db import Database
from rag.config import ROOT
from rag.core import RAGCore
from support.crew import orchestrate_support_query
from support.governance import BudgetExceededError, RequestBudget, RISK_CLASSIFICATION
from support.guardrails import mask_phone_numbers
from support.models import Citation, SupportResponse, TicketInfo
from support.session import reset_session

app = FastAPI(
    title="Medantrik Assist API",
    description="Intelligent Device Support OS for Medantrik Medtech (Synthetic Demonstration)",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_RAG_CORE: Optional[RAGCore] = None
_DB: Optional[Database] = None


def get_rag() -> RAGCore:
    global _RAG_CORE
    if _RAG_CORE is None:
        _RAG_CORE = RAGCore()
    return _RAG_CORE


def get_db() -> Database:
    global _DB
    if _DB is None:
        _DB = Database()
    return _DB


@app.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    rag = get_rag()
    db = get_db()
    counts = {
        "fixed_overlap": rag.collection_fixed.count(),
        "sentence_based": rag.collection_sentence.count(),
    }
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        mock_llm=True,
        collections=counts,
        database_connected=db.path.exists(),
    )


@app.post("/ask", response_model=AskResponse)
def ask(req: AskRequest) -> AskResponse:
    t0 = time.time()
    trace_id = get_trace_id()
    session_id = req.session_id or "default"

    try:
        result = orchestrate_support_query(
            query=req.query,
            session_id=session_id,
            db=get_db(),
            rag=get_rag(),
        )
    except BudgetExceededError as exc:
        latency_ms = (time.time() - t0) * 1000
        log_request_event(
            trace_id=trace_id,
            session_id=session_id,
            query=req.query,
            outcome="rejected_budget",
            latency_ms=latency_ms,
            tokens=0,
            cached=False,
            status_code=413,
            guardrails=["BUDGET_EXCEEDED"],
        )
        raise HTTPException(status_code=413, detail=str(exc))

    latency_ms = (time.time() - t0) * 1000
    resp_dict = result["response"]
    tokens = result.get("governance", {}).get("total_tokens", 0)
    cached = bool(result.get("cached", False))

    log_request_event(
        trace_id=trace_id,
        session_id=session_id,
        query=req.query,
        outcome=resp_dict.get("outcome", "answered"),
        latency_ms=latency_ms,
        tokens=tokens,
        cached=cached,
        status_code=200,
        guardrails=resp_dict.get("guardrails", []),
    )

    ticket_data = None
    if resp_dict.get("ticket"):
        ticket_data = TicketInfo(**resp_dict["ticket"])

    citations = [Citation(**c) for c in resp_dict.get("citations", [])]

    return AskResponse(
        trace_id=trace_id,
        session_id=session_id,
        answer=resp_dict["answer"],
        outcome=resp_dict.get("outcome", "answered"),
        citations=citations,
        ticket=ticket_data,
        guardrails=resp_dict.get("guardrails", []),
        needs_human=bool(resp_dict.get("needs_human", False)),
        review=result.get("review"),
        cached=cached,
        latency_ms=round(latency_ms, 2),
        governance=result.get("governance"),
    )


@app.post("/reset-session", response_model=ResetSessionResponse)
def reset_session_endpoint(req: ResetSessionRequest) -> ResetSessionResponse:
    t0 = time.time()
    trace_id = get_trace_id()
    reset_session(req.session_id)
    latency_ms = (time.time() - t0) * 1000

    log_request_event(
        trace_id=trace_id,
        session_id=req.session_id,
        query="[RESET_SESSION]",
        outcome="session_reset",
        latency_ms=latency_ms,
        tokens=0,
        cached=False,
        status_code=200,
    )
    return ResetSessionResponse(
        session_id=req.session_id,
        status="reset",
        message=f"Conversation memory reset for session '{req.session_id}'.",
    )


@app.get("/tickets")
def list_tickets(
    status: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    product: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=500),
):
    db = get_db()
    return db.list_tickets(status=status, category=category, product=product, search=search, limit=limit)


@app.get("/tickets/{record_id}")
def get_ticket_detail(record_id: str):
    db = get_db()
    ticket = db.get_ticket(record_id)
    if not ticket:
        raise HTTPException(status_code=404, detail=f"Ticket '{record_id}' not found")
    audit = db.get_audit_events(record_id)
    return {"ticket": ticket, "audit_events": audit}


@app.post("/tickets")
def create_ticket(req: TicketCreateRequest):
    db = get_db()
    created = db.create_ticket(
        category=req.category,
        subject=req.subject,
        product=req.product_name or "NODex",
        status="Open",
        escalated=False,
        actor="customer_api",
        details=f"Created via API: role={req.customer_role}, desc={req.description[:60]}",
    )
    return created


@app.post("/tickets/{record_id}/decision")
def record_ticket_decision(record_id: str, req: DecisionRequest):
    db = get_db()
    current = db.get_ticket(record_id)
    if not current:
        raise HTTPException(status_code=404, detail=f"Ticket '{record_id}' not found")

    decision = req.decision.strip().lower()
    if "approve" in decision or "resolve" in decision:
        new_status = "Resolved"
    elif "reject" in decision or "close" in decision:
        new_status = "Closed"
    elif "escalat" in decision:
        new_status = "Escalated"
    else:
        new_status = "In Progress"

    updated = db.update_ticket_status(
        record_id=record_id,
        new_status=new_status,
        actor=req.operator or "Human Operator",
        details=f"Human Decision: {req.decision}. Notes: {req.notes}",
    )
    audit = db.get_audit_events(record_id)
    return {"ticket": updated, "audit_events": audit}


@app.get("/knowledge")
def get_knowledge():
    """Return categorized knowledge sources distinguishing VERIFIED PUBLIC vs DEMO POLICY."""
    catalog_path = ROOT / "data" / "product_catalog.json"
    products_info: list[dict] = []
    company_info: dict = {}
    if catalog_path.exists():
        with open(catalog_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            products_info = [
                {
                    "id": p["id"],
                    "name": p["name"],
                    "kind": p["kind"],
                    "description": p["safe_description"],
                    "provenance": "VERIFIED PUBLIC",
                    "source": p.get("source", "https://medantrik.com/"),
                }
                for p in data.get("products", [])
            ]
            company_info = data.get("company", {})

    policies: list[dict] = []
    kb_dir = ROOT / "knowledge_base"
    if kb_dir.exists():
        for file in sorted(kb_dir.glob("*.md")):
            content = file.read_text(encoding="utf-8")
            title = file.stem.replace("_", " ").title()
            policies.append({
                "slug": file.stem,
                "title": title,
                "provenance": "DEMO POLICY",
                "disclaimer": "Synthetic policy for capstone demonstration; not an official Medantrik policy.",
                "content": content,
            })

    return {
        "verified_public": {
            "company": company_info,
            "products": products_info,
        },
        "synthetic_policies": policies,
        "governance": RISK_CLASSIFICATION,
    }


@app.get("/metrics", response_model=MetricsResponse)
def get_metrics() -> MetricsResponse:
    db = get_db()
    m = db.get_metrics()
    return MetricsResponse(
        total_tickets=m["total_tickets"],
        escalated_count=m["escalated_tickets"],
        escalated_percentage=m["escalated_percentage"],
        categories=m["by_category"],
        statuses=m["by_status"],
        severities={"Critical": 8, "High": 22, "Medium": 34, "Low": 16},  # heuristic distribution
    )


@app.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """Interactive WebSocket chat endpoint with graceful disconnect handling (Task 11)."""
    await websocket.accept()
    session_id = "ws-client"

    try:
        while True:
            data = await websocket.receive_json()
            query = data.get("query", "")
            session_id = data.get("session_id", session_id)

            if not query.strip():
                await websocket.send_json({"type": "error", "message": "Query cannot be empty"})
                continue

            t0 = time.time()
            trace_id = get_trace_id()

            # Check budget upfront before entering pipeline stages
            try:
                RequestBudget().check_input_size(query)
            except BudgetExceededError as exc:
                latency_ms = (time.time() - t0) * 1000
                log_request_event(
                    trace_id=trace_id,
                    session_id=session_id,
                    query=query,
                    outcome="rejected_budget",
                    latency_ms=latency_ms,
                    status_code=413,
                    guardrails=["BUDGET_EXCEEDED"],
                )
                await websocket.send_json({
                    "type": "error",
                    "error_code": "BUDGET_EXCEEDED",
                    "message": str(exc),
                })
                continue

            # Inform client of progress stages
            await websocket.send_json({
                "type": "stage",
                "stage": "guardrails",
                "message": "Validating input security and medical safety...",
            })

            try:
                # Execute orchestration (run synchronous orchestrator)
                result = await asyncio.to_thread(
                    orchestrate_support_query,
                    query=query,
                    session_id=session_id,
                    db=get_db(),
                    rag=get_rag(),
                )
            except BudgetExceededError as exc:
                latency_ms = (time.time() - t0) * 1000
                log_request_event(
                    trace_id=trace_id,
                    session_id=session_id,
                    query=query,
                    outcome="rejected_budget",
                    latency_ms=latency_ms,
                    status_code=413,
                    guardrails=["BUDGET_EXCEEDED"],
                )
                await websocket.send_json({
                    "type": "error",
                    "error_code": "BUDGET_EXCEEDED",
                    "message": str(exc),
                })
                continue

            latency_ms = (time.time() - t0) * 1000
            resp_dict = result["response"]
            tokens = result.get("governance", {}).get("total_tokens", 0)
            cached = bool(result.get("cached", False))

            log_request_event(
                trace_id=trace_id,
                session_id=session_id,
                query=query,
                outcome=resp_dict.get("outcome", "answered"),
                latency_ms=latency_ms,
                tokens=tokens,
                cached=cached,
                status_code=200,
                guardrails=resp_dict.get("guardrails", []),
            )

            await websocket.send_json({
                "type": "response",
                "trace_id": trace_id,
                "session_id": session_id,
                "response": resp_dict,
                "review": result.get("review"),
                "governance": result.get("governance"),
                "cached": cached,
                "latency_ms": round(latency_ms, 2),
            })

    except WebSocketDisconnect:
        # Graceful disconnect: do not crash, allow next client connection
        pass
    except Exception as exc:
        try:
            await websocket.send_json({"type": "error", "message": f"Server error: {exc}"})
        except Exception:
            pass

# Mount frontend production build if available
dist_dir = ROOT / "frontend" / "dist"
if dist_dir.exists():
    from fastapi.staticfiles import StaticFiles
    app.mount("/", StaticFiles(directory=str(dist_dir), html=True), name="static")
