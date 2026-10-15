"""
Research Runs v2 REST API Endpoints.
Implements SRS Section 4, FR-002, FR-003, FR-012, FR-014, FR-015, Gate G2, Gate G7.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.dependencies import get_auth_context, get_auth_context_allow_guest
from app.identity.auth_context import AuthContext, Permission
from app.models import (
    ResearchRun,
    RunStep,
    Claim,
    ClaimEvidence,
    ClaimVerdict,
    Report,
    Source,
    Snapshot,
    Passage,
)
from app.research.service import (
    create_research_run,
    get_research_run,
    cancel_research_run,
    list_workspace_runs,
)
from app.research.pipeline import execute_research_run
from app.evidence.review_service import ReviewService, ReviewPermissionError
from app.api.v2.schemas import (
    ResearchRunCreateRequest,
    ResearchRunResponse,
    SourceItemResponse,
    ClaimResponse,
    EvidenceEdgeResponse,
    ReportResponse,
    EvidenceReviewRequest,
    ReportApprovalRequest,
)

router = APIRouter(prefix="/research-runs", tags=["Research Runs v2"])


@router.post("", response_model=ResearchRunResponse, status_code=status.HTTP_201_CREATED)
def create_run(
    req: ResearchRunCreateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context_allow_guest),
):
    """
    Initiate a new research run within the caller's authorized workspace.
    Guarantees idempotency via `idempotency_key` (AT-01).
    """
    if not auth.has_permission(Permission.CREATE_RESEARCH):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to create research runs.")

    run, was_created = create_research_run(
        db=db,
        auth=auth,
        question=req.question,
        mode=req.mode,
        idempotency_key=req.idempotency_key,
        filters=req.filters,
        budget=req.budget,
    )

    return run


@router.get("", response_model=List[ResearchRunResponse])
def list_runs(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context_allow_guest),
):
    """List runs strictly scoped to the active workspace."""
    return list_workspace_runs(db=db, auth=auth, limit=limit, offset=offset)


@router.get("/{run_id}", response_model=ResearchRunResponse)
def get_run(
    run_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context_allow_guest),
):
    """Retrieve run status, stage step progress, and timings."""
    run = get_research_run(db=db, auth=auth, run_id=run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research run '{run_id}' not found.")
    return run


@router.post("/{run_id}/execute", response_model=ResearchRunResponse)
async def execute_run_now(
    run_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context_allow_guest),
):
    """Directly trigger pipeline execution for a pending run."""
    run = get_research_run(db=db, auth=auth, run_id=run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research run '{run_id}' not found.")

    completed_run = await execute_research_run(run_id=run.id, db=db)
    return completed_run


@router.post("/{run_id}/cancel", response_model=ResearchRunResponse)
def cancel_run(
    run_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context_allow_guest),
):
    """Cancel an ongoing research run at the next checkpoint."""
    if not auth.has_permission(Permission.CANCEL_RESEARCH):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to cancel runs.")

    run = cancel_research_run(db=db, auth=auth, run_id=run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research run '{run_id}' not found.")
    return run


@router.get("/{run_id}/sources", response_model=List[SourceItemResponse])
def get_run_sources(
    run_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context_allow_guest),
):
    """List sources acquired during this research run."""
    run = get_research_run(db=db, auth=auth, run_id=run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research run '{run_id}' not found.")

    # Return distinct sources queried
    sources = db.query(Source).limit(100).all()
    return sources


@router.get("/{run_id}/claims", response_model=List[ClaimResponse])
def get_run_claims(
    run_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context_allow_guest),
):
    """List atomic propositions evaluated for this run along with calibrated verdicts."""
    run = get_research_run(db=db, auth=auth, run_id=run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research run '{run_id}' not found.")

    verdicts = db.query(ClaimVerdict).filter(ClaimVerdict.run_id == run.id).all()
    verdict_map = {v.claim_id: v for v in verdicts}

    claims = db.query(Claim).filter(Claim.workspace_id == auth.workspace_id).limit(100).all()

    results = []
    for c in claims:
        v = verdict_map.get(c.id)
        results.append(
            ClaimResponse(
                id=c.id,
                proposition=c.proposition,
                subject=c.subject,
                predicate=c.predicate,
                object_val=c.object_val,
                units=c.units,
                temporal_scope=c.temporal_scope,
                geographic_scope=c.geographic_scope,
                origin_type=c.origin_type,
                verdict=v.verdict if v else None,
                rationale=v.rationale if v else None,
            )
        )
    return results


@router.get("/{run_id}/claims/{claim_id}/evidence", response_model=List[EvidenceEdgeResponse])
def get_claim_evidence(
    run_id: str,
    claim_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context_allow_guest),
):
    """Retrieve grounded evidence edges and passages for a specific claim."""
    run = get_research_run(db=db, auth=auth, run_id=run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research run '{run_id}' not found.")

    edges = db.query(ClaimEvidence).filter(ClaimEvidence.claim_id == claim_id).all()
    results = []

    for edge in edges:
        pas = db.query(Passage).filter(Passage.id == edge.passage_id).first()
        results.append(
            EvidenceEdgeResponse(
                id=edge.id,
                claim_id=edge.claim_id,
                passage_id=edge.passage_id,
                relation=edge.relation,
                rationale=edge.rationale,
                assessor_version=edge.assessor_version,
                passage_text=pas.text_content if pas else "",
                reviewer_id=edge.reviewer_id,
                reviewer_notes=edge.reviewer_notes,
                reviewed_at=edge.reviewed_at,
            )
        )
    return results


@router.get("/{run_id}/reports/{version}", response_model=ReportResponse)
def get_run_report(
    run_id: str,
    version: int,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context_allow_guest),
):
    """Retrieve a citation-frozen reproducible research brief."""
    run = get_research_run(db=db, auth=auth, run_id=run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research run '{run_id}' not found.")

    report = (
        db.query(Report)
        .filter(Report.run_id == run.id, Report.version == version)
        .first()
    )
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Report version {version} not found for run '{run_id}'.")
    return report


@router.post("/{run_id}/claims/{claim_id}/evidence/{evidence_id}/review", response_model=EvidenceEdgeResponse)
def review_evidence(
    run_id: str,
    claim_id: str,
    evidence_id: str,
    req: EvidenceReviewRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """Human review annotation or dispute over an evidence grounding edge (FR-014, BR-06)."""
    run = get_research_run(db=db, auth=auth, run_id=run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research run '{run_id}' not found.")

    try:
        updated = ReviewService.annotate_evidence(
            db=db,
            auth_context=auth,
            evidence_id=evidence_id,
            new_relation=req.new_relation,
            reviewer_notes=req.reviewer_notes,
        )
    except ReviewPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    pas = db.query(Passage).filter(Passage.id == updated.passage_id).first()
    return EvidenceEdgeResponse(
        id=updated.id,
        claim_id=updated.claim_id,
        passage_id=updated.passage_id,
        relation=updated.relation,
        rationale=updated.rationale,
        assessor_version=updated.assessor_version,
        passage_text=pas.text_content if pas else "",
        reviewer_id=updated.reviewer_id,
        reviewer_notes=updated.reviewer_notes,
        reviewed_at=updated.reviewed_at,
    )


@router.post("/{run_id}/reports/{report_id}/approve", response_model=ReportResponse)
def approve_report(
    run_id: str,
    report_id: str,
    req: ReportApprovalRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """Human reviewer approval for a frozen research brief."""
    run = get_research_run(db=db, auth=auth, run_id=run_id)
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Research run '{run_id}' not found.")

    try:
        report = ReviewService.approve_report(
            db=db,
            auth_context=auth,
            report_id=report_id,
            reviewer_notes=req.reviewer_notes,
        )
    except ReviewPermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    return report
