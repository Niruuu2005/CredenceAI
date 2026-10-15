import uuid
from typing import List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.database import get_db
from app.models import Monitor, User, MonitorJob, Job
from app.services.security import get_current_user
from app.services.quota_service import check_monitor_quota
from app.services.repository import create_job
from app.services.job_dispatch import dispatch_process_job, JobEnqueueError
from app.schemas import MonitorCreate, MonitorResponse

router = APIRouter(prefix="/monitors", tags=["Monitors"])


def _get_user_monitor(db: Session, monitor_id: str, user_id: str) -> Monitor:
    monitor = (
        db.query(Monitor)
        .filter(Monitor.id == monitor_id, Monitor.user_id == user_id)
        .first()
    )
    if not monitor:
        raise HTTPException(status_code=404, detail="Monitor not found")
    return monitor


@router.get("", response_model=List[MonitorResponse])
def list_monitors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Monitor)
        .filter(Monitor.user_id == current_user.id)
        .order_by(Monitor.created_at.desc())
        .all()
    )


@router.post("", response_model=MonitorResponse, status_code=201)
def create_monitor(
    request: MonitorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    check_monitor_quota(db, current_user)

    monitor_id = f"mon-{uuid.uuid4().hex[:8]}"
    db_monitor = Monitor(
        id=monitor_id,
        user_id=current_user.id,
        topic=request.topic,
        scope=request.scope or "Web & News Indexes",
        interval=request.interval or "Daily",
        status="Active",
        last_check="Just created",
        health="Green",
    )
    db.add(db_monitor)
    db.commit()
    db.refresh(db_monitor)
    return db_monitor


@router.get("/{monitor_id}", response_model=MonitorResponse)
def get_monitor(
    monitor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return _get_user_monitor(db, monitor_id, current_user.id)


@router.delete("/{monitor_id}")
def delete_monitor(
    monitor_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_monitor = _get_user_monitor(db, monitor_id, current_user.id)
    db.delete(db_monitor)
    db.commit()
    return {"message": "Monitor deleted successfully"}


@router.post("/{monitor_id}/sync", response_model=MonitorResponse)
def sync_monitor(
    monitor_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_monitor = _get_user_monitor(db, monitor_id, current_user.id)

    job_id = f"job_{uuid.uuid4().hex[:12]}"
    trace_id = f"mon_sync_{monitor_id}"

    create_job(
        db=db,
        job_id=job_id,
        trace_id=trace_id,
        job_type="search_query",
        input_val=db_monitor.topic,
        vertical="news",
        priority="normal",
        user_id=current_user.id,
    )

    try:
        dispatch_process_job(job_id, background_tasks)
    except JobEnqueueError as exc:
        raise HTTPException(status_code=503, detail="Failed to enqueue monitor sync job") from exc

    monitor_job = MonitorJob(
        id=f"mj_{uuid.uuid4().hex[:10]}",
        monitor_id=monitor_id,
        job_id=job_id,
    )
    db.add(monitor_job)

    db_monitor.last_check = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    db_monitor.health = "Syncing"
    db.commit()
    db.refresh(db_monitor)
    return db_monitor
