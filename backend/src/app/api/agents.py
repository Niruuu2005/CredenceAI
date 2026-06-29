from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models import User
from app.services.security import get_current_user
from app.services.agent_decision_logger import AgentDecisionRecord, AgentDecisionLogger
from app.schemas import AgentDecisionResponse

router = APIRouter(prefix="/agent/decisions", tags=["Agent Decisions"])

@router.get("", response_model=List[AgentDecisionResponse])
def get_agent_decisions(
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    agent_name: Optional[str] = Query(None, description="Filter by agent name"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get agent decisions, optionally filtered by job ID, agent name, or success."""
    query = db.query(AgentDecisionRecord)
    if job_id:
        query = query.filter(AgentDecisionRecord.job_id == job_id)
    if agent_name:
        query = query.filter(AgentDecisionRecord.agent_name == agent_name)
    if success is not None:
        query = query.filter(AgentDecisionRecord.success == success)
        
    records = query.order_by(AgentDecisionRecord.timestamp.desc()).offset(offset).limit(limit).all()
    return records

@router.get("/{job_id}", response_model=List[AgentDecisionResponse])
def get_decisions_for_job(
    job_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all agent decisions for a specific job."""
    logger = AgentDecisionLogger(db)
    records = logger.get_decisions_by_job(job_id)
    return records
