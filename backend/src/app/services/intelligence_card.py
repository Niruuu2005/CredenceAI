"""
Intelligence Card Generator for CredenceAI Iteration 0.3 (Sprint 56)

Generates structured "Intelligence Cards" — rich entity profiles that aggregate:
- Entity identity (canonical name, type, Wikidata QID)
- Key facts extracted from evidence graph
- Source attribution & confidence metrics
- Related entities and contradictions
- Freshness indicators

Cards are the primary output format for the Company and Research verticals.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class IntelligenceCard:
    """
    A structured entity intelligence card.
    Contains aggregated intelligence about a single entity from multiple sources.
    """
    entity_name: str
    entity_type: str = "unknown"
    canonical_name: str = ""
    wikidata_qid: Optional[str] = None
    description: str = ""

    # Evidence summary
    key_facts: List[Dict[str, Any]] = field(default_factory=list)
    contradictions: List[Dict[str, Any]] = field(default_factory=list)
    related_entities: List[str] = field(default_factory=list)

    # Source metrics
    source_count: int = 0
    avg_confidence: float = 0.0
    highest_corroboration: int = 0

    # Provenance
    sources: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    vertical: str = "general"

    @property
    def freshness_label(self) -> str:
        """Human-readable freshness label based on recency."""
        return "fresh"  # Simplified — in prod driven by freshness_scorer

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entity_name": self.entity_name,
            "entity_type": self.entity_type,
            "canonical_name": self.canonical_name or self.entity_name,
            "wikidata_qid": self.wikidata_qid,
            "description": self.description,
            "key_facts": self.key_facts,
            "contradictions": self.contradictions,
            "related_entities": self.related_entities,
            "source_count": self.source_count,
            "avg_confidence": round(self.avg_confidence, 4),
            "highest_corroboration": self.highest_corroboration,
            "sources": self.sources[:20],
            "generated_at": self.generated_at,
            "vertical": self.vertical,
            "freshness_label": self.freshness_label,
        }


class IntelligenceCardGenerator:
    """
    Generates IntelligenceCards from evidence graph data and entity metadata.

    Usage:
        generator = IntelligenceCardGenerator()
        card = generator.generate(
            entity_name="OpenAI",
            entity_meta={...},
            evidence_graph=graph,
            vertical="company",
        )
    """

    def __init__(self):
        self._cards: Dict[str, IntelligenceCard] = {}

    def generate(
        self,
        entity_name: str,
        entity_meta: Dict[str, Any],
        evidence_nodes: List[Dict[str, Any]],
        contradictions: List[Dict[str, Any]],
        sources: List[str],
        vertical: str = "general",
    ) -> IntelligenceCard:
        """
        Generate an intelligence card for an entity.

        Args:
            entity_name: Primary entity name
            entity_meta: Resolved entity metadata (type, qid, description)
            evidence_nodes: List of ClaimNode.to_dict() outputs for this entity
            contradictions: List of contradiction records
            sources: List of source URLs contributing evidence
            vertical: Research vertical context

        Returns:
            A populated IntelligenceCard
        """
        # Sort nodes by confidence descending → key facts
        sorted_nodes = sorted(evidence_nodes, key=lambda n: n.get("confidence", 0), reverse=True)
        key_facts = [
            {
                "claim": n["canonical_text"],
                "confidence": n.get("confidence", 0),
                "corroboration": n.get("corroboration_count", 1),
                "sources": n.get("supporting_sources", [])[:3],
            }
            for n in sorted_nodes[:10]  # Top 10 facts
        ]

        # Average confidence across all nodes
        confidences = [n.get("confidence", 0) for n in evidence_nodes]
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

        highest_corroboration = max(
            (n.get("corroboration_count", 0) for n in evidence_nodes), default=0
        )

        # Extract related entities from claims text
        related = self._extract_related_entities(sorted_nodes, entity_name)

        card = IntelligenceCard(
            entity_name=entity_name,
            entity_type=entity_meta.get("type", "unknown"),
            canonical_name=entity_meta.get("canonical", entity_name),
            wikidata_qid=entity_meta.get("wikidata_qid"),
            description=entity_meta.get("description", ""),
            key_facts=key_facts,
            contradictions=contradictions[:5],
            related_entities=related,
            source_count=len(set(sources)),
            avg_confidence=avg_confidence,
            highest_corroboration=highest_corroboration,
            sources=list(set(sources))[:20],
            vertical=vertical,
        )

        self._cards[entity_name.lower()] = card
        logger.info(
            f"INTELLIGENCE_CARD  GENERATED  entity={entity_name}  "
            f"facts={len(key_facts)}  sources={card.source_count}  "
            f"confidence={avg_confidence:.2f}"
        )
        return card

    def get_card(self, entity_name: str) -> Optional[IntelligenceCard]:
        """Retrieve a cached card by entity name."""
        return self._cards.get(entity_name.lower())

    def list_cards(self) -> List[str]:
        """Return entity names for all generated cards."""
        return list(self._cards.keys())

    def export_all(self) -> List[Dict[str, Any]]:
        """Export all cards as a list of dicts."""
        return [card.to_dict() for card in self._cards.values()]

    def generate_from_graph(
        self,
        entity_name: str,
        entity_meta: Dict[str, Any],
        evidence_graph,  # EvidenceGraph instance
        vertical: str = "general",
        top_n: int = 10,
    ) -> IntelligenceCard:
        """
        Convenience method: generate card directly from an EvidenceGraph instance.
        """
        nodes = evidence_graph.get_top_claims(entity_name, top_n=top_n)
        contradicted = evidence_graph.get_contradicted_claims()

        evidence_nodes = [n.to_dict() for n in nodes]
        contradictions = [
            {"claim": n.canonical_text, "sources": n.contradicting_sources[:3]}
            for n in contradicted
            if n.entity == entity_name
        ]

        all_sources = []
        for n in nodes:
            all_sources.extend(n.supporting_sources)

        return self.generate(
            entity_name=entity_name,
            entity_meta=entity_meta,
            evidence_nodes=evidence_nodes,
            contradictions=contradictions,
            sources=all_sources,
            vertical=vertical,
        )

    @staticmethod
    def _extract_related_entities(nodes: List[Dict], primary_entity: str) -> List[str]:
        """Simple heuristic: extract capitalised words from claims as related entity candidates."""
        import re
        candidate_set = set()
        primary_lower = primary_entity.lower()
        for node in nodes[:5]:
            text = node.get("canonical_text", "")
            candidates = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", text)
            for c in candidates:
                if c.lower() != primary_lower and len(c) > 2:
                    candidate_set.add(c)
        return list(candidate_set)[:10]
