"""
Entity Resolution Agent for CredenceAI Iteration 0.4 (Sprint 55)

Resolves ambiguous entity mentions to canonical identifiers using:
- Wikidata QID matching
- Wikipedia article disambiguation
- Alias/alternate-name normalisation
- Confidence-weighted disambiguation
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentInput, AgentOutput

logger = logging.getLogger(__name__)


# Compact disambiguation knowledge base for testing (expanded by live Wikidata in prod)
ENTITY_KB: Dict[str, Dict[str, Any]] = {
    "openai": {
        "canonical": "OpenAI",
        "type": "organization",
        "wikidata_qid": "Q28909344",
        "aliases": ["open ai", "openai inc", "openai lp"],
        "description": "American AI research laboratory",
    },
    "perplexity": {
        "canonical": "Perplexity AI",
        "type": "organization",
        "wikidata_qid": "Q116908013",
        "aliases": ["perplexity ai", "perplexity.ai"],
        "description": "AI-powered search engine company",
    },
    "python": {
        "canonical": "Python (programming language)",
        "type": "concept",
        "wikidata_qid": "Q28865",
        "aliases": ["python programming", "python language", "cpython"],
        "description": "High-level programming language",
        "disambiguation": ["Monty Python", "Ball python (snake)"],
    },
    "apple": {
        "canonical": "Apple Inc.",
        "type": "organization",
        "wikidata_qid": "Q312",
        "aliases": ["apple inc", "apple computer", "cupertino company"],
        "description": "American technology company",
        "disambiguation": ["Apple (fruit)", "Apple Records"],
    },
    "rag": {
        "canonical": "Retrieval-Augmented Generation",
        "type": "concept",
        "wikidata_qid": None,
        "aliases": ["retrieval augmented generation", "rag system"],
        "description": "LLM augmentation technique using external retrieval",
    },
}


class ResolvedEntity(BaseModel):
    """A resolved entity with canonical form and metadata."""
    original: str
    canonical: str
    entity_type: str = "unknown"
    wikidata_qid: Optional[str] = None
    description: str = ""
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)
    disambiguation_options: List[str] = Field(default_factory=list)


class EntityResolutionOutput(BaseModel):
    """Output of entity resolution for a set of mentions."""
    resolved: List[ResolvedEntity]
    unresolved: List[str]
    resolution_rate: float = Field(ge=0.0, le=1.0)
    reasoning: str


class EntityResolutionAgent(BaseAgent):
    """
    Agent that resolves entity mentions to canonical identifiers.
    Uses a local knowledge base + fuzzy matching; in production augmented by Wikidata API.
    """

    agent_name = "entity_resolution_agent"
    agent_description = "Resolves entity mentions to canonical identifiers using Wikidata and KB lookup"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config=config or {})
        self._kb = ENTITY_KB

    def validate_input(self, agent_input: AgentInput) -> bool:
        if "entities" not in agent_input.context:
            raise ValueError("Missing required field: entities (list of entity mention strings)")
        if not isinstance(agent_input.context["entities"], list):
            raise ValueError("entities must be a list of strings")
        return True

    async def invoke(self, agent_input: AgentInput) -> AgentOutput:
        entities: List[str] = agent_input.context["entities"]
        context_text: str = agent_input.context.get("context_text", "")

        resolved: List[ResolvedEntity] = []
        unresolved: List[str] = []

        for mention in entities:
            result = self._resolve_entity(mention, context_text)
            if result:
                resolved.append(result)
            else:
                unresolved.append(mention)

        total = len(entities)
        rate = len(resolved) / total if total > 0 else 0.0

        reasoning = (
            f"Resolved {len(resolved)}/{total} entities. "
            f"Rate: {rate:.1%}. "
            f"Unresolved: {unresolved[:5]}"
        )

        output = EntityResolutionOutput(
            resolved=resolved,
            unresolved=unresolved,
            resolution_rate=round(rate, 4),
            reasoning=reasoning,
        )

        avg_confidence = (
            sum(r.confidence for r in resolved) / len(resolved) if resolved else 0.0
        )

        return AgentOutput(
            decision=output.model_dump(),
            reasoning=reasoning,
            confidence_score=round(min(avg_confidence, 1.0), 4),
            metadata={"total": total, "resolved": len(resolved), "unresolved": len(unresolved)},
        )

    def parse_output(self, raw_output: Any) -> AgentOutput:
        if isinstance(raw_output, AgentOutput):
            return raw_output
        return AgentOutput(
            decision=str(raw_output),
            reasoning="Parsed from raw output",
            confidence_score=0.5,
        )

    def _resolve_entity(self, mention: str, context_text: str = "") -> Optional[ResolvedEntity]:
        """Resolve a single entity mention. Returns None if no match found."""
        normalised = mention.lower().strip()

        # Direct key match
        if normalised in self._kb:
            entry = self._kb[normalised]
            return self._build_resolved(mention, entry, confidence=0.95)

        # Alias matching
        for key, entry in self._kb.items():
            if normalised in [a.lower() for a in entry.get("aliases", [])]:
                return self._build_resolved(mention, entry, confidence=0.85)

        # Partial match (entity key contained in mention or vice versa)
        for key, entry in self._kb.items():
            if key in normalised or normalised in key:
                return self._build_resolved(mention, entry, confidence=0.60)

        # Token overlap matching
        mention_tokens = set(re.findall(r"\w+", normalised))
        best_score = 0.0
        best_entry = None
        for key, entry in self._kb.items():
            key_tokens = set(re.findall(r"\w+", key))
            alias_tokens = set()
            for alias in entry.get("aliases", []):
                alias_tokens.update(re.findall(r"\w+", alias.lower()))
            all_tokens = key_tokens | alias_tokens
            if not all_tokens:
                continue
            overlap = len(mention_tokens & all_tokens) / len(all_tokens)
            if overlap > best_score:
                best_score = overlap
                best_entry = entry

        if best_score >= 0.5 and best_entry:
            return self._build_resolved(mention, best_entry, confidence=round(best_score * 0.8, 4))

        return None

    @staticmethod
    def _build_resolved(mention: str, entry: Dict, confidence: float) -> ResolvedEntity:
        return ResolvedEntity(
            original=mention,
            canonical=entry["canonical"],
            entity_type=entry.get("type", "unknown"),
            wikidata_qid=entry.get("wikidata_qid"),
            description=entry.get("description", ""),
            confidence=min(1.0, confidence),
            disambiguation_options=entry.get("disambiguation", []),
        )

    def add_entity(self, key: str, entry: Dict) -> None:
        """Runtime entity KB extension (for testing and dynamic enrichment)."""
        self._kb[key.lower()] = entry
