import datetime
import logging
import time
import uuid
from celery import Celery
from kombu import Queue, Exchange
from app.config import settings
from app.database import SessionLocal
from app.services.repository import update_job_status, get_job
from app.utils.redis_ssl import celery_ssl_options, is_rediss_url

logger = logging.getLogger(__name__)

_broker_url = settings.celery_broker_url
_backend_url = settings.celery_result_backend

celery_app = Celery(
    "credenceai",
    broker=_broker_url,
    backend=_backend_url,
)

_celery_conf: dict = {
    "task_always_eager": settings.CELERY_ALWAYS_EAGER,
    "task_eager_propagates": settings.CELERY_ALWAYS_EAGER,
    "task_default_queue": "default",
    "task_queues": (
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("crawling", Exchange("crawling"), routing_key="crawling"),
        Queue("dlq", Exchange("dlq"), routing_key="dlq"),
    ),
    "task_routes": {
        "app.services.crawler_task.*": {"queue": "crawling"},
        "app.worker.process_job": {"queue": "default"},
    },
}

if is_rediss_url(_broker_url):
    _ssl_opts = celery_ssl_options(_broker_url, settings.REDIS_SSL_CERT_REQS)
    _celery_conf["broker_use_ssl"] = _ssl_opts
if is_rediss_url(_backend_url):
    _celery_conf["redis_backend_use_ssl"] = celery_ssl_options(
        _backend_url, settings.REDIS_SSL_CERT_REQS
    )

celery_app.conf.update(**_celery_conf)



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


@celery_app.task(name="app.worker.sync_monitors")
def sync_monitors():
    """Periodic task: enqueue search jobs for all active monitors."""
    from app.models import Monitor
    from app.models import MonitorJob
    from app.services.repository import create_job

    db = get_db_session()
    try:
        monitors = db.query(Monitor).filter(Monitor.status == "Active").all()
        for mon in monitors:
            job_id = f"job_{uuid.uuid4().hex[:12]}"
            create_job(
                db=db,
                job_id=job_id,
                trace_id=f"beat_{mon.id}",
                job_type="search_query",
                input_val=mon.topic,
                vertical="news",
                user_id=mon.user_id,
            )
            db.add(MonitorJob(
                id=f"mj_{uuid.uuid4().hex[:10]}",
                monitor_id=mon.id,
                job_id=job_id,
            ))
            mon.last_check = datetime.datetime.now(datetime.UTC).strftime("%Y-%m-%d %H:%M UTC")
            process_job.delay(job_id)
        db.commit()
        logger.info("WORKER  MONITOR_SYNC  count=%d", len(monitors))
    except Exception as exc:
        logger.exception("WORKER  MONITOR_SYNC_FAILED  error=%s", exc)
        db.rollback()
    finally:
        db.close()


celery_app.conf.beat_schedule = {
    "sync-monitors-daily": {
        "task": "app.worker.sync_monitors",
        "schedule": 86400.0,
    },
}

# Import other task modules to ensure registration
import app.services.crawler_task
