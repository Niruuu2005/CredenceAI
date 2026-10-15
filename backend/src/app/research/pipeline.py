"""
Durable Research Execution Pipeline.
Orchestrates sequential run stages: planning -> retrieving -> extracting -> verifying -> reporting.
Implements FR-003, FR-004, FR-005, FR-007 to FR-016, Gate G4, Gate G5, Gate G6, Gate G7.
"""

import hashlib
import json
import time
import uuid
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models import (
    ResearchRun,
    RunStep,
    Source,
    Snapshot,
    Passage,
    Claim,
    ClaimEvidence,
    ClaimVerdict,
    Report,
    utc_now,
)
from app.sources.router import SourceRouter, source_registry
from app.sources.protocol import SourceClass
from app.evidence.claim_extractor import extract_claims_from_text
from app.evidence.syndication_deduplicator import SyndicationDeduplicator, SourceCandidate
from app.evidence.relation_engine import RelationEngine
from app.evidence.verdict_service import VerdictService
from app.reporting.report_generator import ReportGenerator

logger = logging.getLogger(__name__)


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def check_and_handle_cancellation(run: ResearchRun, db: Session) -> bool:
    """Check cancellation checkpoint. Returns True if cancelled and stops pipeline."""
    db.refresh(run)
    if run.status == "cancelled":
        logger.info(f"PIPELINE  run_id={run.id}  STATUS=CANCELLED_CHECKPOINT")
        return True
    return False


async def execute_research_run(
    run_id: str,
    db: Session,
    router: Optional[SourceRouter] = None,
) -> ResearchRun:
    """
    Execute full asynchronous investigation pipeline with state tracking and cancellation checkpoints.
    """
    router = router or SourceRouter(source_registry)
    run = db.query(ResearchRun).filter(ResearchRun.id == run_id).first()
    if not run:
        raise ValueError(f"Research run '{run_id}' not found.")

    if run.status == "cancelled":
        return run

    budget = json.loads(run.budget_json or "{}")

    # =========================================================================
    # STAGE 1: PLANNING
    # =========================================================================
    run.status = "planning"
    db.commit()

    step_planning = (
        db.query(RunStep)
        .filter(RunStep.run_id == run.id, RunStep.step_key == "planning")
        .first()
    )
    if not step_planning:
        step_planning = RunStep(id=f"step_plan_{run.id[:8]}", run_id=run.id, step_key="planning")
        db.add(step_planning)
    step_planning.state = "running"
    step_planning.started_at = utc_now()
    step_planning.attempt_count += 1
    db.commit()

    if check_and_handle_cancellation(run, db):
        step_planning.state = "cancelled"
        db.commit()
        return run

    # Simulate planning duration & configuration
    step_planning.state = "completed"
    step_planning.completed_at = utc_now()
    db.commit()

    # =========================================================================
    # STAGE 2: RETRIEVING
    # =========================================================================
    run.status = "retrieving"
    step_retrieving = RunStep(
        id=f"step_ret_{run.id[:8]}",
        run_id=run.id,
        step_key="retrieving",
        state="running",
        started_at=utc_now(),
        attempt_count=1,
    )
    db.add(step_retrieving)
    db.commit()

    if check_and_handle_cancellation(run, db):
        step_retrieving.state = "cancelled"
        db.commit()
        return run

    search_result = await router.route_and_search(
        query=run.question,
        mode=run.mode,
        budget=budget,
    )

    step_retrieving.duration_ms = search_result.coverage.stage_duration_ms
    step_retrieving.state = "completed"
    step_retrieving.completed_at = utc_now()
    db.commit()

    # =========================================================================
    # STAGE 3: EXTRACTING (Sources, Snapshots, Passages, Claims)
    # =========================================================================
    run.status = "extracting"
    step_extracting = RunStep(
        id=f"step_ext_{run.id[:8]}",
        run_id=run.id,
        step_key="extracting",
        state="running",
        started_at=utc_now(),
        attempt_count=1,
    )
    db.add(step_extracting)
    db.commit()

    if check_and_handle_cancellation(run, db):
        step_extracting.state = "cancelled"
        db.commit()
        return run

    passages_created: list[Passage] = []

    for hit in search_result.hits:
        # Create or fetch Source
        source = db.query(Source).filter(Source.canonical_url == hit.canonical_url).first()
        if not source:
            source = Source(
                id=f"src_{_sha256(hit.canonical_url or hit.url)[:12]}",
                canonical_url=hit.canonical_url or hit.url,
                publisher=hit.publisher,
                source_class=hit.source_class.value,
            )
            db.add(source)
            db.flush()

        # Create Snapshot
        content_text = hit.snippet or hit.title
        snap_hash = _sha256(content_text)
        snapshot = Snapshot(
            id=f"snap_{snap_hash[:12]}",
            source_id=source.id,
            content_hash=snap_hash,
            permitted_excerpt=content_text[:1000],
            rights_status="fair_use_excerpt",
            fetched_at=utc_now(),
        )
        db.add(snapshot)
        db.flush()

        # Create Passage with offset anchors
        passage_text = content_text.strip()
        passage_hash = _sha256(passage_text)
        passage = Passage(
            id=f"pas_{passage_hash[:12]}",
            snapshot_id=snapshot.id,
            text_content=passage_text,
            char_offset_start=0,
            char_offset_end=len(passage_text),
            passage_hash=passage_hash,
            extraction_version="v2.0",
        )
        db.add(passage)
        db.flush()
        passages_created.append(passage)

    # Create Atomic Claims from User's Question/Proposition using ClaimExtractor
    extracted_claim_drafts = extract_claims_from_text(run.question, origin_type="user_submitted")
    user_claims: list[Claim] = []
    for draft in extracted_claim_drafts:
        claim_id = f"clm_{_sha256(draft.proposition)[:12]}"
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if not claim:
            claim = Claim(
                id=claim_id,
                workspace_id=run.workspace_id,
                proposition=draft.proposition,
                subject=draft.subject,
                predicate=draft.predicate,
                object_val=draft.object_val,
                units=draft.units,
                temporal_scope=draft.temporal_scope,
                geographic_scope=draft.geographic_scope,
                origin_type=draft.origin_type,
                extractor_version="v2.0",
            )
            db.add(claim)
            db.flush()
        user_claims.append(claim)

    if not user_claims:
        fallback_claim = Claim(
            id=f"clm_{_sha256(run.question)[:12]}",
            workspace_id=run.workspace_id,
            proposition=run.question,
            origin_type="user_submitted",
            extractor_version="v2.0",
        )
        db.add(fallback_claim)
        db.flush()
        user_claims.append(fallback_claim)

    # Detect syndication and calculate genuinely independent entities (FR-011, DATA-03, Gate G5)
    candidates: list[SourceCandidate] = [
        SourceCandidate(
            source_id=f"src_{_sha256(h.canonical_url or h.url)[:12]}",
            canonical_url=h.canonical_url or h.url,
            publisher=h.publisher,
            title=h.title,
            snippet=h.snippet,
        )
        for h in search_result.hits
    ]
    clusters = SyndicationDeduplicator.cluster_sources(candidates)
    independent_count = SyndicationDeduplicator.get_independent_entity_count(clusters)

    step_extracting.state = "completed"
    step_extracting.completed_at = utc_now()
    db.commit()

    # =========================================================================
    # STAGE 4: VERIFYING (Evidence Relations & Verdicts)
    # =========================================================================
    run.status = "verifying"
    step_verifying = RunStep(
        id=f"step_ver_{run.id[:8]}",
        run_id=run.id,
        step_key="verifying",
        state="running",
        started_at=utc_now(),
        attempt_count=1,
    )
    db.add(step_verifying)
    db.commit()

    if check_and_handle_cancellation(run, db):
        step_verifying.state = "cancelled"
        db.commit()
        return run

    primary_claim = user_claims[0]
    created_edges: list[ClaimEvidence] = []

    for passage in passages_created:
        # Run 5-label relation classification with deterministic sanity checks (FR-010, EVD-05, Gate G6)
        assessment = RelationEngine.evaluate(
            proposition=primary_claim.proposition,
            passage_text=passage.text_content,
            subject=primary_claim.subject,
            predicate=primary_claim.predicate,
            units=primary_claim.units,
            temporal_scope=primary_claim.temporal_scope,
            geographic_scope=primary_claim.geographic_scope,
        )

        edge = ClaimEvidence(
            id=f"edge_{uuid.uuid4().hex[:10]}",
            claim_id=primary_claim.id,
            passage_id=passage.id,
            relation=assessment.relation,
            rationale=assessment.rationale,
            assessor_version="v2.0",
        )
        db.add(edge)
        created_edges.append(edge)

    db.flush()

    # Aggregate run-scoped calibrated verdict (FR-012, EVD-10, EVD-12)
    verdict_assessment = VerdictService.aggregate_verdict(
        evidence_edges=created_edges,
        independent_sources_count=independent_count,
    )
    verdict_record = VerdictService.record_verdict(
        db=db,
        run_id=run.id,
        claim_id=primary_claim.id,
        assessment=verdict_assessment,
    )

    step_verifying.state = "completed"
    step_verifying.completed_at = utc_now()
    db.commit()

    # =========================================================================
    # STAGE 5: REPORTING (Frozen Citation-Validated Report Gate)
    # =========================================================================
    run.status = "reporting"
    step_reporting = RunStep(
        id=f"step_rep_{run.id[:8]}",
        run_id=run.id,
        step_key="reporting",
        state="running",
        started_at=utc_now(),
        attempt_count=1,
    )
    db.add(step_reporting)
    db.commit()

    if check_and_handle_cancellation(run, db):
        step_reporting.state = "cancelled"
        db.commit()
        return run

    # Build coverage summary for report
    coverage_lines = [
        f"- Providers queried: {', '.join(search_result.coverage.queried_sources) or 'None'}",
        f"- Successful: {', '.join(search_result.coverage.successful_sources) or 'None'}",
        f"- Independent syndication origins: {independent_count}",
    ]
    if search_result.coverage.skipped_sources:
        coverage_lines.append(f"- Skipped: {', '.join(search_result.coverage.skipped_sources.keys())}")
    if search_result.coverage.failed_sources:
        coverage_lines.append(f"- Failures: {', '.join(search_result.coverage.failed_sources.keys())}")

    # Generate frozen report and enforce Gate G7 citation resolution
    report = ReportGenerator.create_frozen_report(
        db=db,
        run=run,
        verdict=verdict_record,
        passages=passages_created,
        coverage_summary="\n".join(coverage_lines),
    )

    step_reporting.state = "completed"
    step_reporting.completed_at = utc_now()

    # Terminal Outcome: completed or partial
    if search_result.coverage.failed_sources:
        run.status = "partial"
    else:
        run.status = "completed"

    run.completed_at = utc_now()
    run.updated_at = utc_now()
    db.commit()
    db.refresh(run)

    logger.info(
        f"PIPELINE_COMPLETE  run_id={run.id}  status={run.status}  "
        f"passages={len(passages_created)}  verdict={verdict_record.verdict}"
    )
    return run

