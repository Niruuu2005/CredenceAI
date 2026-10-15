"""
Atomic Claim Extractor.
Implements FR-009, EVD-01, EVD-02, EVD-03, DATA-05.
Decomposes assertions into verifiable atomic propositions preserving origin and scope.
"""

import re
import hashlib
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AtomicClaimDraft:
    proposition: str
    subject: Optional[str] = None
    predicate: Optional[str] = None
    object_val: Optional[str] = None
    units: Optional[str] = None
    temporal_scope: Optional[str] = None
    geographic_scope: Optional[str] = None
    origin_type: str = "user_submitted"  # user_submitted, source_extracted


def extract_claims_from_text(
    text: str,
    origin_type: str = "source_extracted",
) -> List[AtomicClaimDraft]:
    """
    Extract atomic propositions from input text.
    Handles user prompts or extracted source passages.
    """
    clean_text = text.strip()
    if not clean_text:
        return []

    # Detect temporal patterns (years like 2024, 2025, 2026)
    year_match = re.search(r"\b(19\d{2}|20\d{2})\b", clean_text)
    temporal_scope = year_match.group(0) if year_match else None

    # Detect percentage or numeric units
    units_match = re.search(r"(\b\d+(?:\.\d+)?%|\$\d+(?:\.\d+)?|\b\d+\s*(?:percent|dollars|meters|km)\b)", clean_text, re.IGNORECASE)
    units = units_match.group(0) if units_match else None

    # For user inquiries or short statements, return atomic claim directly
    if len(clean_text) < 180 or "?" in clean_text:
        return [
            AtomicClaimDraft(
                proposition=clean_text,
                temporal_scope=temporal_scope,
                units=units,
                origin_type=origin_type,
            )
        ]

    # For longer texts, segment by sentence boundaries
    sentences = re.split(r"(?<=[.!?])\s+", clean_text)
    claims: List[AtomicClaimDraft] = []

    for s in sentences:
        s_clean = s.strip()
        if len(s_clean) >= 20:
            claims.append(
                AtomicClaimDraft(
                    proposition=s_clean,
                    temporal_scope=temporal_scope,
                    units=units,
                    origin_type=origin_type,
                )
            )

    return claims[:5]
