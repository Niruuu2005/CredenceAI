"""
Source Selection Agent for CredenceAI Iteration 0.4 (Sprint 54)

Selects the optimal set of sources for a given research query based on:
- Vertical context (company, research, news, rag)
- Source reliability metadata
- Query characteristics (entity type, freshness requirement, domain)
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


# Source reliability metadata
SOURCE_REGISTRY = {
    # Scholarly
    "openalex": {"vertical": "research", "reliability": 0.95, "type": "academic"},
    "crossref": {"vertical": "research", "reliability": 0.93, "type": "academic"},
    "arxiv": {"vertical": "research", "reliability": 0.90, "type": "preprint"},
    "semantic_scholar": {"vertical": "research", "reliability": 0.88, "type": "academic"},
    # News
    "gdelt": {"vertical": "news", "reliability": 0.80, "type": "news_aggregator"},
    "newsapi": {"vertical": "news", "reliability": 0.82, "type": "news_api"},
    "searxng_news": {"vertical": "news", "reliability": 0.75, "type": "meta_search"},
    # Company/Entity
    "wikidata": {"vertical": "company", "reliability": 0.92, "type": "knowledge_graph"},
    "wikipedia": {"vertical": "company", "reliability": 0.85, "type": "encyclopedia"},
    "crunchbase": {"vertical": "company", "reliability": 0.87, "type": "business_data"},
    # General
    "searxng": {"vertical": "general", "reliability": 0.70, "type": "meta_search"},
    "common_crawl": {"vertical": "general", "reliability": 0.65, "type": "web_archive"},
}

VERTICAL_PRIMARY_SOURCES = {
    "research": ["openalex", "crossref", "arxiv", "semantic_scholar"],
    "news": ["gdelt", "newsapi", "searxng_news"],
    "company": ["wikidata", "wikipedia", "crunchbase"],
    "rag": ["openalex", "common_crawl", "searxng"],
    "general": ["searxng", "wikipedia", "wikidata"],
}


class SourceSelectionInput(BaseModel):
    """Input schema for source selection."""
    query: str
    vertical: str = "general"
    entities: List[str] = Field(default_factory=list)
    max_sources: int = 5
    min_reliability: float = 0.70


class SourceSelectionOutput(BaseModel):
    """Output schema for source selection."""
    selected_sources: List[str]
    source_metadata: Dict[str, Any]
    reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0)


class SourceSelectionAgent(BaseAgent):
    """
    Agent that selects optimal data sources for a research query.
    Uses vertical context and reliability metadata to rank sources.
    """

    agent_name = "source_selection_agent"
    agent_description = "Selects the optimal set of sources for a given research query"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config=config or {})
        self.source_registry = SOURCE_REGISTRY
        self.vertical_sources = VERTICAL_PRIMARY_SOURCES

    def validate_input(self, agent_input: AgentInput) -> bool:
        if "query" not in agent_input.context:
            raise ValueError("Missing required field: query")
        if not agent_input.context["query"]:
            raise ValueError("query must be non-empty")
        return True

    async def invoke(self, agent_input: AgentInput) -> AgentOutput:
        query = agent_input.context["query"]
        vertical = agent_input.context.get("vertical", "general")
        entities = agent_input.context.get("entities", [])
        max_sources = agent_input.context.get("max_sources", 5)
        min_reliability = agent_input.context.get("min_reliability", 0.70)

        selected = self._select_sources(vertical, min_reliability, max_sources)
        metadata = {s: self.source_registry.get(s, {}) for s in selected}
        avg_reliability = (
            sum(self.source_registry.get(s, {}).get("reliability", 0) for s in selected) / len(selected)
            if selected else 0.0
        )

        reasoning = (
            f"Selected {len(selected)} sources for '{vertical}' vertical. "
            f"Average reliability: {avg_reliability:.2f}. "
            f"Query: '{query[:80]}'. Entities: {entities[:3]}."
        )

        output = SourceSelectionOutput(
            selected_sources=selected,
            source_metadata=metadata,
            reasoning=reasoning,
            confidence_score=round(min(avg_reliability, 1.0), 4),
        )

        return AgentOutput(
            decision=output.model_dump(),
            reasoning=reasoning,
            confidence_score=output.confidence_score,
            metadata={"vertical": vertical, "num_sources": len(selected)},
        )

    def parse_output(self, raw_output: Any) -> AgentOutput:
        if isinstance(raw_output, AgentOutput):
            return raw_output
        return AgentOutput(
            decision=str(raw_output),
            reasoning="Parsed from raw output",
            confidence_score=0.5,
        )

    def _select_sources(self, vertical: str, min_reliability: float, max_sources: int) -> List[str]:
        """Select sources by vertical, filtered by min reliability, sorted by reliability."""
        candidates = self.vertical_sources.get(vertical, self.vertical_sources["general"])
        filtered = [
            s for s in candidates
            if self.source_registry.get(s, {}).get("reliability", 0) >= min_reliability
        ]
        # Sort by reliability descending
        filtered.sort(
            key=lambda s: self.source_registry.get(s, {}).get("reliability", 0),
            reverse=True,
        )
        return filtered[:max_sources]

    def get_source_reliability(self, source_name: str) -> float:
        """Return reliability score for a source (0.0 if unknown)."""
        return self.source_registry.get(source_name, {}).get("reliability", 0.0)

    def list_sources_for_vertical(self, vertical: str) -> List[str]:
        """Return all sources for a given vertical."""
        return self.vertical_sources.get(vertical, [])
