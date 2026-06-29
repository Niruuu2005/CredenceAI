import datetime
from typing import Optional, List
from sqlalchemy.orm import Session
from app.models import Job, SourceResult, NormalizedResult

def create_job(
    db: Session,
    job_id: str,
    trace_id: str,
    job_type: str,
    input_val: str,
    vertical: Optional[str] = None,
    priority: str = "normal",
    routing_mode: str = "free_first",
    execution_mode: str = "standard",
    user_id: Optional[str] = None
) -> Job:
    job = Job(
        id=job_id,
        trace_id=trace_id,
        job_type=job_type,
        input=input_val,
        vertical=vertical,
        priority=priority,
        routing_mode=routing_mode,
        execution_mode=execution_mode,
        user_id=user_id,
        status="queued",
        created_at=datetime.datetime.now(datetime.UTC),
        updated_at=datetime.datetime.now(datetime.UTC)
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    return job

def update_job_status(
    db: Session,
    job_id: str,
    status: str,
    completed_at: Optional[datetime.datetime] = None,
    error_message: Optional[str] = None
) -> Optional[Job]:
    job = db.query(Job).filter(Job.id == job_id).first()
    if job:
        job.status = status
        job.updated_at = datetime.datetime.now(datetime.UTC)
        if completed_at:
            job.completed_at = completed_at
        if error_message:
            job.error_message = error_message
        db.commit()
        db.refresh(job)
    return job

def get_job(db: Session, job_id: str) -> Optional[Job]:
    return db.query(Job).filter(Job.id == job_id).first()

def create_source_result(
    db: Session,
    source_result_id: str,
    job_id: str,
    source: str,
    source_type: str,
    input_value: str,
    status: str,
    raw_payload_ref: Optional[str] = None,
    confidence: float = 1.0
) -> SourceResult:
    source_res = SourceResult(
        id=source_result_id,
        job_id=job_id,
        source=source,
        source_type=source_type,
        input_value=input_value,
        raw_payload_ref=raw_payload_ref,
        status=status,
        confidence=confidence,
        fetched_at=datetime.datetime.now(datetime.UTC)
    )
    db.add(source_res)
    db.commit()
    db.refresh(source_res)
    return source_res

def create_normalized_result(
    db: Session,
    normalized_result_id: str,
    job_id: str,
    source_result_id: str,
    title: str,
    url: str,
    source: str,
    canonical_url: Optional[str] = None,
    snippet: Optional[str] = None,
    language: str = "en",
    raw_payload_ref: Optional[str] = None
) -> NormalizedResult:
    norm_res = NormalizedResult(
        id=normalized_result_id,
        job_id=job_id,
        source_result_id=source_result_id,
        title=title,
        url=url,
        canonical_url=canonical_url or url,
        snippet=snippet,
        source=source,
        language=language,
        raw_payload_ref=raw_payload_ref,
        fetched_at=datetime.datetime.now(datetime.UTC),
        created_at=datetime.datetime.now(datetime.UTC)
    )
    db.add(norm_res)
    db.commit()
    db.refresh(norm_res)
    return norm_res

def get_job_normalized_results(db: Session, job_id: str) -> List[NormalizedResult]:
    return db.query(NormalizedResult).filter(NormalizedResult.job_id == job_id).all()


# Version 0.2 database repository helper functions
from app.models import QualityScore, DedupGroup, DedupMember, Entity, EntityAlias, EntityLink

def create_quality_score(
    db: Session,
    quality_score_id: str,
    result_id: str,
    scores: dict
) -> QualityScore:
    qs = QualityScore(
        id=quality_score_id,
        result_id=result_id,
        relevance_score=scores.get("relevance_score", 0.0),
        source_reliability_score=scores.get("source_reliability_score", 0.0),
        freshness_score=scores.get("freshness_score", 0.0),
        authority_score=scores.get("authority_score", 0.0),
        entity_match_score=scores.get("entity_match_score", 0.0),
        dedup_confidence=scores.get("dedup_confidence", 0.0),
        extraction_likelihood_score=scores.get("extraction_likelihood_score", 0.0),
        risk_score=scores.get("risk_score", 0.0),
        final_trust_score=scores.get("final_trust_score", 0.0),
        decision=scores.get("decision", "accept"),
        reason=scores.get("reason"),
        created_at=datetime.datetime.now(datetime.UTC)
    )
    db.add(qs)
    db.commit()
    db.refresh(qs)
    return qs

def create_dedup_group(
    db: Session,
    group_id: str,
    group_type: str,
    canonical_result_id: str,
    canonical_url: str,
    content_hash: Optional[str] = None,
    simhash: Optional[str] = None
) -> DedupGroup:
    dg = DedupGroup(
        id=group_id,
        group_type=group_type,
        canonical_result_id=canonical_result_id,
        canonical_url=canonical_url,
        content_hash=content_hash,
        simhash=simhash,
        created_at=datetime.datetime.now(datetime.UTC)
    )
    db.add(dg)
    db.commit()
    db.refresh(dg)
    return dg

def create_dedup_member(
    db: Session,
    member_id: str,
    group_id: str,
    result_id: str,
    match_type: str,
    confidence: float = 1.0
) -> DedupMember:
    dm = DedupMember(
        id=member_id,
        group_id=group_id,
        result_id=result_id,
        match_type=match_type,
        confidence=confidence,
        created_at=datetime.datetime.now(datetime.UTC)
    )
    db.add(dm)
    db.commit()
    db.refresh(dm)
    return dm

def create_entity(
    db: Session,
    entity_id: str,
    canonical_name: str,
    entity_type: Optional[str] = None,
    description: Optional[str] = None,
    official_url: Optional[str] = None,
    wikidata_id: Optional[str] = None,
    wikipedia_url: Optional[str] = None
) -> Entity:
    ent = Entity(
        id=entity_id,
        canonical_name=canonical_name,
        entity_type=entity_type,
        description=description,
        official_url=official_url,
        wikidata_id=wikidata_id,
        wikipedia_url=wikipedia_url,
        created_at=datetime.datetime.now(datetime.UTC),
        updated_at=datetime.datetime.now(datetime.UTC)
    )
    db.add(ent)
    db.commit()
    db.refresh(ent)
    return ent

def get_entity_by_wikidata_id(db: Session, wikidata_id: str) -> Optional[Entity]:
    return db.query(Entity).filter(Entity.wikidata_id == wikidata_id).first()

def create_entity_alias(
    db: Session,
    alias_id: str,
    entity_id: str,
    alias: str,
    source: Optional[str] = None,
    confidence: float = 1.0
) -> EntityAlias:
    ea = EntityAlias(
        id=alias_id,
        entity_id=entity_id,
        alias=alias,
        language="en",
        source=source,
        confidence=confidence
    )
    db.add(ea)
    db.commit()
    db.refresh(ea)
    return ea

def create_entity_link(
    db: Session,
    link_id: str,
    entity_id: str,
    result_id: str,
    mention: Optional[str] = None,
    confidence: float = 1.0,
    decision: str = "accept"
) -> EntityLink:
    el = EntityLink(
        id=link_id,
        entity_id=entity_id,
        result_id=result_id,
        mention=mention,
        confidence=confidence,
        decision=decision,
        created_at=datetime.datetime.now(datetime.UTC)
    )
    db.add(el)
    db.commit()
    db.refresh(el)
    return el


