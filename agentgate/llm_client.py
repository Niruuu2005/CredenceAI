"""Optional OpenRouter LLM enhancement with rules fallback."""

from __future__ import annotations

import json
import logging
from typing import Any

import httpx

from config import LLM_ENABLED, LLM_TIMEOUT_SEC, OPENROUTER_API_KEY, OPENROUTER_MODEL
from models import CompareOptionsRequest, CompareOptionsResponse, EvaluateTaskRequest, EvaluateTaskResponse
from rules_engine import compare_options_rules, evaluate_task_rules

logger = logging.getLogger(__name__)

EVALUATE_SCHEMA = {
    "type": "object",
    "properties": {
        "status": {"type": "string", "enum": ["ready", "needs_clarification", "unsafe", "incomplete"]},
        "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
        "missing_info": {"type": "array", "items": {"type": "string"}},
        "recommended_next_action": {"type": "string"},
        "reasoning_summary": {"type": "string"},
        "confidence": {"type": "number"},
        "agent_instruction": {"type": "string"},
    },
    "required": [
        "status", "risk_level", "missing_info", "recommended_next_action",
        "reasoning_summary", "confidence", "agent_instruction",
    ],
    "additionalProperties": False,
}

COMPARE_SCHEMA = {
    "type": "object",
    "properties": {
        "recommended_option_id": {"type": "string"},
        "ranking": {"type": "array", "items": {"type": "string"}},
        "risk_level": {"type": "string", "enum": ["low", "medium", "high"]},
        "reasoning_summary": {"type": "string"},
        "confidence": {"type": "number"},
        "agent_instruction": {"type": "string"},
    },
    "required": [
        "recommended_option_id", "ranking", "risk_level",
        "reasoning_summary", "confidence", "agent_instruction",
    ],
    "additionalProperties": False,
}


async def _openrouter_json(prompt: str, schema: dict, schema_name: str) -> dict[str, Any] | None:
    if not LLM_ENABLED or not OPENROUTER_API_KEY:
        return None

    payload = {
        "model": OPENROUTER_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are AgentGate, a pre-action safety evaluator for autonomous agents. "
                    "Respond only with JSON matching the schema."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "response_format": {
            "type": "json_schema",
            "json_schema": {"name": schema_name, "strict": True, "schema": schema},
        },
        "temperature": 0.2,
    }

    try:
        async with httpx.AsyncClient(timeout=LLM_TIMEOUT_SEC) as client:
            res = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/Niruuu2005/CredenceAI",
                    "X-Title": "AgentGate",
                },
                json=payload,
            )
            if res.status_code != 200:
                logger.warning("OpenRouter error %s: %s", res.status_code, res.text[:200])
                return None
            data = res.json()
            content = data["choices"][0]["message"]["content"]
            return json.loads(content)
    except Exception as exc:
        logger.warning("LLM enhancement failed: %s", exc)
        return None


async def evaluate_task(req: EvaluateTaskRequest) -> EvaluateTaskResponse:
    rules_result = evaluate_task_rules(req)

    # Use LLM only for ambiguous low-confidence cases
    if rules_result.confidence >= 0.9 or rules_result.status == "unsafe":
        return rules_result

    prompt = (
        f"Evaluate this agent task:\n"
        f"task_description: {req.task_description}\n"
        f"goal: {req.goal}\n"
        f"proposed_action: {req.proposed_action}\n"
        f"context: {json.dumps(req.available_context)}\n"
        f"constraints: {req.constraints}\n"
        f"Rules engine said: {rules_result.model_dump()}"
    )
    llm_data = await _openrouter_json(prompt, EVALUATE_SCHEMA, "evaluate_task")
    if llm_data:
        try:
            return EvaluateTaskResponse(**llm_data)
        except Exception:
            pass
    return rules_result


async def compare_options(req: CompareOptionsRequest) -> CompareOptionsResponse:
    rules_result = compare_options_rules(req)

    prompt = (
        f"Compare options for: {req.decision_goal}\n"
        f"options: {json.dumps([o.model_dump() for o in req.options])}\n"
        f"context: {json.dumps(req.context)}\n"
        f"Rules ranking: {rules_result.ranking}"
    )
    llm_data = await _openrouter_json(prompt, COMPARE_SCHEMA, "compare_options")
    if llm_data:
        try:
            return CompareOptionsResponse(**llm_data)
        except Exception:
            pass
    return rules_result
