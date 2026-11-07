"""AI Governance: Least Autonomy Principle, Risk Classification, and Cost/Token Budget (Task 15)."""
from __future__ import annotations
import json
from typing import Any

RISK_CLASSIFICATION = {
    "level": "HIGH",
    "domain": "Medical Device & Care Equipment Support",
    "justification": (
        "Classified as HIGH RISK under AI governance frameworks because the system operates in a healthcare-adjacent "
        "medical technology domain (respiratory monitoring and life-support devices: OxySense, NODex, Iron Lung). "
        "Misleading answers, incorrect calibration instructions, or failure to escalate alarms could jeopardize patient "
        "safety. Consequently, strict medical-safety triage overrides automated generation, diagnostic statements are "
        "categorically prohibited, and ticket lookup permissions are restricted under the principle of least autonomy."
    ),
}

MAX_TOKENS_PER_REQUEST = 50000
MAX_COST_PER_REQUEST = 0.10  # $0.10 simulated cost cap


class BudgetExceededError(Exception):
    """Raised when a request exceeds simulated token or cost budget."""


def estimate_tokens(text_or_obj: Any) -> int:
    """Deterministic token estimation: ~4 chars per token."""
    if isinstance(text_or_obj, str):
        return max(1, len(text_or_obj) // 4)
    if isinstance(text_or_obj, (dict, list)):
        dumped = json.dumps(text_or_obj)
        return max(1, len(dumped) // 4)
    return 1


class RequestBudget:
    def __init__(
        self,
        max_tokens: int = MAX_TOKENS_PER_REQUEST,
        max_cost: float = MAX_COST_PER_REQUEST,
    ):
        self.max_tokens = max_tokens
        self.max_cost = max_cost
        self.total_prompt_tokens = 0
        self.total_completion_tokens = 0
        self.calls: list[dict[str, Any]] = []

    def check_input_size(self, input_text: str) -> None:
        """Reject oversized input that would exceed budget."""
        tokens = estimate_tokens(input_text)
        if tokens > self.max_tokens:
            raise BudgetExceededError(
                f"Input size of {tokens} tokens exceeds the per-request governance cap of {self.max_tokens} tokens."
            )

    def charge(self, caller: str, prompt: Any, completion: Any) -> dict[str, Any]:
        p_tok = estimate_tokens(prompt)
        c_tok = estimate_tokens(completion)

        if (self.total_prompt_tokens + self.total_completion_tokens + p_tok + c_tok) > self.max_tokens:
            raise BudgetExceededError(
                f"Request token accumulation exceeds budget limit of {self.max_tokens} tokens."
            )

        self.total_prompt_tokens += p_tok
        self.total_completion_tokens += c_tok

        # Simulated pricing: $0.002 / 1k prompt, $0.006 / 1k completion
        cost = (p_tok / 1000.0) * 0.002 + (c_tok / 1000.0) * 0.006

        call_record = {
            "caller": caller,
            "prompt_tokens": p_tok,
            "completion_tokens": c_tok,
            "cost_usd": round(cost, 6),
        }
        self.calls.append(call_record)
        return call_record

    def summary(self) -> dict[str, Any]:
        total_tokens = self.total_prompt_tokens + self.total_completion_tokens
        total_cost = sum(c["cost_usd"] for c in self.calls)
        return {
            "total_prompt_tokens": self.total_prompt_tokens,
            "total_completion_tokens": self.total_completion_tokens,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "max_tokens_allowed": self.max_tokens,
            "max_cost_allowed": self.max_cost,
            "call_count": len(self.calls),
            "budget_exceeded": False,
        }
