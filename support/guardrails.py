"""Input and output guardrails: Indian phone masking, injection defense, medical safety, and grounding (Task 10)."""
from __future__ import annotations
import re
from typing import Any

from support.models import Citation, StageResult, SupportResponse, TicketInfo

# Indian mobile numbers: 10 digits starting with 6, 7, 8, or 9; optional +91 or 0 prefix, optional spaces or hyphens
INDIAN_PHONE_REGEX = re.compile(
    r"(?:\+91[\s-]?)?(?:0)?([6-9]\d{4}[\s-]?\d{5}|[6-9]\d{9})\b"
)

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"system\s+prompt",
    r"disregard\s+(all\s+)?prior",
    r"you\s+are\s+now\s+(an?\s+)?unrestricted",
    r"dan\s+mode",
    r"bypass\s+security",
    r"jailbreak",
    r"developer\s+mode",
]
INJECTION_REGEX = re.compile("|".join(INJECTION_PATTERNS), re.IGNORECASE)

MEDICAL_SAFETY_PATTERNS = [
    r"\b(can'?t|cannot)\s+breathe\b",
    r"\bchest\s+pain\b",
    r"\boxygen\s+alarm\b",
    r"\blife\s+support\b",
    r"\bstop(ped)?\s+breathing\b",
    r"\bturn\s+off\s+(the\s+)?alarm\b",
    r"\bdisable\s+(the\s+)?alarm\b",
    r"\bchange\s+(the\s+)?oxygen\s+(flow|concentration|level|setting)\b",
    r"\bmodify\s+(the\s+)?(device\s+)?settings\b",
    r"\bpatient\s+(is\s+)?(collapsing|unconscious|turning\s+blue|cyanosis)\b",
    r"\b(unconscious|cyanosis)\b",
    r"\bmedical\s+emergency\b",
    r"\bprescribe\b",
    r"\bdosage\b",
]
MEDICAL_SAFETY_REGEX = re.compile("|".join(MEDICAL_SAFETY_PATTERNS), re.IGNORECASE)


def mask_phone_numbers(text: str) -> str:
    """Mask Indian phone numbers before memory, logs, tools, or model ingestion."""
    return INDIAN_PHONE_REGEX.sub("[PHONE_MASKED]", text)


def detect_prompt_injection(text: str) -> bool:
    """Detect common prompt-injection and jailbreak vectors."""
    return bool(INJECTION_REGEX.search(text))


def check_medical_safety(text: str) -> dict[str, Any] | None:
    """Detect safety-critical or clinical advice requests and produce a safe triage handoff."""
    if MEDICAL_SAFETY_REGEX.search(text):
        return {
            "is_critical": True,
            "outcome": "refused",
            "answer": (
                "SAFETY HANDOFF: This query involves an urgent medical or medical-device safety situation. "
                "Medantrik Assist is a customer support prototype and does not provide clinical diagnoses, "
                "treatment decisions, or instructions to modify device parameters or disable alarms. "
                "Please seek immediate medical attention from local emergency/clinical personnel and contact "
                "a qualified biomedical equipment specialist. A critical review ticket has been initiated for qualified human follow-up."
            ),
            "guardrail_triggered": "MEDICAL_SAFETY_TRIAGE",
            "needs_human": True,
        }
    return None


def compose_evidence(stages: list[StageResult]) -> SupportResponse:
    """Combine RAG and ticket stage outputs into a structured SupportResponse."""
    answer_parts = []
    citations: list[Citation] = []
    ticket_info: TicketInfo | None = None
    outcome = "not_found"
    guardrails: list[str] = []
    needs_human = False

    for stage in stages:
        if stage.kind == "guard":
            guardrails.append(stage.data.get("guardrail", "GUARDRAIL_TRIGGERED"))
            if stage.data.get("refused"):
                return SupportResponse(
                    answer=stage.data.get("reason", "Request refused by guardrail policy."),
                    outcome="refused",
                    guardrails=guardrails,
                    needs_human=stage.data.get("needs_human", False),
                )

        elif stage.kind == "triage":
            guardrails.append("MEDICAL_SAFETY_TRIAGE")
            return SupportResponse(
                answer=stage.data["answer"],
                outcome="refused",
                guardrails=guardrails,
                needs_human=True,
            )

        elif stage.kind == "ticket":
            if not stage.requested:
                continue
            t_data = stage.data
            if t_data.get("found"):
                ticket_info = TicketInfo.model_validate(t_data["ticket"])
                answer_parts.append(t_data.get("summary", f"Ticket {ticket_info.record_id} is {ticket_info.status}."))
                outcome = "answered"
                if ticket_info.recommended_review:
                    needs_human = True
            else:
                answer_parts.append(t_data.get("error", "Ticket was not found."))
                outcome = "not_found"

        elif stage.kind == "rag":
            if not stage.requested:
                continue
            rag_data = stage.data
            if rag_data.get("outcome") == "answered":
                answer_parts.append(rag_data["answer"])
                outcome = "answered"
                for c in rag_data.get("citations", []):
                    citations.append(Citation.model_validate(c))
            else:
                if not answer_parts:
                    answer_parts.append(rag_data.get("answer", "I don't know based on the available verified information."))
                    outcome = "not_found"

    final_answer = "\n\n".join(answer_parts).strip() if answer_parts else "No relevant information could be retrieved."

    return SupportResponse(
        answer=final_answer,
        outcome=outcome,  # type: ignore
        citations=citations,
        ticket=ticket_info,
        guardrails=guardrails,
        needs_human=needs_human,
    )


def guard_output(
    draft: SupportResponse,
    stages: list[StageResult],
    original_context: list[str],
) -> SupportResponse:
    """Verify draft against stage evidence. Enforce groundedness fallback if ungrounded claims are detected."""
    expected = compose_evidence(stages)
    # If the draft contains hallucinated or ungrounded claims not in expected answer:
    if draft.answer != expected.answer:
        # Check if draft answer is grounded in allowed text
        allowed_text = " ".join([str(s.data) for s in stages])
        # Simple grounding check: if draft answer contains substantial words not in allowed text
        draft_words = set(re.findall(r"\b\w{5,}\b", draft.answer.lower()))
        allowed_words = set(re.findall(r"\b\w{5,}\b", allowed_text.lower()))
        unsupported = draft_words - allowed_words
        if len(unsupported) > 3:
            # Revert to expected evidence-only answer
            expected.guardrails.append("OUTPUT_GROUNDING_CORRECTION")
            return expected

    return draft
