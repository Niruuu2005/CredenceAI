"""Deterministic pre-action decision logic — always returns valid JSON."""

from __future__ import annotations

import re
from typing import Any

from models import (
    CompareOptionsRequest,
    CompareOptionsResponse,
    EvaluateTaskRequest,
    EvaluateTaskResponse,
    RiskLevel,
    StatusType,
)

# Patterns that indicate unsafe operations
UNSAFE_PATTERNS = [
    r"\brm\s+-rf\b",
    r"\bdelete\s+(all|production|entire)\b",
    r"\bdrop\s+(database|table|schema)\b",
    r"\btruncate\b",
    r"\bwipe\s+(disk|drive|data)\b",
    r"\bdisable\s+(auth|authentication|security|firewall)\b",
    r"\bexfiltrat",
    r"\bleak\s+(secret|password|credential|api.?key)\b",
    r"\bsend\s+(mass|bulk)\s+email",
    r"\bwire\s+transfer\b",
    r"\btransfer\s+\$?\d{4,}",
]

HIGH_RISK_ACTIONS = {
    "stripe.transfer",
    "payment.send",
    "db.drop",
    "fs.delete_recursive",
    "auth.disable",
    "email.bulk_send",
}

CLARIFICATION_FIELDS = [
    "user_confirmed",
    "recipient_verified",
    "backup_exists",
    "dates_provided",
    "destination_confirmed",
    "amount_confirmed",
    "human_approved",
]

INCOMPLETE_TASK_HINTS = [
    (r"\bbook\s+(a\s+)?flight\b", ["dates_provided", "destination_confirmed"]),
    (r"\bschedule\s+meeting\b", ["dates_provided", "attendees_confirmed"]),
    (r"\bpay\s+(invoice|bill|vendor)\b", ["user_confirmed", "amount_confirmed", "recipient_verified"]),
    (r"\btransfer\b", ["user_confirmed", "recipient_verified"]),
]


def _text_blob(req: EvaluateTaskRequest) -> str:
    parts = [req.task_description, req.goal or "", req.proposed_action or ""]
    return " ".join(parts).lower()


def _is_unsafe(blob: str, proposed_action: str | None) -> bool:
    if proposed_action and proposed_action.lower() in HIGH_RISK_ACTIONS:
        return True
    return any(re.search(p, blob, re.I) for p in UNSAFE_PATTERNS)


def _missing_from_context(
    blob: str, context: dict[str, Any], constraints: list[str]
) -> list[str]:
    missing: list[str] = []

    for field in CLARIFICATION_FIELDS:
        if field in context and context[field] is False:
            missing.append(field)

    for pattern, fields in INCOMPLETE_TASK_HINTS:
        if re.search(pattern, blob, re.I):
            for f in fields:
                if f not in context or context[f] in (False, None, ""):
                    if f not in missing:
                        missing.append(f)

    if "no_irreversible_without_confirmation" in constraints:
        if not context.get("user_confirmed"):
            if "user_confirmed" not in missing:
                missing.append("user_confirmed")

    if "require_human_approval" in constraints and not context.get("human_approved"):
        if "human_approved" not in missing:
            missing.append("human_approved")

    return missing


def _risk_level(blob: str, proposed_action: str | None, missing: list[str]) -> RiskLevel:
    if _is_unsafe(blob, proposed_action):
        return "high"
    if any(k in blob for k in ("payment", "transfer", "delete", "production", "password")):
        return "high" if missing else "medium"
    if missing:
        return "medium"
    return "low"


def evaluate_task_rules(req: EvaluateTaskRequest) -> EvaluateTaskResponse:
    blob = _text_blob(req)
    missing = _missing_from_context(blob, req.available_context, req.constraints)
    risk = _risk_level(blob, req.proposed_action, missing)

    if _is_unsafe(blob, req.proposed_action):
        action = req.proposed_action or "proposed action"
        return EvaluateTaskResponse(
            status="unsafe",
            risk_level="high",
            missing_info=missing or ["user_confirmed", "backup_exists"],
            recommended_next_action="stop_and_request_human_approval",
            reasoning_summary=(
                f"Task or action '{action}' matches destructive, financial, "
                "or security-sensitive patterns without sufficient safeguards."
            ),
            confidence=0.95,
            agent_instruction=(
                f"Do not execute {action}. Request explicit human approval "
                "and verify all safety checks before retrying /evaluate-task."
            ),
        )

    if not req.task_description.strip() or len(req.task_description.strip()) < 3:
        return EvaluateTaskResponse(
            status="incomplete",
            risk_level="low",
            missing_info=["task_description"],
            recommended_next_action="clarify_task_with_user",
            reasoning_summary="Task description is empty or too short to evaluate.",
            confidence=0.99,
            agent_instruction="Ask the user for a clear, specific task description.",
        )

    if missing:
        return EvaluateTaskResponse(
            status="needs_clarification",
            risk_level=risk,
            missing_info=missing,
            recommended_next_action="ask_user_for_missing_fields",
            reasoning_summary=(
                f"Task requires additional context before safe execution: {', '.join(missing)}."
            ),
            confidence=0.88 if risk == "high" else 0.82,
            agent_instruction=(
                f"Do not execute yet. Ask the user to provide: {', '.join(missing)}. "
                "Then call /evaluate-task again with updated available_context."
            ),
        )

    return EvaluateTaskResponse(
        status="ready",
        risk_level=risk,
        missing_info=[],
        recommended_next_action="proceed_with_proposed_action",
        reasoning_summary="Task has sufficient context and no blocking safety signals detected.",
        confidence=0.85 if risk == "low" else 0.72,
        agent_instruction=(
            f"Proceed with {req.proposed_action or 'the planned action'} "
            "if it aligns with the user's goal."
        ),
    )


RISK_ORDER = {"low": 0, "medium": 1, "high": 2}


def compare_options_rules(req: CompareOptionsRequest) -> CompareOptionsResponse:
    ctx = req.context

    def score_option(opt) -> tuple[int, int, str]:
        risk_score = RISK_ORDER.get(opt.estimated_risk, 1)
        gathers_info = 0
        label_lower = opt.label.lower()
        action_lower = (opt.action or "").lower()

        if any(k in label_lower or k in action_lower for k in ("ask", "clarif", "confirm", "verify")):
            gathers_info = -1

        if ctx.get("needs_citations") and "verify" in action_lower:
            gathers_info -= 1
        if ctx.get("user_provided_city") is False and "ask" in action_lower:
            gathers_info -= 1
        if ctx.get("ambiguous_location") and "ask" in action_lower:
            gathers_info -= 1

        return (risk_score, gathers_info, opt.id)

    ranked = sorted(req.options, key=score_option)
    ranking_ids = [o.id for o in ranked]
    best = ranked[0]
    worst_risk = max(RISK_ORDER.get(o.estimated_risk, 1) for o in req.options)
    best_risk: RiskLevel = best.estimated_risk

    reasoning = (
        f"Selected '{best.label}' for goal '{req.decision_goal}' "
        f"based on lowest estimated risk and information-gathering value."
    )
    if ctx.get("needs_citations"):
        reasoning = (
            "Citations are required; prefer the option that verifies sources before acting."
        )
    if ctx.get("user_provided_city") is False:
        reasoning = (
            "Location is ambiguous; prefer asking the user before fetching external data."
        )

    return CompareOptionsResponse(
        recommended_option_id=best.id,
        ranking=ranking_ids,
        risk_level=best_risk if worst_risk <= 1 else "medium",
        reasoning_summary=reasoning,
        confidence=0.84 if len(req.options) == 2 else 0.78,
        agent_instruction=f"Execute option {best.id}: {best.label}.",
    )
