"""Per-user quota checks for jobs, monitors, and collections."""
import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Job, Monitor, Collection, User

PLAN_JOB_LIMITS = {"Free": 50, "Pro": 500, "Enterprise": 5000}
PLAN_MONITOR_LIMITS = {"Free": 1, "Pro": 10, "Enterprise": 100}
PLAN_COLLECTION_LIMITS = {"Free": 3, "Pro": 20, "Enterprise": 1000}


def _period_start(user: User) -> datetime.datetime:
    if user.usage_period_start:
        return user.usage_period_start
    return user.created_at or datetime.datetime.now(datetime.timezone.utc)


def count_user_jobs_in_period(db: Session, user: User) -> int:
    start = _period_start(user)
    return (
        db.query(func.count(Job.id))
        .filter(Job.user_id == user.id, Job.created_at >= start)
        .scalar()
        or 0
    )


def check_job_quota(db: Session, user: User) -> None:
    limit = user.search_quota_limit or PLAN_JOB_LIMITS.get(user.plan, 50)
    used = count_user_jobs_in_period(db, user)
    if used >= limit:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail=f"Daily search quota reached ({used}/{limit}). Upgrade your plan or wait for the next period.",
        )


def check_monitor_quota(db: Session, user: User) -> None:
    limit = PLAN_MONITOR_LIMITS.get(user.plan, 1)
    used = db.query(Monitor).filter(Monitor.user_id == user.id).count()
    if used >= limit:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail=f"Active monitors limit reached. Limit is {limit} for the '{user.plan}' tier.",
        )


def check_collection_quota(db: Session, user: User) -> None:
    limit = PLAN_COLLECTION_LIMITS.get(user.plan, 3)
    used = db.query(Collection).filter(Collection.user_id == user.id).count()
    if used >= limit:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=403,
            detail=f"Collections limit reached. Limit is {limit} for the '{user.plan}' tier.",
        )
