from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.storage import StorageClient
from app.services.search_index import SearchIndexClient
from app.config import settings
from app.schemas import SystemMetricsResponse
from typing import Dict, Any
import redis

router = APIRouter(tags=["System Status"])

def _check_redis() -> str:
    try:
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=2)
        r.ping()
        return "healthy"
    except Exception as e:
        return f"unhealthy: {str(e)[:80]}"

@router.get("/health")
def health_check(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Returns connectivity status for database, object storage, search index, and Redis."""

    db_status = "unhealthy"
    try:
        db.execute(text("SELECT 1"))
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)[:80]}"

    redis_status = _check_redis()

    storage = StorageClient()
    storage_status = "healthy (MinIO)" if storage.use_s3 else "degraded (local fallback)"

    search = SearchIndexClient()
    search_status = "healthy (OpenSearch)" if search.use_opensearch else "degraded (SQLite fallback)"

    from app.services.health_router import HealthRouter
    hr = HealthRouter()
    provider_status = hr.get_status_report()

    overall = "online" if db_status == "healthy" else "offline"
    
    dependencies = {
        "database": "ok" if db_status == "healthy" else "error",
        "cache": "ok" if redis_status == "healthy" else "error",
        "storage": "ok" if storage.use_s3 else "degraded",
    }

    return {
        "status": "ok" if overall == "online" else "error",
        "overall": overall,
        "version": settings.API_VERSION if hasattr(settings, "API_VERSION") else "0.5.0",
        "dependencies": dependencies,
        "mock_mode": settings.MOCK_SERVICES,
        "components": {
            "database": db_status,
            "redis": redis_status,
            "object_storage": storage_status,
            "search_index": search_status,
        },
        "providers": provider_status
    }


@router.get("/system/metrics", response_model=SystemMetricsResponse)
def get_system_metrics(db: Session = Depends(get_db)):
    """Retrieve database metrics, quality decision counts, and agent invocation statistics."""
    from app.models import Job, NormalizedResult, QualityScore
    from app.services.agent_decision_logger import AgentDecisionLogger
    from app.schemas import DecisionStatsResponse, SystemMetricsResponse
    
    jobs_count = db.query(Job).count()
    results_count = db.query(NormalizedResult).count()
    
    accepted_count = db.query(QualityScore).filter(QualityScore.decision == "accept").count()
    review_count = db.query(QualityScore).filter(QualityScore.decision == "review").count()
    rejected_count = db.query(QualityScore).filter(QualityScore.decision == "reject").count()
    
    # Extract agent decisions
    logger = AgentDecisionLogger(db)
    stats = logger.get_decision_stats()
    
    overall = "healthy"
    try:
        db.execute(text("SELECT 1"))
    except Exception:
        overall = "unhealthy"
        
    decision_stats = DecisionStatsResponse(
        total_decisions=stats.get("total_decisions", 0),
        successful=stats.get("successful", 0),
        failed=stats.get("failed", 0),
        success_rate=stats.get("success_rate", 0.0),
        avg_confidence=stats.get("avg_confidence", 0.0),
        avg_execution_time_ms=stats.get("avg_execution_time_ms", 0.0),
        agents_used=stats.get("agents_used", [])
    )
    
    return SystemMetricsResponse(
        status=overall,
        jobs_count=jobs_count,
        results_count=results_count,
        accepted_count=accepted_count,
        review_count=review_count,
        rejected_count=rejected_count,
        agent_decision_stats=decision_stats
    )

