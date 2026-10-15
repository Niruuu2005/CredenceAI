"""
Claim-Passage Relation Engine.
Implements FR-010, EVD-05, EVD-07, EVD-08, Gate G6.
Evaluates atomic claim-passage pairs into exact 5-label typed relations:
- supports
- contradicts
- mentions
- irrelevant
- uncertain
Applies deterministic sanity checks for numeric, temporal, and polarity compatibility.
"""

import re
from dataclasses import dataclass, field
from typing import Optional, List, Tuple


RELATION_SUPPORTS = "supports"
RELATION_CONTRADICTS = "contradicts"
RELATION_MENTIONS = "mentions"
RELATION_IRRELEVANT = "irrelevant"
RELATION_UNCERTAIN = "uncertain"

VALID_RELATIONS = {
    RELATION_SUPPORTS,
    RELATION_CONTRADICTS,
    RELATION_MENTIONS,
    RELATION_IRRELEVANT,
    RELATION_UNCERTAIN,
}


@dataclass
class RelationAssessment:
    relation: str  # one of VALID_RELATIONS
    confidence: float
    rationale: str
    contradiction_flags: List[str] = field(default_factory=list)
    matched_tokens: List[str] = field(default_factory=list)


class RelationEngine:
    """
    Classifies the factual grounding relationship between an atomic claim proposition
    and an inspectable passage.
    """

    NEGATION_WORDS = {
        "not", "never", "no", "neither", "nor", "denied", "refuted",
        "debunked", "false", "untrue", "disputed", "contradicts", "incorrect"
    }

    AFFIRMATIVE_WORDS = {
        "confirmed", "verified", "announced", "reported", "shows",
        "demonstrated", "achieved", "reached", "proved", "supported"
    }

    @classmethod
    def extract_numbers(cls, text: str) -> List[float]:
        """Extract floats/ints from text, excluding 4-digit years (1900-2099)."""
        raw_matches = re.findall(r"\b\d+(?:\.\d+)?\b", text)
        results = []
        for m in raw_matches:
            try:
                val = float(m)
                if val.is_integer() and 1900 <= int(val) <= 2099:
                    continue
                results.append(val)
            except ValueError:
                pass
        return results

    @classmethod
    def extract_years(cls, text: str) -> set[str]:
        return set(re.findall(r"\b(19\d{2}|20\d{2})\b", text))

    @classmethod
    def evaluate(
        cls,
        proposition: str,
        passage_text: str,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        units: Optional[str] = None,
        temporal_scope: Optional[str] = None,
        geographic_scope: Optional[str] = None,
    ) -> RelationAssessment:
        """
        Evaluate claim against passage text with deterministic sanity checks.
        """
        prop_clean = proposition.strip().lower()
        pas_clean = passage_text.strip().lower()

        if not pas_clean or len(pas_clean) < 5:
            return RelationAssessment(
                relation=RELATION_IRRELEVANT,
                confidence=0.9,
                rationale="Passage is empty or trivial.",
            )

        prop_words = [w for w in re.findall(r"\b\w{3,}\b", prop_clean) if w not in cls.NEGATION_WORDS]
        pas_words = set(re.findall(r"\b\w{3,}\b", pas_clean))

        # Check token overlap
        overlap = [w for w in prop_words if w in pas_words]
        overlap_ratio = len(overlap) / max(len(prop_words), 1)

        # 1. Check for Irrelevance: low lexical overlap
        if overlap_ratio < 0.15 and not any(k in pas_clean for k in (subject or "").lower().split()):
            return RelationAssessment(
                relation=RELATION_IRRELEVANT,
                confidence=0.85,
                rationale="No meaningful contextual or keyword overlap with the claim.",
                matched_tokens=overlap,
            )

        contradiction_flags: List[str] = []

        # 2. Deterministic Temporal Sanity Check (EVD-08)
        claim_years = set(re.findall(r"\b(19\d{2}|20\d{2})\b", prop_clean))
        if temporal_scope:
            claim_years.update(re.findall(r"\b(19\d{2}|20\d{2})\b", temporal_scope))
        passage_years = set(re.findall(r"\b(19\d{2}|20\d{2})\b", pas_clean))

        if claim_years and passage_years:
            if not claim_years.intersection(passage_years):
                # Distinct years mentioned in claim vs passage
                contradiction_flags.append(
                    f"Temporal mismatch: Claim specifies {list(claim_years)}, but passage refers to {list(passage_years)}"
                )

        # 3. Deterministic Numeric Sanity Check (EVD-07)
        claim_nums = cls.extract_numbers(prop_clean)
        pas_nums = cls.extract_numbers(pas_clean)

        if claim_nums and pas_nums:
            common_nums = set(claim_nums).intersection(set(pas_nums))
            if not common_nums:
                diff_ratio = abs(claim_nums[0] - pas_nums[0]) / max(claim_nums[0], 0.001)
                if diff_ratio > 0.05:  # more than 5% difference
                    contradiction_flags.append(
                        f"Numeric discrepancy: Claim states {claim_nums[0]}, but passage specifies {pas_nums[0]}"
                    )

        # 4. Polarity and Direct Negation Checks
        has_passage_negation = any(neg in pas_words for neg in cls.NEGATION_WORDS)
        has_prop_negation = any(neg in prop_clean.split() for neg in cls.NEGATION_WORDS)

        # Direct contradiction signals
        if contradiction_flags:
            return RelationAssessment(
                relation=RELATION_CONTRADICTS,
                confidence=0.85,
                rationale="; ".join(contradiction_flags),
                contradiction_flags=contradiction_flags,
                matched_tokens=overlap,
            )

        if has_passage_negation != has_prop_negation and overlap_ratio >= 0.4:
            # Opposite polarity with high overlap
            return RelationAssessment(
                relation=RELATION_CONTRADICTS,
                confidence=0.8,
                rationale="Negation or dispute polarity detected between claim and passage.",
                contradiction_flags=["Polarity / negation conflict detected."],
                matched_tokens=overlap,
            )

        # 5. Support vs Mentions vs Uncertain
        # If the claim asserts quantitative numbers, but the passage has no corroborating numbers,
        # it only mentions the topic entities rather than affirming the quantitative proposition.
        if claim_nums and not (pas_nums and set(claim_nums).intersection(set(pas_nums))):
            if overlap_ratio >= 0.2:
                return RelationAssessment(
                    relation=RELATION_MENTIONS,
                    confidence=0.75,
                    rationale=f"Passage mentions topic entities ({', '.join(overlap[:4])}) but lacks the specified numeric figures ({claim_nums}).",
                    matched_tokens=overlap,
                )

        if overlap_ratio >= 0.45 or (subject and subject.lower() in pas_clean and overlap_ratio >= 0.3):
            # Strong grounding
            return RelationAssessment(
                relation=RELATION_SUPPORTS,
                confidence=min(0.5 + overlap_ratio * 0.5, 0.95),
                rationale=f"Passage directly corroborates proposition key terms: {', '.join(overlap[:5])}.",
                matched_tokens=overlap,
            )

        if overlap_ratio >= 0.2:
            return RelationAssessment(
                relation=RELATION_MENTIONS,
                confidence=0.7,
                rationale=f"Passage mentions topic entities ({', '.join(overlap[:4])}) but lacks direct propositional affirmation.",
                matched_tokens=overlap,
            )

        return RelationAssessment(
            relation=RELATION_UNCERTAIN,
            confidence=0.5,
            rationale="Passage context is ambiguous or insufficient to establish clear alignment.",
            matched_tokens=overlap,
        )
