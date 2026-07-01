import uuid
import logging
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database import get_db
from app.config import settings
from app.models import User
from app.schemas import JobStatusResponse, QualitySummary
from app.services.repository import create_job, get_job, get_job_normalized_results
from app.services.orchestrator import invoke_planner_agent
from app.services.security import get_current_user
from app.services.quota_service import check_job_quota
from app.worker import process_job

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/goals", tags=["Goals"])

# With CELERY_ALWAYS_EAGER, each process_job.delay() runs inline — cap to avoid proxy timeouts.
MAX_EAGER_GOAL_JOBS = 1


def _map_db_status(db_status: str) -> str:
    if db_status == "queued":
        return "submitted"
    if db_status == "running":
        return "processing"
    return db_status


def _job_status_response(db: Session, job_id: str) -> JobStatusResponse:
    """Build job status from DB after process_job (eager or async)."""
    job = get_job(db, job_id)
    if not job:
        raise HTTPException(status_code=500, detail="Job record missing after submit")

    results = get_job_normalized_results(db, job_id)
    accepted = rejected = manual_review = 0
    for r in results:
        if r.quality_scores:
            dec = r.quality_scores.decision
            if dec == "accept":
                accepted += 1
            elif dec == "reject":
                rejected += 1
            elif dec == "review":
                manual_review += 1
        else:
            accepted += 1

    return JobStatusResponse(
        job_id=job.id,
        status=_map_db_status(job.status),
        results_count=len(results),
        failed_events=0,
        quality_summary=QualitySummary(
            accepted=accepted, rejected=rejected, manual_review=manual_review
        ),
        created_at=job.created_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        job_type=job.job_type,
        input=job.input,
        submitted_at=job.created_at,
    )

class GoalCreate(BaseModel):
    goal: str
    vertical: Optional[str] = "general"

class GoalResponse(BaseModel):
    goal: str
    plan_id: str
    jobs: List[JobStatusResponse]

@router.post("", response_model=GoalResponse, status_code=200)
async def submit_goal(
    goal_in: GoalCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    user_id = current_user.id
    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    logger.info(
        "API POST /goals RECEIVED user_id=%s plan_id=%s goal_preview=%r",
        user_id,
        plan_id,
        goal_in.goal[:60],
    )

    try:
        check_job_quota(db, current_user)

        if not goal_in.goal or len(goal_in.goal.strip()) < 3:
            raise HTTPException(
                status_code=400,
                detail="Goal must be a non-empty string with at least 3 characters",
            )

        plan = await invoke_planner_agent(db, plan_id, goal_in.goal)

        job_defs = plan.get("jobs", []) if plan else []
        if settings.CELERY_ALWAYS_EAGER and len(job_defs) > MAX_EAGER_GOAL_JOBS:
            logger.warning(
                "API GOAL_PLAN plan_id=%s capping jobs %d -> %d (CELERY_ALWAYS_EAGER)",
                plan_id,
                len(job_defs),
                MAX_EAGER_GOAL_JOBS,
            )
            job_defs = job_defs[:MAX_EAGER_GOAL_JOBS]

        jobs_out = []
        if plan and job_defs:
            logger.info(
                "API GOAL_PLAN plan_id=%s decomposed_jobs=%d",
                plan_id,
                len(job_defs),
            )
            for job_def in job_defs:
                job_id = f"job_{uuid.uuid4().hex[:12]}"

                input_val = None
                params = job_def.get("parameters") or {}
                if "query" in params:
                    input_val = params["query"]
                elif "entity" in params:
                    input_val = params["entity"]
                elif "topic" in params:
                    input_val = params["topic"]

                if not input_val:
                    input_val = job_def.get("description", goal_in.goal)

                job_type = job_def.get("job_type") or "search_query"
                if job_type == "search":
                    job_type = "search_query"

                vertical = params.get("vertical") or goal_in.vertical or "general"
                priority = "high" if job_def.get("priority", 1) == 1 else "normal"

                db_job = create_job(
                    db=db,
                    job_id=job_id,
                    trace_id=plan_id,
                    job_type=job_type,
                    input_val=input_val,
                    vertical=vertical,
                    priority=priority,
                    user_id=user_id,
                )

                process_job.delay(db_job.id)
                db.expire_all()
                jobs_out.append(_job_status_response(db, db_job.id))
        else:
            logger.warning(
                "API GOAL_PLAN plan_id=%s planning_failed using_search_fallback",
                plan_id,
            )
            job_id = f"job_{uuid.uuid4().hex[:12]}"
            db_job = create_job(
                db=db,
                job_id=job_id,
                trace_id=plan_id,
                job_type="search_query",
                input_val=goal_in.goal,
                vertical=goal_in.vertical or "general",
                user_id=user_id,
            )

            process_job.delay(db_job.id)
            db.expire_all()
            jobs_out.append(_job_status_response(db, db_job.id))

        logger.info("API POST /goals OK plan_id=%s jobs_submitted=%d", plan_id, len(jobs_out))
        return GoalResponse(goal=goal_in.goal, plan_id=plan_id, jobs=jobs_out)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            "API POST /goals FAILED plan_id=%s user_id=%s error=%s",
            plan_id,
            user_id,
            exc,
        )
        raise HTTPException(status_code=500, detail="Failed to submit goal. Please try again.") from exc
