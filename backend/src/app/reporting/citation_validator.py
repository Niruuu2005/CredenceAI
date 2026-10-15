"""
Citation Resolution Validator & Manifest Hash Enforcer.
Implements FR-015, FR-016, Release Gate G7, RPT-03, AT-04.
Enforces 100% resolution of citations in research briefs against immutable database passages.
Rejects report publishing if any citation is unanchored or invalid.
"""

import re
import hashlib
from typing import List, Set, Dict, Optional
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.models import Passage, Snapshot, Source, ResearchRun


class CitationResolutionError(Exception):
    """Raised when one or more citations cannot be resolved to frozen passages."""
    def __init__(self, message: str, unresolved_ids: List[str]):
        super().__init__(message)
        self.unresolved_ids = unresolved_ids


@dataclass
class CitationValidationResult:
    is_valid: bool
    cited_passage_ids: List[str]
    resolved_passage_ids: List[str]
    unresolved_passage_ids: List[str]
    manifest_hash: str
    error_message: Optional[str] = None


class CitationValidator:
    """
    Parses and verifies passage citation tokens in generated research briefs.
    """

    # Matches patterns like:
    # [citation:pas_12345] or [^pas_12345] or (Passage: `pas_12345`) or `pas_12345`
    CITATION_PATTERNS = [
        re.compile(r"\[citation:(pas_[a-zA-Z0-9_-]+)\]", re.IGNORECASE),
        re.compile(r"\[\^(pas_[a-zA-Z0-9_-]+)\]", re.IGNORECASE),
        re.compile(r"\(Passage:\s*`?(pas_[a-zA-Z0-9_-]+)`?\)", re.IGNORECASE),
        re.compile(r"\b(pas_[a-zA-Z0-9]{8,24})\b"),
    ]

    @classmethod
    def extract_cited_passage_ids(cls, markdown_text: str) -> List[str]:
        """
        Extract all unique cited passage IDs from markdown text preserving order of first appearance.
        """
        seen: Set[str] = set()
        citations: List[str] = []

        for pattern in cls.CITATION_PATTERNS:
            for match in pattern.finditer(markdown_text):
                p_id = match.group(1)
                if p_id not in seen:
                    seen.add(p_id)
                    citations.append(p_id)

        return citations

    @classmethod
    def compute_manifest_hash(cls, passages: List[Passage]) -> str:
        """
        Computes deterministic SHA-256 manifest hash of frozen passages.
        Sorted by passage ID to ensure reproducible hash independent of query order.
        """
        if not passages:
            return hashlib.sha256(b"empty_manifest").hexdigest()

        sorted_passages = sorted(passages, key=lambda p: p.id)
        tokens = [f"{p.id}:{p.passage_hash}" for p in sorted_passages]
        combined = "::".join(tokens)
        return hashlib.sha256(combined.encode("utf-8")).hexdigest()

    @classmethod
    def validate_and_compute_manifest(
        cls,
        db: Session,
        markdown_text: str,
        expected_run_id: Optional[str] = None,
    ) -> CitationValidationResult:
        """
        Validate all citation tokens in markdown text against the database.
        Release Gate G7 / AT-04: If any citation ID does not exist in DB, validation FAILS.
        """
        cited_ids = cls.extract_cited_passage_ids(markdown_text)

        if not cited_ids:
            # If text has no citations, manifest hash is empty manifest
            return CitationValidationResult(
                is_valid=True,
                cited_passage_ids=[],
                resolved_passage_ids=[],
                unresolved_passage_ids=[],
                manifest_hash=cls.compute_manifest_hash([]),
            )

        # Query passages
        found_passages = db.query(Passage).filter(Passage.id.in_(cited_ids)).all()
        found_map: Dict[str, Passage] = {p.id: p for p in found_passages}

        resolved_ids = [p_id for p_id in cited_ids if p_id in found_map]
        unresolved_ids = [p_id for p_id in cited_ids if p_id not in found_map]

        if unresolved_ids:
            err_msg = (
                f"Release Gate G7 Violated: Report contains {len(unresolved_ids)} unresolvable "
                f"citation(s): {', '.join(unresolved_ids)}"
            )
            return CitationValidationResult(
                is_valid=False,
                cited_passage_ids=cited_ids,
                resolved_passage_ids=resolved_ids,
                unresolved_passage_ids=unresolved_ids,
                manifest_hash="",
                error_message=err_msg,
            )

        manifest_hash = cls.compute_manifest_hash(found_passages)

        return CitationValidationResult(
            is_valid=True,
            cited_passage_ids=cited_ids,
            resolved_passage_ids=resolved_ids,
            unresolved_passage_ids=[],
            manifest_hash=manifest_hash,
        )

    @classmethod
    def enforce_gate_g7(
        cls,
        db: Session,
        markdown_text: str,
        expected_run_id: Optional[str] = None,
    ) -> str:
        """
        Enforce Release Gate G7. Raises CitationResolutionError if any citation fails resolution.
        Returns the computed manifest_hash on success.
        """
        result = cls.validate_and_compute_manifest(db, markdown_text, expected_run_id)
        if not result.is_valid:
            raise CitationResolutionError(
                result.error_message or "Citation resolution failure.",
                unresolved_ids=result.unresolved_passage_ids,
            )
        return result.manifest_hash
