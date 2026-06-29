import datetime
import logging
import time
from celery import Celery
from kombu import Queue, Exchange
from app.config import settings
from app.database import SessionLocal
from app.services.repository import update_job_status, get_job

logger = logging.getLogger(__name__)

celery_app = Celery(
    "credenceai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery_app.conf.update(
    task_always_eager=settings.CELERY_ALWAYS_EAGER,
    task_eager_propagates=True,
    task_default_queue="default",
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("crawling", Exchange("crawling"), routing_key="crawling"),
        Queue("dlq", Exchange("dlq"), routing_key="dlq"),
    ),
    task_routes={
        "app.services.crawler_task.*": {"queue": "crawling"},
        "app.worker.process_job": {"queue": "default"},
    }
)



def get_db_session():
    return SessionLocal()


@celery_app.task(name="app.worker.process_job")
def process_job(job_id: str):
    """Execute a single job through the full pipeline. Logs all state transitions."""
    t0 = time.perf_counter()
    logger.info(
        f"WORKER  STATUS=RECEIVED  job_id={job_id}"
    )

    db = get_db_session()
    try:
        # queued -> running
        update_job_status(db, job_id, "running")
        logger.info(
            f"WORKER  STATUS=RUNNING  job_id={job_id}"
        )

        from app.services.orchestrator import route_and_execute_job
        route_and_execute_job(db, job_id)

        # running -> completed
        completed_at = datetime.datetime.now(datetime.UTC)
        update_job_status(db, job_id, "completed", completed_at=completed_at)
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.info(
            f"WORKER  STATUS=COMPLETED  "
            f"job_id={job_id}  "
            f"elapsed={elapsed_ms:.2f}ms"
        )

    except Exception as exc:
        elapsed_ms = (time.perf_counter() - t0) * 1000
        logger.error(
            f"WORKER  STATUS=FAILED  "
            f"job_id={job_id}  "
            f"error='{exc}'  "
            f"elapsed={elapsed_ms:.2f}ms",
            exc_info=True,
        )
        update_job_status(
            db,
            job_id,
            "failed",
            completed_at=datetime.datetime.now(datetime.UTC),
            error_message=str(exc),
        )
    finally:
        db.close()
        logger.debug(f"WORKER  STATUS=DB_SESSION_CLOSED  job_id={job_id}")

# Import other task modules to ensure registration
import app.services.crawler_task
