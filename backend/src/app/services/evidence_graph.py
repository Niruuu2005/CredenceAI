"""
Evidence Graph for CredenceAI Iteration 0.3 (Sprint 56)

Tracks claims made in source documents and builds a weighted directed graph where:
- Nodes = Claims / Entities
- Edges = Support or contradiction relationships between claims
- Edge weights = Confidence derived from source reliability + corroboration count

The graph supports:
- Claim registration with source attribution
- Corroboration counting (how many sources make the same claim)
- Contradiction tracking
- Graph summary export
"""

import logging
import hashlib
import re
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class Claim:
    """A single factual claim extracted from a source document."""
    claim_id: str
    text: str
    entity: str                     # The primary entity this claim is about
    claim_type: str = "factual"     # factual | statistical | opinion | inference
    source_url: str = ""
    source_reliability: float = 0.5
    extracted_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "text": self.text,
            "entity": self.entity,
            "claim_type": self.claim_type,
            "source_url": self.source_url,
            "source_reliability": self.source_reliability,
            "extracted_at": self.extracted_at,
        }


@dataclass
class ClaimNode:
    """A node in the evidence graph representing a normalised claim."""
    node_id: str
    canonical_text: str
    entity: str
    corroboration_count: int = 0
    contradiction_count: int = 0
    supporting_sources: List[str] = field(default_factory=list)
    contradicting_sources: List[str] = field(default_factory=list)
    avg_source_reliability: float = 0.0
    claim_type: str = "factual"

    @property
    def confidence(self) -> float:
        """Confidence = reliability × corroboration boost, penalised by contradictions."""
        base = self.avg_source_reliability
        boost = min(1.0, self.corroboration_count * 0.15)
        penalty = min(0.5, self.contradiction_count * 0.10)
        return max(0.0, min(1.0, base + boost - penalty))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "canonical_text": self.canonical_text,
            "entity": self.entity,
            "corroboration_count": self.corroboration_count,
            "contradiction_count": self.contradiction_count,
            "supporting_sources": self.supporting_sources[:10],
            "contradicting_sources": self.contradicting_sources[:10],
            "avg_source_reliability": round(self.avg_source_reliability, 4),
            "confidence": round(self.confidence, 4),
            "claim_type": self.claim_type,
        }


@dataclass
class ClaimEdge:
    """A directed edge between two claims in the evidence graph."""
    from_node_id: str
    to_node_id: str
    relationship: str  # "supports" | "contradicts" | "extends"
    weight: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from": self.from_node_id,
            "to": self.to_node_id,
            "relationship": self.relationship,
            "weight": round(self.weight, 4),
        }


class EvidenceGraph:
    """
    In-memory evidence graph for tracking claims and their relationships.

    Key operations:
    - add_claim(): Register a new claim from a source
    - add_contradiction(): Record that two claims conflict
    - get_node(): Retrieve a node by normalised claim text
    - summarise(): Get graph statistics
    - get_top_claims(): Return highest-confidence claims for an entity
    """

    def __init__(self):
        self.nodes: Dict[str, ClaimNode] = {}       # node_id -> ClaimNode
        self.edges: List[ClaimEdge] = []
        self._text_index: Dict[str, str] = {}       # normalised_text -> node_id
        self._entity_index: Dict[str, Set[str]] = {}  # entity -> set of node_ids

    def add_claim(self, claim: Claim) -> ClaimNode:
        """
        Add a claim to the graph. If an equivalent claim already exists,
        increment its corroboration count. Otherwise, create a new node.
        """
        norm_text = self._normalise(claim.text)
        existing_id = self._text_index.get(norm_text)

        if existing_id:
            node = self.nodes[existing_id]
            node.corroboration_count += 1
            if claim.source_url and claim.source_url not in node.supporting_sources:
                node.supporting_sources.append(claim.source_url)
            # Update rolling average reliability
            n = node.corroboration_count
            node.avg_source_reliability = (
                (node.avg_source_reliability * (n - 1) + claim.source_reliability) / n
            )
            logger.debug(f"EVIDENCE_GRAPH  CORROBORATED  node={existing_id}  count={n}")
            return node
        else:
            node_id = self._generate_id(claim.entity, norm_text)
            node = ClaimNode(
                node_id=node_id,
                canonical_text=claim.text,
                entity=claim.entity,
                corroboration_count=1,
                supporting_sources=[claim.source_url] if claim.source_url else [],
                avg_source_reliability=claim.source_reliability,
                claim_type=claim.claim_type,
            )
            self.nodes[node_id] = node
            self._text_index[norm_text] = node_id

            if claim.entity not in self._entity_index:
                self._entity_index[claim.entity] = set()
            self._entity_index[claim.entity].add(node_id)

            logger.debug(f"EVIDENCE_GRAPH  NEW_CLAIM  node={node_id}  entity={claim.entity}")
            return node

    def add_contradiction(self, claim_text_a: str, claim_text_b: str, source_url: str = "") -> bool:
        """
        Record that two claims contradict each other.
        Returns True if both claims exist in the graph.
        """
        id_a = self._text_index.get(self._normalise(claim_text_a))
        id_b = self._text_index.get(self._normalise(claim_text_b))

        if not id_a or not id_b:
            logger.warning(f"EVIDENCE_GRAPH  CONTRADICTION_NOT_FOUND  a={claim_text_a[:40]}  b={claim_text_b[:40]}")
            return False

        node_a = self.nodes[id_a]
        node_b = self.nodes[id_b]

        node_a.contradiction_count += 1
        node_b.contradiction_count += 1
        if source_url:
            if source_url not in node_a.contradicting_sources:
                node_a.contradicting_sources.append(source_url)
            if source_url not in node_b.contradicting_sources:
                node_b.contradicting_sources.append(source_url)

        edge = ClaimEdge(from_node_id=id_a, to_node_id=id_b, relationship="contradicts", weight=1.0)
        self.edges.append(edge)
        logger.debug(f"EVIDENCE_GRAPH  CONTRADICTION  {id_a} <-> {id_b}")
        return True

    def add_support_edge(self, from_text: str, to_text: str, weight: float = 1.0) -> bool:
        """Add a directed 'supports' edge between two claims."""
        id_from = self._text_index.get(self._normalise(from_text))
        id_to = self._text_index.get(self._normalise(to_text))

        if not id_from or not id_to:
            return False

        edge = ClaimEdge(from_node_id=id_from, to_node_id=id_to, relationship="supports", weight=weight)
        self.edges.append(edge)
        return True

    def get_node(self, claim_text: str) -> Optional[ClaimNode]:
        """Retrieve a node by its (normalised) canonical claim text."""
        node_id = self._text_index.get(self._normalise(claim_text))
        return self.nodes.get(node_id) if node_id else None

    def get_top_claims(self, entity: str, top_n: int = 5) -> List[ClaimNode]:
        """Return the highest-confidence claims for a given entity."""
        node_ids = self._entity_index.get(entity, set())
        nodes = [self.nodes[nid] for nid in node_ids if nid in self.nodes]
        nodes.sort(key=lambda n: n.confidence, reverse=True)
        return nodes[:top_n]

    def get_contradicted_claims(self) -> List[ClaimNode]:
        """Return all claims that have at least one contradiction."""
        return [n for n in self.nodes.values() if n.contradiction_count > 0]

    def summarise(self) -> Dict[str, Any]:
        """Return a summary of the graph statistics."""
        all_confidences = [n.confidence for n in self.nodes.values()]
        return {
            "total_nodes": len(self.nodes),
            "total_edges": len(self.edges),
            "total_entities": len(self._entity_index),
            "contradicted_claims": len(self.get_contradicted_claims()),
            "avg_confidence": round(sum(all_confidences) / len(all_confidences), 4) if all_confidences else 0.0,
            "max_corroboration": max((n.corroboration_count for n in self.nodes.values()), default=0),
        }

    def export(self) -> Dict[str, Any]:
        """Full graph export as dictionary."""
        return {
            "nodes": [n.to_dict() for n in self.nodes.values()],
            "edges": [e.to_dict() for e in self.edges],
            "summary": self.summarise(),
        }

    # ──────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────

    @staticmethod
    def _normalise(text: str) -> str:
        """Normalise claim text for deduplication matching."""
        text = text.lower().strip()
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"[^\w\s]", "", text)
        return text

    @staticmethod
    def _generate_id(entity: str, norm_text: str) -> str:
        content = f"{entity}:{norm_text}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
