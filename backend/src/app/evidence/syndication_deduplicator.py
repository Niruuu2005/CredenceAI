"""
Syndication and Lineage Deduplicator.
Implements FR-007, FR-011, DATA-03, Gate G5.
Detects wire-service syndication, republishing, and duplicates so
syndicated articles do not inflate independent corroboration counts.
"""

import re
import hashlib
from typing import List, Dict, Set, Optional
from dataclasses import dataclass, field


WIRE_SERVICES = [
    ("Reuters", re.compile(r"\b(Reuters|Thomson Reuters)\b", re.IGNORECASE)),
    ("Associated Press", re.compile(r"\b(Associated Press|\bAP\b)\b", re.IGNORECASE)),
    ("Bloomberg", re.compile(r"\bBloomberg\b", re.IGNORECASE)),
    ("PR Newswire", re.compile(r"\bPR Newswire\b", re.IGNORECASE)),
    ("Business Wire", re.compile(r"\bBusiness Wire\b", re.IGNORECASE)),
    ("Agence France-Presse", re.compile(r"\b(Agence France-Presse|\bAFP\b)\b", re.IGNORECASE)),
    ("GlobeNewswire", re.compile(r"\bGlobeNewswire\b", re.IGNORECASE)),
]


@dataclass
class SourceCandidate:
    source_id: str
    canonical_url: str
    publisher: Optional[str]
    title: str
    snippet: str
    content_hash: Optional[str] = None


@dataclass
class SyndicationCluster:
    cluster_id: str
    canonical_publisher: str
    wire_service: Optional[str]
    members: List[SourceCandidate] = field(default_factory=list)
    is_syndicated: bool = False

    @property
    def primary_source(self) -> SourceCandidate:
        return self.members[0]


class SyndicationDeduplicator:
    """
    Groups sources sharing upstream origin or duplicate text.
    Ensures independent corroboration measures distinct reporting entities.
    """

    @staticmethod
    def detect_wire_service(text: str) -> Optional[str]:
        for name, pattern in WIRE_SERVICES:
            if pattern.search(text):
                return name
        return None

    @classmethod
    def cluster_sources(cls, sources: List[SourceCandidate]) -> List[SyndicationCluster]:
        """
        Clusters sources by detected wire service and text similarity/hash.
        """
        if not sources:
            return []

        clusters: List[SyndicationCluster] = []
        wire_map: Dict[str, SyndicationCluster] = {}
        hash_map: Dict[str, SyndicationCluster] = {}

        for src in sources:
            content = f"{src.title} {src.snippet}"
            detected_wire = cls.detect_wire_service(content) or cls.detect_wire_service(src.publisher or "")
            c_hash = src.content_hash or hashlib.sha256(content.strip().lower().encode("utf-8")).hexdigest()

            assigned = False

            # 1. Match by identical content hash
            if c_hash in hash_map:
                cluster = hash_map[c_hash]
                cluster.members.append(src)
                cluster.is_syndicated = True
                assigned = True

            # 2. Match by wire service attribution
            elif detected_wire and detected_wire in wire_map:
                cluster = wire_map[detected_wire]
                cluster.members.append(src)
                cluster.is_syndicated = True
                assigned = True

            if not assigned:
                cluster_id = f"cluster_{len(clusters) + 1}_{c_hash[:8]}"
                canonical_pub = detected_wire or src.publisher or "Independent Source"
                new_cluster = SyndicationCluster(
                    cluster_id=cluster_id,
                    canonical_publisher=canonical_pub,
                    wire_service=detected_wire,
                    members=[src],
                    is_syndicated=False,
                )
                clusters.append(new_cluster)
                hash_map[c_hash] = new_cluster
                if detected_wire:
                    wire_map[detected_wire] = new_cluster

        return clusters

    @classmethod
    def get_independent_entity_count(cls, clusters: List[SyndicationCluster]) -> int:
        """
        Calculates the number of genuinely independent reporting origins.
        """
        return len(clusters)
