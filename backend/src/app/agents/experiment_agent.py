"""
Experiment Agent — recommends metrics and stopping criteria for A/B tests.
"""

import logging
from typing import Any, Dict, Optional

from app.agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


class ExperimentAgent(BaseAgent):
    agent_name = "experiment_agent"
    agent_description = "Recommends experiment metrics and stopping criteria"

    def validate_input(self, agent_input: AgentInput) -> bool:
        return "experiment_type" in agent_input.context or "query" in agent_input.context

    async def invoke(self, agent_input: AgentInput) -> AgentOutput:
        exp_type = agent_input.context.get("experiment_type", "search_quality")
        query = agent_input.context.get("query", "")

        recommendations: Dict[str, Any] = {
            "metrics": ["relevance_score", "citation_count", "trust_score", "latency_ms"],
            "stop_criteria": {
                "min_samples": 50,
                "confidence_threshold": 0.95,
                "max_duration_hours": 72,
            },
            "variants": ["control", "agent_enhanced"],
        }

        if exp_type == "source_selection":
            recommendations["metrics"].append("source_diversity")
        if query:
            recommendations["query"] = query

        return AgentOutput(
            decision=recommendations,
            reasoning=f"Experiment plan for {exp_type}",
            confidence_score=0.8,
        )

    def parse_output(self, raw_output: Any) -> AgentOutput:
        if isinstance(raw_output, AgentOutput):
            return raw_output
        return AgentOutput(decision=raw_output, reasoning="", confidence_score=0.5)
