import logging
from typing import Dict, Any

import redis
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.schemas import SystemMetricsResponse
from app.services.backend_selection import search_backend_label, storage_backend_label
from app.services.search_index import SearchIndexClient
from app.services.storage import StorageClient
from app.services.searxng_client import resolve_search_provider
from app.utils.redis_ssl import redis_client_kwargs

logger = logging.getLogger(__name__)

router = APIRouter(tags=["System Status"])


@router.get("/health")
def health_check() -> Dict[str, str]:
    """Liveness probe — no database or auth dependencies."""
    return {"status": "ok", "service": "credenceai-api"}


@router.options("/health")
def health_options() -> Dict[str, str]:
    """Explicit preflight handler for health checks."""
    return {"status": "ok"}


def _check_redis() -> str:
    try:
        r = redis.from_url(
            settings.redis_url,
            socket_connect_timeout=2,
            **redis_client_kwargs(settings.redis_url, settings.REDIS_SSL_CERT_REQS),
        )
        r.ping()
        return "ok"
    except Exception as e:
        return f"error: {str(e)[:80]}"


@router.get("/health/ready")
def health_ready(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Readiness probe — dependency status for operators and dashboards."""

    db_ok = False
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception as e:
        logger.error("Health ready check: database unhealthy: %s", e)

    redis_status = _check_redis()
    storage = StorageClient()
    search = SearchIndexClient()

    search_label = (
        "opensearch_ok" if search.use_opensearch else search_backend_label()
    )
    storage_label = "s3_ok" if storage.use_s3 else storage_backend_label()

    if not db_ok:
        readiness = "offline"
    elif search_label != "opensearch_ok" or storage_label != "s3_ok":
        readiness = "degraded"
    else:
        readiness = "ready"

    celery_mode = "eager" if settings.CELERY_ALWAYS_EAGER else "worker"
    worker_available = True

    payload: Dict[str, Any] = {
        "status": readiness,
        "service": "credenceai-api",
        "database": "ok" if db_ok else "error",
        "cache": redis_status,
        "search": search_label,
        "storage": storage_label,
        "celery_mode": celery_mode,
        "celery_eager": settings.CELERY_ALWAYS_EAGER,
        "worker_available": worker_available,
        "search_provider": resolve_search_provider(),
        "openai_configured": bool(settings.OPENAI_API_KEY),
        "version": settings.API_VERSION,
        "mock_mode": settings.MOCK_SERVICES,
        "components": {
            "database": "healthy" if db_ok else "unhealthy",
            "redis": "healthy" if redis_status == "ok" else redis_status,
            "object_storage": "healthy (S3)" if storage.use_s3 else "degraded (local fallback)",
            "search_index": (
                "healthy (OpenSearch)"
                if search.use_opensearch
                else "degraded (PostgreSQL fallback)"
            ),
        },
    }

    if settings.APP_ENV == "production":
        payload["cors_origins_configured"] = len(settings.CORS_ALLOWED_ORIGINS)

    from app.services.health_router import HealthRouter

    payload["providers"] = HealthRouter().get_status_report()

    return payload


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

    logger_svc = AgentDecisionLogger(db)
    stats = logger_svc.get_decision_stats()

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
        agents_used=stats.get("agents_used", []),
    )

    return SystemMetricsResponse(
        status=overall,
        jobs_count=jobs_count,
        results_count=results_count,
        accepted_count=accepted_count,
        review_count=review_count,
        rejected_count=rejected_count,
        agent_decision_stats=decision_stats,
    )
