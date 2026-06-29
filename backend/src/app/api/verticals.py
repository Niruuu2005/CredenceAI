import json
import uuid
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import VerticalRun, User
from app.services.security import get_current_user
from app.schemas import VerticalPackInfo, VerticalRunResponse, VerticalRunCreate
from app.verticals import (
    CompanyVerticalPack,
    ResearchVerticalPack,
    NewsMonitoringPack,
    RAGDatasetBuilderPack
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/verticals", tags=["Vertical Packs"])

VERTICAL_PACKS = {
    "company": CompanyVerticalPack,
    "research": ResearchVerticalPack,
    "news": NewsMonitoringPack,
    "rag": RAGDatasetBuilderPack
}

def _map_run_to_response(run: VerticalRun) -> VerticalRunResponse:
    report_dict = None
    if run.report:
        try:
            report_dict = json.loads(run.report)
        except Exception as e:
            logger.error(f"Failed to parse report JSON: {e}")
    return VerticalRunResponse(
        run_id=run.id,
        pack_name=run.pack_name,
        query=run.query,
        status=run.status,
        created_at=run.created_at,
        completed_at=run.completed_at,
        report=report_dict,
        error_message=run.error_message
    )

@router.get("", response_model=List[VerticalPackInfo])
def list_vertical_packs(current_user: User = Depends(get_current_user)):
    """List all available Vertical Intelligence Packs."""
    return [
        VerticalPackInfo(name="company", description="Company Profile & Competitor Intelligence Pack", enabled=True),
        VerticalPackInfo(name="research", description="Academic Research Paper & Citation Discovery Pack", enabled=True),
        VerticalPackInfo(name="news", description="Breaking Event Detection & News Source Diversity Monitoring Pack", enabled=True),
        VerticalPackInfo(name="rag", description="Curated Dataset JSONL Builder & Embedding Pack", enabled=True)
    ]

@router.post("/{pack_name}/run", response_model=VerticalRunResponse, status_code=202)
async def run_vertical_pack(
    pack_name: str,
    run_in: VerticalRunCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Trigger a workflow execution for a specified vertical pack."""
    pack_class = VERTICAL_PACKS.get(pack_name.lower())
    if not pack_class:
        raise HTTPException(status_code=404, detail=f"Vertical pack '{pack_name}' not found")
        
    run_id = f"vrun_{uuid.uuid4().hex[:12]}"
    
    # Register the run record
    db_run = VerticalRun(
        id=run_id,
        pack_name=pack_name.lower(),
        query=run_in.query,
        status="running",
        created_at=datetime.now(timezone.utc)
    )
    db.add(db_run)
    db.commit()
    
    # Instantiate and run
    pack = pack_class()
    if run_in.config:
        pack.configure(run_in.config)
        
    try:
        run_data = await pack.execute(run_in.query, db)
        report = pack.generate_report(run_data)
        
        db_run.report = json.dumps(report)
        db_run.status = "completed"
        db_run.completed_at = datetime.now(timezone.utc)
        db.commit()
    except Exception as e:
        logger.exception("Vertical pack run failed")
        db_run.status = "failed"
        db_run.error_message = str(e)
        db_run.completed_at = datetime.now(timezone.utc)
        db.commit()
        
    db.refresh(db_run)
    return _map_run_to_response(db_run)

@router.get("/{pack_name}/runs/{run_id}", response_model=VerticalRunResponse)
def get_vertical_run(
    pack_name: str,
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve status and metadata of a vertical pack run."""
    run = db.query(VerticalRun).filter(VerticalRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Vertical run not found")
    return _map_run_to_response(run)

@router.get("/{pack_name}/runs/{run_id}/report")
def get_vertical_run_report(
    pack_name: str,
    run_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Retrieve the synthesized intelligence report from a completed vertical pack run."""
    run = db.query(VerticalRun).filter(VerticalRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Vertical run not found")
    if run.status != "completed":
        raise HTTPException(status_code=400, detail=f"Run report is not ready (status: {run.status})")
        
    try:
        return json.loads(run.report)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to parse report: {e}")
