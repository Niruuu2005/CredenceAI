import logging
import uuid
import time
import datetime
import asyncio
from sqlalchemy.orm import Session
from app.services.repository import get_job, create_source_result, create_normalized_result
from app.services.searxng_client import SearXNGClient
from app.services.storage import StorageClient
from app.services.normalizer import normalize_searxng_payload
from app.agents.planner_agent import PlannerAgent
from app.agents.base import AgentInput
from app.services.agent_decision_logger import AgentDecisionLogger
from app.services.cache_manager import CacheManager

logger = logging.getLogger(__name__)

# Verticals handled in Iteration 0.1
HANDLED_VERTICALS = {"web", "news", "research", "entity", "company", "rag"}


def should_use_planner(query: str, vertical: str) -> bool:
    """
    Determine if a query should use the Planner Agent.
    """
    if vertical in ["web", "general"]:
        complexity_indicators = [
            "and", "or", "vs", "versus", "compare",
            "track", "monitor", "build", "research",
            "find", "analyze", "what are", "how to",
            "latest", "recent", "competitors", "alternatives",
            "breaking", "developments", "for", "in"
        ]
        
        import re
        query_lower = query.lower()
        complexity_count = 0
        for indicator in complexity_indicators:
            pattern = rf"\b{re.escape(indicator)}\b"
            if re.search(pattern, query_lower):
                complexity_count += 1
        
        if complexity_count >= 2:
            return True
        
        if len(query.split()) > 8:
            return True
    
    return False


async def invoke_planner_agent(db: Session, job_id: str, query: str) -> dict:
    """
    Invoke the Planner Agent to decompose a user goal.
    """
    logger.info(
        f"ORCHESTRATOR  STEP=PLANNING  "
        f"job_id={job_id}  "
        f"query='{query[:60]}'"
    )
    
    t_plan = time.perf_counter()
    
    try:
        planner = PlannerAgent()
        agent_input = AgentInput(
            context={"user_goal": query},
            job_id=job_id,
            user_request=query
        )
        
        decision = await planner.execute(agent_input)
        plan_ms = (time.perf_counter() - t_plan) * 1000
        
        if decision.success:
            decision_logger = AgentDecisionLogger(db)
            decision_logger.log_decision(decision)
            
            plan = decision.output_data.get("decision", {})
            
            logger.info(
                f"ORCHESTRATOR  STEP=PLANNING  STATUS=SUCCESS  "
                f"job_id={job_id}  "
                f"jobs={len(plan.get('jobs', []))}  "
                f"entities={len(plan.get('entities', []))}  "
                f"verticals={plan.get('recommended_verticals', [])}  "
                f"confidence={decision.confidence_score:.2f}  "
                f"elapsed={plan_ms:.2f}ms"
            )
            return plan
        else:
            logger.warning(
                f"ORCHESTRATOR  STEP=PLANNING  STATUS=FAILED  "
                f"job_id={job_id}  "
                f"error='{decision.error_message}'  "
                f"elapsed={plan_ms:.2f}ms"
            )
            return None
            
    except Exception as exc:
        plan_ms = (time.perf_counter() - t_plan) * 1000
        logger.error(
            f"ORCHESTRATOR  STEP=PLANNING  STATUS=ERROR  "
            f"job_id={job_id}  "
            f"error='{exc}'  "
            f"elapsed={plan_ms:.2f}ms"
        )
        return None


def route_and_execute_job(db: Session, job_id: str) -> None:
    """Full pipeline supporting Fast, Standard, and Deep latency modes."""
    t_pipeline = time.perf_counter()

    job = get_job(db, job_id)
    if not job:
        logger.error(f"ORCHESTRATOR  STATUS=JOB_NOT_FOUND  job_id={job_id}")
        raise ValueError(f"Job {job_id} not found")

    mode = (job.execution_mode or "standard").lower()
    logger.info(
        f"ORCHESTRATOR  STATUS=STARTED  "
        f"job_id={job_id}  "
        f"mode={mode}  "
        f"vertical={job.vertical}  "
        f"query='{job.input[:60]}'"
    )

    cache_manager = CacheManager()
    cache_key = f"query_cache:{job.input.strip().lower()}:{job.vertical}"

    # ── Try Cache Lookup for Fast / Standard modes ──────────────────────────
    if mode in ["fast", "standard"]:
        cached_data = cache_manager.get(cache_key)
        if cached_data:
            logger.info(f"ORCHESTRATOR  CACHE_HIT  job_id={job_id}  key={cache_key}")
            from app.services.search_index import SearchIndexClient
            search_index_client = SearchIndexClient()
            import app.services.repository as repo
            
            source_result_id = f"src_res_cache_{uuid.uuid4().hex[:12]}"
            create_source_result(
                db=db,
                source_result_id=source_result_id,
                job_id=job.id,
                source="cache",
                source_type="web",
                input_value=job.input,
                status="success",
                raw_payload_ref="cached",
                confidence=1.0,
            )

            for idx, res in enumerate(cached_data):
                res_id = f"res_cache_{uuid.uuid4().hex[:12]}_{idx}"
                repo.create_normalized_result(
                    db=db,
                    normalized_result_id=res_id,
                    job_id=job.id,
                    source_result_id=source_result_id,
                    title=res.get("title", "Cached Result"),
                    url=res.get("url", ""),
                    source=res.get("source", "cache"),
                    canonical_url=res.get("canonical_url"),
                    snippet=res.get("snippet"),
                    language=res.get("language", "en"),
                    raw_payload_ref="cached",
                )
                
                repo.create_quality_score(
                    db=db,
                    quality_score_id=f"qs_{uuid.uuid4().hex[:12]}",
                    result_id=res_id,
                    scores=res.get("quality_scores", {
                        "relevance_score": 0.9,
                        "source_reliability_score": 0.8,
                        "freshness_score": 0.8,
                        "final_trust_score": 0.85,
                        "decision": "accept"
                    })
                )
                
                # Re-index
                try:
                    res_index = {
                        "id": res_id,
                        "title": res.get("title", ""),
                        "url": res.get("url", ""),
                        "snippet": res.get("snippet", ""),
                        "source": res.get("source", "cache"),
                        "job_id": job.id,
                        "quality_score": 0.85,
                        "decision": "accept"
                    }
                    search_index_client.index_normalized_result(res_index)
                except Exception as exc:
                    logger.warning(f"ORCHESTRATOR  CACHE_INDEX_FAIL  error={exc}")

            total_ms = (time.perf_counter() - t_pipeline) * 1000
            logger.info(
                f"ORCHESTRATOR  STATUS=COMPLETED  "
                f"job_id={job_id}  (CACHE HIT PATH)  "
                f"total_elapsed={total_ms:.2f}ms"
            )
            return

    # ── Cache Miss / Deep Mode Path ───────────────────────────────────────
    # Run planner agent only in Standard or Deep mode
    plan = None
    if mode in ["standard", "deep"] and should_use_planner(job.input, job.vertical):
        try:
            plan = asyncio.run(invoke_planner_agent(db, job_id, job.input))
            if plan:
                recommended_verticals = plan.get("recommended_verticals", [])
                if recommended_verticals and recommended_verticals[0] != job.vertical:
                    job.vertical = recommended_verticals[0]
        except Exception as exc:
            logger.warning(f"ORCHESTRATOR  PLANNING_SKIPPED  error='{exc}'")

    # Fetch results from search engine
    t_fetch = time.perf_counter()
    searxng_client = SearXNGClient()
    try:
        raw_payload = searxng_client.search(job.input)
        # Fast mode: limit results for speed
        if mode == "fast" and "results" in raw_payload:
            raw_payload["results"] = raw_payload["results"][:5]
            
        n_raw = len(raw_payload.get("results", []))
        fetch_ms = (time.perf_counter() - t_fetch) * 1000
        logger.info(f"ORCHESTRATOR  FETCH_OK  results={n_raw}  elapsed={fetch_ms:.2f}ms")
    except Exception as exc:
        logger.error(f"ORCHESTRATOR  FETCH_FAILED  error='{exc}'")
        raise

    # Store raw payload
    storage_client = StorageClient()
    bucket = "raw"
    key = f"searxng/{datetime.datetime.now(datetime.UTC).strftime('%Y/%m/%d')}/{job_id}.json"
    raw_payload_ref = storage_client.upload_raw_payload(bucket, key, raw_payload)

    # Persist source result
    source_result_id = f"src_res_{uuid.uuid4().hex[:12]}"
    create_source_result(
        db=db,
        source_result_id=source_result_id,
        job_id=job.id,
        source="searxng",
        source_type="web",
        input_value=job.input,
        status="success",
        raw_payload_ref=raw_payload_ref,
        confidence=1.0,
    )

    # Normalize
    normalized_results = normalize_searxng_payload(
        raw_payload=raw_payload,
        job_id=job.id,
        raw_payload_ref=raw_payload_ref,
    )

    # Quality Scorer & Deduplication
    from app.services.quality_scorer import QualityScorer
    from app.services.deduplicator import DeduplicationService
    from app.services.entity_resolver import EntityResolver
    import app.services.repository as repo
    
    scorer = QualityScorer()
    scored_results = []
    for res in normalized_results:
        scores = scorer.score_result(job.input, res)
        res["quality_scores"] = scores
        scored_results.append(res)
        
    deduplicator = DeduplicationService()
    unique_results, db_groups = deduplicator.group_duplicates(scored_results)

    # Save to search index & DB
    from app.services.search_index import SearchIndexClient
    search_index_client = SearchIndexClient()
    entity_resolver = EntityResolver(db)

    # Persist all normalized results
    for res in scored_results:
        repo.create_normalized_result(
            db=db,
            normalized_result_id=res["id"],
            job_id=job.id,
            source_result_id=source_result_id,
            title=res["title"],
            url=res["url"],
            source=res["source"],
            canonical_url=res["canonical_url"],
            snippet=res["snippet"],
            language=res["language"],
            raw_payload_ref=res["raw_payload_ref"],
        )
        repo.create_quality_score(
            db=db,
            quality_score_id=f"qs_{uuid.uuid4().hex[:12]}",
            result_id=res["id"],
            scores=res["quality_scores"]
        )

    # Save groups
    for dg in db_groups:
        repo.create_dedup_group(
            db=db,
            group_id=dg["group_id"],
            group_type=dg["group_type"],
            canonical_result_id=dg["canonical_result_id"],
            canonical_url=dg["canonical_url"]
        )
        for dm in dg["members"]:
            repo.create_dedup_member(
                db=db,
                member_id=f"dm_{uuid.uuid4().hex[:12]}",
                group_id=dg["group_id"],
                result_id=dm["result_id"],
                match_type=dm["match_type"],
                confidence=dm["confidence"]
            )

    # Resolve entities & index
    indexed_ok = 0
    for res in unique_results:
        if mode in ["standard", "deep"]:
            try:
                entity_resolver.resolve_and_link_entities(
                    result_id=res["id"],
                    title=res["title"],
                    snippet=res["snippet"]
                )
            except Exception as exc:
                logger.warning(f"ORCHESTRATOR  ENTITY_RESOLUTION_FAIL  error={exc}")

        if res["quality_scores"]["decision"] != "reject":
            try:
                res_index = {
                    "id": res["id"],
                    "title": res["title"],
                    "url": res["url"],
                    "snippet": res["snippet"],
                    "source": res["source"],
                    "job_id": res["job_id"],
                    "quality_score": res["quality_scores"]["final_trust_score"],
                    "decision": res["quality_scores"]["decision"]
                }
                search_index_client.index_normalized_result(res_index)
                indexed_ok += 1
            except Exception as exc:
                logger.warning(f"ORCHESTRATOR  INDEX_FAIL  error={exc}")

    # ── Deep Mode Crawl & Agent Validation ────────────────────────────────
    if mode == "deep":
        logger.info(f"ORCHESTRATOR  DEEP_MODE_PROCESSING  job_id={job_id}")
        # Run background crawl tasks for top 3 accepted results
        from app.services.crawler_task import crawl_web_page
        
        top_urls = [res["url"] for res in unique_results if res["quality_scores"]["decision"] == "accept"][:3]
        for url in top_urls:
            try:
                # Synchronous trigger in worker pipeline for deep analysis
                crawl_web_page(job_id=job_id, url=url)
            except Exception as exc:
                logger.warning(f"ORCHESTRATOR  DEEP_CRAWL_FAIL  url={url}  error={exc}")

    # Cache successful results
    try:
        cache_manager.set(cache_key, scored_results, ttl_seconds=3600)
    except Exception as exc:
        logger.warning(f"ORCHESTRATOR  CACHE_SET_FAIL  error={exc}")

    total_ms = (time.perf_counter() - t_pipeline) * 1000
    logger.info(
        f"ORCHESTRATOR  STATUS=COMPLETED  "
        f"job_id={job_id}  "
        f"total_elapsed={total_ms:.2f}ms"
    )
