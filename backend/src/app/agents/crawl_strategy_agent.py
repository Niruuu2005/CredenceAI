"""
Crawl Strategy Agent — chooses the cheapest safe crawl strategy per URL.
"""

import logging
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)

STRATEGIES = ("skip", "metadata_only", "scrapy", "playwright", "common_crawl", "internet_archive")


class CrawlStrategyOutput(BaseModel):
    url: str
    strategy: str
    reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0)


class CrawlStrategyAgent(BaseAgent):
    agent_name = "crawl_strategy_agent"
    agent_description = "Selects optimal crawl strategy per URL"

    def validate_input(self, agent_input: AgentInput) -> bool:
        if "urls" not in agent_input.context:
            raise ValueError("Missing required field: urls")
        return True

    async def invoke(self, agent_input: AgentInput) -> AgentOutput:
        urls: List[str] = agent_input.context["urls"]
        trust_scores: Dict[str, float] = agent_input.context.get("trust_scores", {})
        strategies = []
        for url in urls:
            score = trust_scores.get(url, 0.5)
            if score < 0.4:
                strategy = "skip"
                reason = "Low trust score — skip crawl"
            elif score < 0.6:
                strategy = "metadata_only"
                reason = "Borderline trust — metadata only"
            elif any(d in url for d in ("arxiv.org", "wikipedia.org", "wikidata.org")):
                strategy = "metadata_only"
                reason = "Structured source — metadata sufficient"
            elif score >= 0.85:
                strategy = "playwright"
                reason = "High trust — full render crawl"
            else:
                strategy = "scrapy"
                reason = "Standard HTTP crawl"
            strategies.append({"url": url, "strategy": strategy, "reason": reason})

        return AgentOutput(
            decision=strategies,
            reasoning=f"Evaluated {len(urls)} URLs for crawl strategy",
            confidence_score=0.85,
            metadata={"strategies": strategies},
        )

    def parse_output(self, raw_output: Any) -> AgentOutput:
        if isinstance(raw_output, AgentOutput):
            return raw_output
        return AgentOutput(decision=raw_output, reasoning="", confidence_score=0.5)
