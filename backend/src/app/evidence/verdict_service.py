"""
Run-Scoped Verdict Aggregator & Honest Abstention Service.
Implements FR-012, DATA-06, EVD-10, EVD-12.
Computes calibrated verdicts over claim evidence graphs:
- supported
- disputed
- insufficient_evidence
- not_assessed
Eliminates pseudo-scientific "truth probability" percentages (ADR-004).
"""

import uuid
from typing import List, Optional, Dict
from dataclasses import dataclass, field
from sqlalchemy.orm import Session

from app.models import ClaimVerdict, ClaimEvidence, Passage, Source, utc_now
from app.evidence.relation_engine import (
    RELATION_SUPPORTS,
    RELATION_CONTRADICTS,
    RELATION_MENTIONS,
    RELATION_IRRELEVANT,
    RELATION_UNCERTAIN,
)

VERDICT_SUPPORTED = "supported"
VERDICT_DISPUTED = "disputed"
VERDICT_INSUFFICIENT_EVIDENCE = "insufficient_evidence"
VERDICT_NOT_ASSESSED = "not_assessed"

VALID_VERDICTS = {
    VERDICT_SUPPORTED,
    VERDICT_DISPUTED,
    VERDICT_INSUFFICIENT_EVIDENCE,
    VERDICT_NOT_ASSESSED,
}


@dataclass
class VerdictAssessment:
    verdict: str
    rationale: str
    supporting_count: int
    contradicting_count: int
    mentions_count: int
    independent_sources_count: int
    caveats: List[str] = field(default_factory=list)


class VerdictService:
    """
    Evaluates evidence edges for an atomic claim and produces an honest, calibrated verdict.
    """

    @classmethod
    def aggregate_verdict(
        cls,
        evidence_edges: List[ClaimEvidence],
        independent_sources_count: int = 1,
        min_supporting_sources: int = 1,
    ) -> VerdictAssessment:
        """
        Aggregate evidence relations into a run-scoped verdict.
        """
        if not evidence_edges:
            return VerdictAssessment(
                verdict=VERDICT_INSUFFICIENT_EVIDENCE,
                rationale="No relevant passages or citations could be retrieved to substantiate this claim.",
                supporting_count=0,
                contradicting_count=0,
                mentions_count=0,
                independent_sources_count=0,
                caveats=["Evidence retrieval yielded zero matching passages within configured budget."],
            )

        supporting = [e for e in evidence_edges if e.relation == RELATION_SUPPORTS]
        contradicting = [e for e in evidence_edges if e.relation == RELATION_CONTRADICTS]
        mentions = [e for e in evidence_edges if e.relation == RELATION_MENTIONS]

        caveats: List[str] = []

        # 1. Disputed Verdict (both supports and contradicts, or strong contradiction)
        if contradicting and supporting:
            return VerdictAssessment(
                verdict=VERDICT_DISPUTED,
                rationale=(
                    f"Directly disputed: {len(contradicting)} source passage(s) contradict the proposition, "
                    f"while {len(supporting)} passage(s) assert support."
                ),
                supporting_count=len(supporting),
                contradicting_count=len(contradicting),
                mentions_count=len(mentions),
                independent_sources_count=independent_sources_count,
                caveats=["Examined literature contains unresolved conflicting material assertions."],
            )

        if contradicting and not supporting:
            return VerdictAssessment(
                verdict=VERDICT_DISPUTED,
                rationale=f"Contradicted: {len(contradicting)} source passage(s) refute or contradict the proposition.",
                supporting_count=0,
                contradicting_count=len(contradicting),
                mentions_count=len(mentions),
                independent_sources_count=independent_sources_count,
                caveats=["Evidence directly opposes the claim proposition."],
            )

        # 2. Supported Verdict (sufficient corroboration without contradictions)
        if len(supporting) >= min_supporting_sources:
            if independent_sources_count == 1 and len(supporting) > 1:
                caveats.append(
                    "All supporting passages originate from a single or syndicated publisher lineage."
                )

            return VerdictAssessment(
                verdict=VERDICT_SUPPORTED,
                rationale=(
                    f"Supported by {len(supporting)} corroborating passage(s) across "
                    f"{independent_sources_count} independent publisher entity/entities."
                ),
                supporting_count=len(supporting),
                contradicting_count=0,
                mentions_count=len(mentions),
                independent_sources_count=independent_sources_count,
                caveats=caveats,
            )

        # 3. Insufficient Evidence (only mentions, uncertain, or irrelevant)
        return VerdictAssessment(
            verdict=VERDICT_INSUFFICIENT_EVIDENCE,
            rationale=(
                f"Accessible evidence mentions the subject ({len(mentions)} mention(s)) "
                "but does not substantiate the specific atomic proposition."
            ),
            supporting_count=len(supporting),
            contradicting_count=0,
            mentions_count=len(mentions),
            independent_sources_count=independent_sources_count,
            caveats=["Retrieved references lack conclusive grounding for the predicate."],
        )

    @classmethod
    def record_verdict(
        cls,
        db: Session,
        run_id: str,
        claim_id: str,
        assessment: VerdictAssessment,
    ) -> ClaimVerdict:
        """
        Persist or update ClaimVerdict in database.
        """
        existing = (
            db.query(ClaimVerdict)
            .filter(ClaimVerdict.run_id == run_id, ClaimVerdict.claim_id == claim_id)
            .first()
        )
        if existing:
            existing.verdict = assessment.verdict
            existing.rationale = assessment.rationale
            existing.evaluator_version = "v2.0"
            db.commit()
            return existing

        verdict_record = ClaimVerdict(
            id=f"vrd_{uuid.uuid4().hex[:12]}",
            run_id=run_id,
            claim_id=claim_id,
            verdict=assessment.verdict,
            rationale=assessment.rationale,
            evaluator_version="v2.0",
            created_at=utc_now(),
        )
        db.add(verdict_record)
        db.commit()
        return verdict_record
