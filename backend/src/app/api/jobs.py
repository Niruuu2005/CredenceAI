import uuid
import time
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Job, NormalizedResult, DedupGroup, User
from app.services.security import get_current_user
from app.schemas import (
    JobCreate,
    JobSubmitResponse,
    JobStatusResponse,
    QualitySummary,
    SynthesisResponse,
    ExportRequest,
    ExportResponse,
    NormalizedResultResponse,
    DuplicateResponse,
    EntityResponse,
    QualityScoreResponse,
    ErrorResponse,
)
from app.services.intent import classify_intent
from app.services.repository import create_job, get_job, get_job_normalized_results
from app.services.synthesis import SynthesisService
from app.services.vertical_packs import RAGPack
from app.services.quota_service import check_job_quota


from app.limiter import limiter


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["Jobs"])


def _get_user_job(db: Session, job_id: str, user_id: str) -> Job:
    job = db.query(Job).filter(Job.id == job_id, Job.user_id == user_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job


@router.post("", response_model=JobSubmitResponse, status_code=202)
@limiter.limit("30/minute")
def submit_job(
    job_in: JobCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    check_job_quota(db, current_user)

    t0 = time.perf_counter()
    trace_id = getattr(request.state, "trace_id", f"trace_{uuid.uuid4().hex[:12]}")
    job_id = f"job_{uuid.uuid4().hex[:12]}"

    input_text = job_in.query or job_in.input or ""
    exec_mode = job_in.mode or job_in.execution_mode or "standard"

    logger.info(
        f"API  POST /jobs  STATUS=RECEIVED  "
        f"job_id={job_id}  trace_id={trace_id}  "
        f"query='{input_text[:60]}'  "
        f"job_type={job_in.job_type}  "
        f"routing_mode={job_in.routing_mode}"
    )

    # Intent classification
    vertical = job_in.vertical
    if not vertical or vertical == "web":
        intent_res = classify_intent(input_text)
        vertical = intent_res["vertical"]
        logger.info(
            f"API  INTENT  job_id={job_id}  "
            f"-> vertical={vertical}  "
            f"intent={intent_res['intent']}"
        )
    else:
        logger.info(
            f"API  INTENT  job_id={job_id}  "
            f"-> vertical={vertical}  (caller-specified, no classification)"
        )

    # Persist job
    job = create_job(
        db=db,
        job_id=job_id,
        trace_id=trace_id,
        job_type=job_in.job_type,
        input_val=input_text,
        vertical=vertical,
        priority=job_in.priority,
        routing_mode=job_in.routing_mode,
        execution_mode=exec_mode,
        user_id=current_user.id,
    )
    logger.debug(
        f"API  DB_WRITE  job_id={job_id}  status=queued  "
        f"vertical={vertical}"
    )

    # Dispatch worker (eager mode — runs synchronously in dev/test)
    from app.worker import process_job
    logger.info(f"API  DISPATCH  job_id={job_id}  -> worker=process_job")
    process_job.delay(job.id)

    elapsed_ms = (time.perf_counter() - t0) * 1000
    final_status = get_job(db, job_id).status  # read back after worker runs
    logger.info(
        f"API  POST /jobs  STATUS=DISPATCHED  "
        f"job_id={job_id}  "
        f"final_status={final_status}  "
        f"elapsed={elapsed_ms:.2f}ms"
    )

    return JobSubmitResponse(
        job_id=job.id,
        trace_id=job.trace_id,
        status=job.status,
        created_at=job.created_at,
    )


@router.get("/{job_id}", response_model=JobStatusResponse)
def get_job_status(
    job_id: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    t0 = time.perf_counter()
    job = _get_user_job(db, job_id, current_user.id)

    results = get_job_normalized_results(db, job_id)
    results_count = len(results)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    accepted = 0
    rejected = 0
    manual_review = 0
    for r in results:
        if r.quality_scores:
            dec = r.quality_scores.decision
            if dec == "accept":
                accepted += 1
            elif dec == "reject":
                rejected += 1
            elif dec == "review":
                manual_review += 1
        else:
            accepted += 1

    db_status = job.status
    if db_status == "queued":
        status_val = "submitted"
    elif db_status == "running":
        status_val = "processing"
    else:
        status_val = db_status

    logger.info(
        f"API  GET /jobs/{job_id}  STATUS=OK  "
        f"job_status={job.status}  "
        f"results={results_count}  "
        f"error={job.error_message or 'none'}  "
        f"elapsed={elapsed_ms:.2f}ms"
    )

    error_obj = None
    if job.status == "failed" or job.error_message:
        error_obj = ErrorResponse(
            error="job_failed",
            message=job.error_message or "Job execution failed.",
            trace_id=job.trace_id
        )

    result_dict = None
    if job.status == "completed":
        results_responses = _build_job_results_list(db, job.id)
        result_dict = {"results": [r.model_dump() for r in results_responses]}

    return JobStatusResponse(
        job_id=job.id,
        status=status_val,
        results_count=results_count,
        failed_events=0,
        quality_summary=QualitySummary(accepted=accepted, rejected=rejected, manual_review=manual_review),
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        job_type=job.job_type,
        input=job.input,
        submitted_at=job.created_at,
        # SDK fields
        result=result_dict,
        error=error_obj,
        trace_id=job.trace_id,
    )


@router.get("/{job_id}/synthesis", response_model=SynthesisResponse)
async def get_job_synthesis(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _get_user_job(db, job_id, current_user.id)

    results = get_job_normalized_results(db, job_id)
    
    # Map SQLAlchemy models to dict representation for the service
    documents = []
    for r in results:
        documents.append({
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet,
            "source": r.source,
        })

    synthesis_service = SynthesisService()
    synthesis_out = await synthesis_service.synthesize(
        query=job.input,
        documents=documents,
        vertical=job.vertical or "general"
    )

    return SynthesisResponse(
        summary=synthesis_out.summary,
        citations={
            k: {
                "citation_id": v.citation_id,
                "title": v.title,
                "url": v.url,
                "source": v.source,
            }
            for k, v in synthesis_out.citations.items()
        },
        confidence_score=synthesis_out.confidence_score,
    )


@router.post("/{job_id}/export", response_model=ExportResponse)
async def export_job_data(
    job_id: str,
    export_in: ExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    job = _get_user_job(db, job_id, current_user.id)

    results = get_job_normalized_results(db, job_id)
    documents = []
    for r in results:
        documents.append({
            "title": r.title,
            "url": r.url,
            "snippet": r.snippet,
            "source": r.source,
        })

    synthesis_service = SynthesisService()
    synthesis_out = await synthesis_service.synthesize(
        query=job.input,
        documents=documents,
        vertical=job.vertical or "general"
    )

    rag_pack = RAGPack()
    if export_in.format.lower() == "csv":
        content = rag_pack.export_csv(job.input, documents, synthesis_out.summary)
    else:
        content = rag_pack.export_json(job.input, documents, synthesis_out.summary)

    return ExportResponse(
        format=export_in.format,
        content=content,
    )


@router.get("", response_model=List[JobStatusResponse])
def list_jobs(
    request: Request,
    status: Optional[str] = None,
    q: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a paginated list of jobs, optionally filtered by status and query."""
    trace_id = getattr(request.state, "trace_id", None)
    try:
        query = db.query(Job).filter(Job.user_id == current_user.id)
        if status:
            query = query.filter(Job.status == status)
        if q:
            query = query.filter(Job.input.ilike(f"%{q}%"))

        jobs = query.order_by(Job.created_at.desc()).offset(offset).limit(limit).all()

        out = []
        for job in jobs:
            results = get_job_normalized_results(db, job.id)
            results_count = len(results)

            accepted = 0
            rejected = 0
            manual_review = 0
            for r in results:
                if r.quality_scores:
                    dec = r.quality_scores.decision
                    if dec == "accept":
                        accepted += 1
                    elif dec == "reject":
                        rejected += 1
                    elif dec == "review":
                        manual_review += 1
                else:
                    accepted += 1

            db_status = job.status
            if db_status == "queued":
                status_val = "submitted"
            elif db_status == "running":
                status_val = "processing"
            else:
                status_val = db_status

            out.append(JobStatusResponse(
                job_id=job.id,
                status=status_val,
                results_count=results_count,
                failed_events=0,
                quality_summary=QualitySummary(accepted=accepted, rejected=rejected, manual_review=manual_review),
                created_at=job.created_at,
                completed_at=job.completed_at,
                error_message=job.error_message,
                job_type=job.job_type,
                input=job.input,
                submitted_at=job.created_at,
                trace_id=job.trace_id,
            ))
        return out
    except Exception as exc:
        logger.exception(
            "API GET /jobs FAILED user_id=%s trace_id=%s error=%s",
            current_user.id,
            trace_id,
            exc,
        )
        return JSONResponse(
            status_code=500,
            content={
                "error": "internal_error",
                "message": "Failed to list jobs.",
                "detail": "Internal server error",
                "trace_id": trace_id,
            },
        )


def _build_job_results_list(db: Session, job_id: str) -> List[NormalizedResultResponse]:
    results = db.query(NormalizedResult).filter(NormalizedResult.job_id == job_id).all()
    
    out = []
    for r in results:
        qs = None
        if r.quality_scores:
            qs = QualityScoreResponse(
                relevance_score=r.quality_scores.relevance_score,
                source_reliability_score=r.quality_scores.source_reliability_score,
                freshness_score=r.quality_scores.freshness_score,
                authority_score=r.quality_scores.authority_score,
                entity_match_score=r.quality_scores.entity_match_score,
                dedup_confidence=r.quality_scores.dedup_confidence,
                extraction_likelihood_score=r.quality_scores.extraction_likelihood_score,
                risk_score=r.quality_scores.risk_score,
                final_trust_score=r.quality_scores.final_trust_score,
                decision=r.quality_scores.decision,
                reason=r.quality_scores.reason
            )
            
        duplicates = []
        group = db.query(DedupGroup).filter(DedupGroup.canonical_result_id == r.id).first()
        if group:
            for member in group.members:
                m_res = db.query(NormalizedResult).filter(NormalizedResult.id == member.result_id).first()
                if m_res:
                    duplicates.append(DuplicateResponse(
                        id=m_res.id,
                        title=m_res.title,
                        url=m_res.url,
                        snippet=m_res.snippet,
                        source=m_res.source,
                        match_type=member.match_type,
                        confidence=member.confidence
                    ))
                    
        entities = []
        for link in r.entity_links:
            ent = link.entity
            if ent:
                entities.append(EntityResponse(
                    id=ent.id,
                    canonical_name=ent.canonical_name,
                    entity_type=ent.entity_type,
                    description=ent.description,
                    wikidata_id=ent.wikidata_id,
                    wikipedia_url=ent.wikipedia_url,
                    confidence=link.confidence,
                    mention=link.mention
                ))
                
        out.append(NormalizedResultResponse(
            id=r.id,
            job_id=r.job_id,
            source_result_id=r.source_result_id,
            title=r.title,
            url=r.url,
            canonical_url=r.canonical_url,
            snippet=r.snippet,
            source=r.source,
            language=r.language,
            published_at=r.published_at,
            fetched_at=r.fetched_at,
            created_at=r.created_at,
            quality_scores=qs,
            duplicates=duplicates,
            entities=entities
        ))
    return out


@router.get("/{job_id}/results", response_model=List[NormalizedResultResponse])
def get_job_results(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all normalized results for a specific job, including quality scores, duplicates, and entities."""
    _get_user_job(db, job_id, current_user.id)
    return _build_job_results_list(db, job_id)

