"""Dispatch job processing without blocking HTTP when CELERY_ALWAYS_EAGER."""
from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from app.config import settings

if TYPE_CHECKING:
    from fastapi import BackgroundTasks

logger = logging.getLogger(__name__)


class JobEnqueueError(Exception):
    """Raised when a job cannot be enqueued to Celery."""

    def __init__(self, job_id: str, cause: Exception):
        self.job_id = job_id
        self.cause = cause
        super().__init__(str(cause))


def _run_process_job(job_id: str) -> None:
    from app.worker import process_job

    logger.info("DISPATCH background job_id=%s", job_id)
    process_job.run(job_id)


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
                    daemon=True,
                ).start()
        else:
            process_job.delay(job_id)
    except Exception as exc:
        logger.exception("Failed to enqueue job_id=%s", job_id)
        raise JobEnqueueError(job_id, exc) from exc
