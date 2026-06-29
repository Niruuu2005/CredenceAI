import uuid
from typing import List
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Monitor, User
from app.services.security import get_current_user
from app.services.quota_service import check_monitor_quota
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
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db_monitor = _get_user_monitor(db, monitor_id, current_user.id)
    db_monitor.last_check = "Just now"
    db_monitor.health = "Green"
    db.commit()
    db.refresh(db_monitor)
    return db_monitor
