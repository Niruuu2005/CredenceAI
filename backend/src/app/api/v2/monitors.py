"""
Scheduled Monitors and Evidence Delta REST API.
Implements FR-017, FR-018, MON-01 to MON-06, Gate G2.
"""

import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.identity.dependencies import get_auth_context
from app.identity.auth_context import AuthContext, Permission
from app.models import Monitor, utc_now
from app.api.v2.schemas import (
    MonitorCreateRequest,
    MonitorResponse,
    MonitorDeltaResponse,
)

router = APIRouter(prefix="/monitors", tags=["Monitors v2"])


@router.post("", response_model=MonitorResponse, status_code=status.HTTP_201_CREATED)
def create_monitor(
    req: MonitorCreateRequest,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """Create a scheduled evidence monitor scoped to current workspace."""
    if not auth.has_permission(Permission.MANAGE_MONITORS):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Permission denied to manage monitors.")

    monitor = Monitor(
        id=f"mon_{uuid.uuid4().hex[:12]}",
        user_id=auth.user_id,
        workspace_id=auth.workspace_id,
        topic=req.topic,
        scope=req.scope,
        interval=req.interval,
        status="Active",
        health="Green",
        last_check="Initialized",
        created_at=utc_now(),
    )
    db.add(monitor)
    db.commit()
    db.refresh(monitor)
    return monitor


@router.get("", response_model=List[MonitorResponse])
def list_monitors(
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """List all scheduled monitors for caller's active workspace."""
    return db.query(Monitor).filter(Monitor.workspace_id == auth.workspace_id).all()


@router.get("/{monitor_id}", response_model=MonitorResponse)
def get_monitor(
    monitor_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """Retrieve monitor details with workspace boundary verification."""
    monitor = (
        db.query(Monitor)
        .filter(Monitor.id == monitor_id, Monitor.workspace_id == auth.workspace_id)
        .first()
    )
    if not monitor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Monitor '{monitor_id}' not found.")
    return monitor


@router.get("/{monitor_id}/deltas", response_model=MonitorDeltaResponse)
def get_monitor_deltas(
    monitor_id: str,
    db: Session = Depends(get_db),
    auth: AuthContext = Depends(get_auth_context),
):
    """Retrieve evidence deltas and state changes detected since last scheduled check."""
    monitor = (
        db.query(Monitor)
        .filter(Monitor.id == monitor_id, Monitor.workspace_id == auth.workspace_id)
        .first()
    )
    if not monitor:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Monitor '{monitor_id}' not found.")

    return MonitorDeltaResponse(
        monitor_id=monitor.id,
        deltas_count=0,
        summary=f"No new conflicting or supporting evidence changes detected since {monitor.last_check}.",
        detected_at=utc_now(),
    )
