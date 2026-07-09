"""
Ops Recovery Agent — detects provider degradation and recommends fallbacks.
"""

import logging
from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class OpsRecoveryAgent(BaseAgent):
    agent_name = "ops_recovery_agent"
    agent_description = "Detects provider degradation and recommends recovery actions"

    def validate_input(self, agent_input: AgentInput) -> bool:
        return "health_status" in agent_input.context

    async def invoke(self, agent_input: AgentInput) -> AgentOutput:
        health: Dict[str, Any] = agent_input.context["health_status"]
        actions: List[Dict[str, str]] = []

        for provider, status in health.items():
            if status in ("degraded", "down", "unavailable"):
                fallback = self._fallback_for(provider)
                actions.append({
                    "provider": provider,
                    "action": "failover",
                    "fallback": fallback,
                    "reason": f"{provider} is {status}",
                })

        if not actions:
            return AgentOutput(
                decision={"status": "healthy", "actions": []},
                reasoning="All providers healthy",
                confidence_score=0.95,
            )

        return AgentOutput(
            decision={"status": "degraded", "actions": actions},
            reasoning=f"Detected {len(actions)} provider issue(s)",
            confidence_score=0.9,
            metadata={"actions": actions},
        )

    def _fallback_for(self, provider: str) -> str:
        fallbacks = {
            "searxng": "duckduckgo",
            "opensearch": "database",
            "minio": "local",
            "openai": "rule_based_fallback",
        }
        return fallbacks.get(provider, "skip")

    def parse_output(self, raw_output: Any) -> AgentOutput:
        if isinstance(raw_output, AgentOutput):
            return raw_output
        return AgentOutput(decision=raw_output, reasoning="", confidence_score=0.5)
