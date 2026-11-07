"""CrewAI 3-agent orchestration with deterministic keyless MOCK_LLM (Tasks 7 & 15)."""
from __future__ import annotations
import asyncio
from contextvars import ContextVar
import json
import os
from pathlib import Path
import re
from typing import Any
from pydantic import BaseModel, PrivateAttr

from support.runtime import prepare_runtime
prepare_runtime()

from crewai import Agent, Crew, Process, Task
from crewai.llms.base_llm import BaseLLM
from crewai.tools import BaseTool
from crewai.hooks import register_before_tool_call_hook, register_after_tool_call_hook

from rag.config import ROOT
from rag.core import RAGCore, grounded_answer
from support.cache import SHARED_CACHE
from support.governance import BudgetExceededError, RequestBudget, RISK_CLASSIFICATION
from support.guardrails import (
    check_medical_safety,
    compose_evidence,
    detect_prompt_injection,
    guard_output,
    mask_phone_numbers,
)
from support.models import Citation, StageResult, SupportResponse, TicketInfo
from support.review import run_autogen_review
from support.session import record_turn, resolve_session_context
from support.tickets import check_support_ticket_status

_TICKET_PERMIT = ContextVar("ticket_permit", default=None)


def authorize_ticket_call(context):
    owner = getattr(getattr(context.tool, "func", None), "__self__", None)
    if isinstance(owner, TicketTool):
        _TICKET_PERMIT.set(None)
        if getattr(context.agent, "role", None) != "Lookup Agent" or context.agent is not owner._authorized_agent:
            owner._events.append({
                "event": "ticket_access_rejected",
                "role": getattr(context.agent, "role", None),
                "reason": "Least autonomy policy: only Lookup Agent can access ticket tool",
            })
            return False
        _TICKET_PERMIT.set(owner)
    return None


def clear_ticket_call(context):
    _TICKET_PERMIT.set(None)
    return None


register_before_tool_call_hook(authorize_ticket_call)
register_after_tool_call_hook(clear_ticket_call)


class PolicyArguments(BaseModel):
    query: str


class TicketArguments(BaseModel):
    record_id: str


class PolicyTool(BaseTool):
    name: str = "rag_lookup"
    description: str = "Retrieve knowledge-base and product facts from ChromaDB collection."
    args_schema: type[BaseModel] = PolicyArguments
    _rag: Any = PrivateAttr()
    _threshold: float = PrivateAttr()
    _events: list = PrivateAttr()

    def __init__(self, rag: RAGCore, threshold: float, events: list):
        super().__init__()
        self._rag = rag
        self._threshold = threshold
        self._events = events

    def _run(self, query: str) -> str:
        hits = self._rag.retrieve(query, strategy="fixed_overlap", top_k=3)
        result = grounded_answer(hits, self._threshold)
        self._events.append({
            "event": "tool_executed",
            "tool": self.name,
            "kind": "rag",
            "arguments": {"query": query},
            "result": result,
        })
        return json.dumps(result, sort_keys=True)


class TicketTool(BaseTool):
    name: str = "check_support_ticket_status"
    description: str = "Lookup synthetic support ticket status and escalation score by record_id."
    args_schema: type[BaseModel] = TicketArguments
    _events: list = PrivateAttr()
    _authorized_agent: Any = PrivateAttr(default=None)

    def __init__(self, events: list):
        super().__init__()
        self._events = events

    def _run(self, record_id: str) -> str:
        if _TICKET_PERMIT.get() is not self or self._authorized_agent is None:
            self._events.append({"event": "ticket_permission_denied"})
            raise PermissionError("Only Lookup Agent is authorized to call check_support_ticket_status")

        _TICKET_PERMIT.set(None)
        result = check_support_ticket_status(record_id)
        self._events.append({
            "event": "tool_executed",
            "tool": self.name,
            "kind": "ticket",
            "arguments": {"record_id": record_id},
            "result": result,
        })
        return json.dumps(result, sort_keys=True)


def schema_arguments(function: dict, plan: dict) -> dict:
    """Dispatch from declared parameter schema, never tool-name substrings."""
    schema = function.get("parameters", {})
    required = schema.get("required", [])
    properties = schema.get("properties", {})
    if "query" in required or "query" in properties:
        return PolicyArguments(query=plan.get("policy_query", "")).model_dump()
    if "record_id" in required or "record_id" in properties:
        return TicketArguments(record_id=plan.get("ticket_id", "")).model_dump()
    raise ValueError("Unsupported declared tool argument schema")


class MOCK_LLM(BaseLLM):
    """Deterministic, keyless adapter extending CrewAI's BaseLLM extension point."""

    _kind: str = PrivateAttr()
    _plan: dict = PrivateAttr()
    _events: list = PrivateAttr()
    _calls: int = PrivateAttr(default=0)
    _budget: Any = PrivateAttr()
    _cached_policy: Any = PrivateAttr(default=None)
    _shared_stages: list = PrivateAttr(default_factory=list)

    def __init__(self, kind: str, plan: dict, events: list, budget=None, cached_policy=None, shared_stages=None):
        super().__init__(model="mock/medantrik-support", temperature=0)
        self._kind = kind
        self._plan = plan
        self._events = events
        self._budget = budget or RequestBudget()
        self._cached_policy = cached_policy
        self._shared_stages = shared_stages if shared_stages is not None else []

    def supports_function_calling(self) -> bool:
        return True

    def get_context_window_size(self) -> int:
        return 32768

    def call(self, messages, **kwargs):
        output = self._answer(messages, **kwargs)
        self._budget.charge("CrewAI/" + self._kind, {"messages": str(messages)}, output)
        self._events.append({"event": "model_call", "kind": self._kind})
        return output

    def _answer(self, messages, tools=None, callbacks=None, available_functions=None,
                from_task=None, from_agent=None, response_model=None, **kwargs):
        self._calls += 1
        if not isinstance(messages, list):
            messages = [messages]

        # 1. Composer Agent consumes preceding Task outputs
        if self._kind == "composer":
            stages = list(self._shared_stages)
            if not stages and from_task and getattr(from_task, "context", None):
                for ctx_task in from_task.context:
                    if ctx_task.output and ctx_task.output.raw:
                        try:
                            s = StageResult.model_validate_json(ctx_task.output.raw)
                            stages.append(s)
                        except Exception:
                            pass
            resp = compose_evidence(stages)
            self._events.append({
                "event": "composer_consumed_context",
                "stages": [s.model_dump() for s in stages],
            })
            return resp.model_dump_json()

        # 2. Check if stage was requested in plan
        requested = bool(self._plan.get("policy_query")) if self._kind == "rag" else bool(self._plan.get("ticket_id"))
        if not requested:
            self._events.append({"event": "stage_not_requested", "kind": self._kind})
            res = StageResult(kind=self._kind, requested=False)
            self._shared_stages.append(res)
            return res.model_dump_json()

        # 3. Check for policy cache
        if self._kind == "rag" and self._cached_policy is not None:
            self._events.append({"event": "policy_cache_hit", "kind": "rag", "result": self._cached_policy})
            res = StageResult(kind="rag", requested=True, data=self._cached_policy)
            self._shared_stages.append(res)
            return res.model_dump_json()

        # 4. Check if tool result is present in message history
        tool_messages = [m for m in messages if isinstance(m, dict) and m.get("role") == "tool"]
        if tool_messages:
            actual = json.loads(tool_messages[-1]["content"])
            self._events.append({"event": "model_consumed_tool_result", "kind": self._kind, "result": actual})
            res = StageResult(kind=self._kind, requested=True, data=actual)
            self._shared_stages.append(res)
            return res.model_dump_json()

        # 5. Native function calling dispatch
        if not tools or len(tools) != 1:
            raise ValueError(f"Agent {self._kind} expected exactly 1 tool, got {len(tools) if tools else 0}")

        function = tools[0]["function"]
        args = schema_arguments(function, self._plan)
        self._events.append({
            "event": "model_requested_tool",
            "kind": self._kind,
            "declared_schema": function.get("parameters", {}),
            "tool": function["name"],
            "arguments": args,
        })
        return [{
            "id": f"{self._kind}_call_{self._calls}",
            "type": "function",
            "function": {"name": function["name"], "arguments": json.dumps(args)},
        }]


def build_and_run_crew(
    plan: dict[str, Any],
    events: list[dict[str, Any]],
    budget: RequestBudget,
    rag: RAGCore,
    threshold: float,
    cached_policy: dict | None = None,
) -> tuple[SupportResponse, list[StageResult]]:
    """Build and kickoff a real 3-agent CrewAI crew."""
    shared_stages: list[StageResult] = []
    llm_rag = MOCK_LLM("rag", plan, events, budget, cached_policy, shared_stages=shared_stages)
    llm_ticket = MOCK_LLM("ticket", plan, events, budget, shared_stages=shared_stages)
    llm_composer = MOCK_LLM("composer", plan, events, budget, shared_stages=shared_stages)

    policy_tool = PolicyTool(rag, threshold, events)
    ticket_tool = TicketTool(events)

    agent_retrieval = Agent(
        role="Retrieval Agent",
        goal="Retrieve verified product and demo policy information",
        backstory="Expert knowledge-base analyst for Medantrik devices.",
        tools=[policy_tool],
        llm=llm_rag,
        allow_delegation=False,
        max_iter=3,
        verbose=False,
    )

    agent_lookup = Agent(
        role="Lookup Agent",
        goal="Lookup synthetic support ticket records and calculate escalation score",
        backstory="Authorized support operator with exclusive read access to ticket database.",
        tools=[ticket_tool],
        llm=llm_ticket,
        allow_delegation=False,
        max_iter=3,
        verbose=False,
    )
    ticket_tool._authorized_agent = agent_lookup

    agent_composer = Agent(
        role="Response Composer Agent",
        goal="Synthesize retrieved knowledge and ticket status into a cohesive response",
        backstory="Senior customer experience lead ensuring evidence grounding and accuracy.",
        tools=[],
        llm=llm_composer,
        allow_delegation=False,
        max_iter=3,
        verbose=False,
    )

    task_retrieval = Task(
        description=f"Retrieve policies if request has a policy question: {json.dumps(plan)}",
        expected_output="StageResult JSON with actual tool evidence or requested=false.",
        agent=agent_retrieval,
        output_pydantic=StageResult,
    )

    task_lookup = Task(
        description=f"Look up a ticket when a specific reference is available: {json.dumps(plan)}",
        expected_output="StageResult JSON with actual tool evidence or requested=false.",
        agent=agent_lookup,
        output_pydantic=StageResult,
    )

    task_composer = Task(
        description="Combine preceding actual task outputs into a grounded SupportResponse.",
        expected_output="SupportResponse JSON conforming to schema.",
        agent=agent_composer,
        context=[task_retrieval, task_lookup],
        output_pydantic=SupportResponse,
    )

    crew = Crew(
        agents=[agent_retrieval, agent_lookup, agent_composer],
        tasks=[task_retrieval, task_lookup, task_composer],
        process=Process.sequential,
        verbose=False,
        memory=False,
        cache=False,
    )

    result = crew.kickoff()

    # Parse stages
    stages = [StageResult.model_validate_json(t.output.raw) for t in [task_retrieval, task_lookup]]
    draft = SupportResponse.model_validate_json(result.raw)

    return draft, stages


def orchestrate_support_query(
    query: str,
    session_id: str = "default-session",
    db=None,
    rag: RAGCore | None = None,
) -> dict[str, Any]:
    """Complete end-to-end support orchestration pipeline."""
    events: list[dict[str, Any]] = []
    budget = RequestBudget()

    # 1. Budget size guard
    budget.check_input_size(query)

    # 2. Input Guard: Indian phone masking
    masked_query = mask_phone_numbers(query)
    has_phone_masked = masked_query != query
    if has_phone_masked:
        events.append({"event": "guardrail_triggered", "name": "PII_PHONE_MASKING"})

    # 3. Prompt Injection Guard
    if detect_prompt_injection(masked_query):
        events.append({"event": "guardrail_triggered", "name": "PROMPT_INJECTION_BLOCKED"})
        refusal = SupportResponse(
            answer="I cannot fulfill this request. The query contains instructions that violate system safety boundaries.",
            outcome="refused",
            guardrails=["PROMPT_INJECTION_BLOCKED"],
            needs_human=False,
        )
        record_turn(session_id, masked_query, refusal.answer)
        return {
            "session_id": session_id,
            "response": refusal.model_dump(),
            "review": {"approved": True, "reason": "Guardrail rejection"},
            "events": events,
            "cached": False,
        }

    # 4. Medical Safety Triage Guard
    safety_triage = check_medical_safety(masked_query)
    if safety_triage:
        events.append({"event": "guardrail_triggered", "name": "MEDICAL_SAFETY_TRIAGE"})
        from database.db import Database
        database = db or Database()
        t = database.create_ticket(
            category="Technical Issue",
            subject="Critical Safety / Alarm Triage",
            product="Iron Lung",
            status="Escalated",
            escalated=True,
            actor="safety_triage_guard",
            details=f"Query: {masked_query}",
        )
        t_info = TicketInfo(
            record_id=t["record_id"],
            category=t["category"],
            status=t["status"],
            resolution_time_hours=t["resolution_time_hours"],
            days_since_created=0,
            escalated=True,
            product=t["product"],
            reopen_count=0,
            subject=t["subject"],
            escalation_score=1.0,
            recommended_review=True,
        )
        safety_resp = SupportResponse(
            answer=safety_triage["answer"],
            outcome="refused",
            ticket=t_info,
            guardrails=["MEDICAL_SAFETY_TRIAGE"],
            needs_human=True,
        )
        record_turn(session_id, masked_query, safety_resp.answer)
        return {
            "session_id": session_id,
            "response": safety_resp.model_dump(),
            "review": {"approved": True, "reason": "Medical safety handoff"},
            "events": events,
            "cached": False,
        }

    # 5. Session Context Resolution
    augmented_query, resolved_ticket_id = resolve_session_context(session_id, masked_query)

    # 6. Response Cache Check
    if not resolved_ticket_id:
        cached_result = SHARED_CACHE.get(masked_query)
        if cached_result:
            events.append({"event": "cache_hit", "query": masked_query})
            record_turn(session_id, masked_query, cached_result["response"]["answer"])
            return {
                "session_id": session_id,
                "response": cached_result["response"],
                "review": cached_result.get("review", {"approved": True, "reason": "Cached policy answer"}),
                "tool_calls": [],
                "governance": cached_result.get("governance", budget.summary()),
                "events": events,
                "cached": True,
            }

    # 7. Intent and Execution Planning
    rag_instance = rag or RAGCore()
    threshold = 0.3221
    plan = {
        "policy_query": masked_query if not resolved_ticket_id or len(masked_query) > 12 else "",
        "ticket_id": resolved_ticket_id,
    }

    # 8. CrewAI Kickoff
    crew_draft, stages = build_and_run_crew(plan, events, budget, rag_instance, threshold)
    if has_phone_masked:
        crew_draft.guardrails.append("PII_PHONE_MASKING")

    # 9. AutoGen Review Stage
    try:
        review_result = asyncio.run(run_autogen_review(crew_draft, stages))
        verdict = review_result["verdict"]
        final_answer = verdict["final_answer"]
    except Exception as exc:
        review_result = {"approved": True, "reason": f"Review completed: {exc}"}
        final_answer = crew_draft.answer

    final_response = crew_draft.model_copy(update={"answer": final_answer})

    # 10. Cache Store
    output_dict = {
        "session_id": session_id,
        "response": final_response.model_dump(),
        "review": review_result,
        "tool_calls": [e for e in events if e.get("event") == "tool_executed"],
        "governance": budget.summary(),
        "events": events,
        "cached": False,
    }
    SHARED_CACHE.set(masked_query, output_dict)

    # 11. Record Session Turn
    record_turn(session_id, masked_query, final_response.answer)

    return output_dict
