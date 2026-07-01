"""Dispatch job processing without blocking HTTP when CELERY_ALWAYS_EAGER."""
from __future__ import annotations

import logging
import threading
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from fastapi import BackgroundTasks
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

STALE_JOB_AGE_SEC = 180
LAZY_REDISPATCH_AGE_SEC = 60


class JobEnqueueError(Exception):
    """Raised when a job cannot be enqueued to Celery."""

    def __init__(self, job_id: str, cause: Exception):
        self.job_id = job_id
        self.cause = cause
        super().__init__(str(cause))


def _run_process_job(job_id: str) -> None:
    from app.worker import process_job

    logger.info("DISPATCH background job_id=%s", job_id)
    try:
        process_job.run(job_id)
    except Exception:
        logger.exception("DISPATCH failed job_id=%s", job_id)


def dispatch_process_job(
    job_id: str,
    background_tasks: BackgroundTasks | None = None,
) -> None:
    """Queue process_job after the response when eager; else use Celery worker."""
    from app.worker import process_job

    try:
        if settings.CELERY_ALWAYS_EAGER:
            if background_tasks is not None:
                background_tasks.add_task(_run_process_job, job_id)
            else:
                threading.Thread(
                    target=_run_process_job,
                    args=(job_id,),
                    name=f"process_job-{job_id}",
                    daemon=False,
                ).start()
        else:
            process_job.delay(job_id)
    except Exception as exc:
        logger.exception("Failed to enqueue job_id=%s", job_id)
        raise JobEnqueueError(job_id, exc) from exc


def recover_stale_jobs(db: Session, max_age_sec: int = STALE_JOB_AGE_SEC) -> int:
    """Re-dispatch queued/running jobs older than max_age_sec (startup recovery)."""
    from app.models import Job

    cutoff = datetime.now(timezone.utc) - timedelta(seconds=max_age_sec)
    stale = (
        db.query(Job)
        .filter(Job.status.in_(("queued", "running")))
        .filter(Job.created_at < cutoff)
        .all()
    )
    count = 0
    for job in stale:
        logger.warning(
            "STALE_JOB_RECOVERY job_id=%s status=%s created_at=%s",
            job.id,
            job.status,
            job.created_at,
        )
        dispatch_process_job(job.id, background_tasks=None)
        count += 1
    if count:
        logger.info("STALE_JOB_RECOVERY re-dispatched %d job(s)", count)
    return count


def maybe_redispatch_stale_job(db: Session, job_id: str) -> bool:
    """Lazy recovery: re-dispatch a queued job stuck longer than LAZY_REDISPATCH_AGE_SEC."""
    from app.models import Job

    job = db.query(Job).filter(Job.id == job_id).first()
    if not job or job.status != "queued":
        return False

    created = job.created_at
    if created.tzinfo is None:
        created = created.replace(tzinfo=timezone.utc)
    age_sec = (datetime.now(timezone.utc) - created).total_seconds()
    if age_sec < LAZY_REDISPATCH_AGE_SEC:
        return False

    logger.warning(
        "LAZY_JOB_REDISPATCH job_id=%s age_sec=%.0f",
        job_id,
        age_sec,
    )
    dispatch_process_job(job_id, background_tasks=None)
    return True
