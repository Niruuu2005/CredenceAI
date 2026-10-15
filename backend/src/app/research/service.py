"""
Research run lifecycle service with transactional outbox creation.
Implements FR-001, FR-002, FR-003, NFR-001, AT-01, AT-07, Gate G4.
"""

import json
import uuid
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models import ResearchRun, RunStep, OutboxEvent, utc_now
from app.identity.auth_context import AuthContext, Permission


VALID_TERMINAL_STATES = {"completed", "partial", "failed", "cancelled", "timed_out"}


def create_research_run(
    db: Session,
    auth: AuthContext,
    question: str,
    mode: str = "investigate",
    filters: Optional[Dict[str, Any]] = None,
    budget: Optional[Dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
) -> tuple[ResearchRun, bool]:
    """
    Idempotently creates a research run and an outbox event in a single atomic transaction.
    Returns (run, was_created). If idempotency_key matched an existing run, returns (existing_run, False).
    """
    auth.require_permission(Permission.CREATE_RESEARCH)

    # 1. Idempotency Check (FR-002, AT-01)
    if idempotency_key:
        existing = (
            db.query(ResearchRun)
            .filter(
                ResearchRun.workspace_id == auth.workspace_id,
                ResearchRun.idempotency_key == idempotency_key,
            )
            .first()
        )
        if existing:
            return existing, False

    # 2. Instantiate ResearchRun
    run_id = f"run_{uuid.uuid4().hex[:12]}"
    budget_payload = budget or {
        "max_sources": 10,
        "max_time_seconds": 30.0,
        "max_tokens": 4000,
        "max_bytes": 5 * 1024 * 1024,
    }

    run = ResearchRun(
        id=run_id,
        workspace_id=auth.workspace_id,
        author_id=auth.user_id,
        question=question.strip(),
        mode=mode,
        status="queued",
        idempotency_key=idempotency_key,
        filters_json=json.dumps(filters or {}),
        budget_json=json.dumps(budget_payload),
        config_version="v2.0",
        created_at=utc_now(),
        updated_at=utc_now(),
    )
    db.add(run)

    # 3. Create Initial RunStep
    initial_step = RunStep(
        id=f"step_{uuid.uuid4().hex[:10]}",
        run_id=run.id,
        step_key="planning",
        state="pending",
        input_version="v1",
        created_at=utc_now(),
    )
    db.add(initial_step)

    # 4. Atomic Outbox Event (NFR-001)
    outbox_event = OutboxEvent(
        id=f"evt_{uuid.uuid4().hex[:12]}",
        aggregate_type="research_run",
        aggregate_id=run.id,
        event_type="research_run.created",
        payload_json=json.dumps({
            "run_id": run.id,
            "workspace_id": run.workspace_id,
            "question": run.question,
            "mode": run.mode,
            "budget": budget_payload,
        }),
        status="pending",
        created_at=utc_now(),
    )
    db.add(outbox_event)

    # Single atomic commit
    db.commit()
    db.refresh(run)
    return run, True


def get_research_run(db: Session, auth: AuthContext, run_id: str) -> ResearchRun:
    """
    Fetch run strictly scoped by the authorized workspace.
    """
    auth.require_permission(Permission.READ_RESEARCH)
    run = (
        db.query(ResearchRun)
        .filter(
            ResearchRun.id == run_id,
            ResearchRun.workspace_id == auth.workspace_id,
        )
        .first()
    )
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Research run '{run_id}' not found in workspace '{auth.workspace_id}'.",
        )
    return run


def cancel_research_run(db: Session, auth: AuthContext, run_id: str) -> ResearchRun:
    """
    Cancel an in-progress research run. (AT-07, RUN-11).
    """
    auth.require_permission(Permission.CANCEL_RESEARCH)
    run = get_research_run(db, auth, run_id)

    if run.status in VALID_TERMINAL_STATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel run '{run_id}' because it is already in terminal state '{run.status}'.",
        )

    run.status = "cancelled"
    run.updated_at = utc_now()
    run.completed_at = utc_now()

    # Emit outbox cancellation event
    outbox_event = OutboxEvent(
        id=f"evt_{uuid.uuid4().hex[:12]}",
        aggregate_type="research_run",
        aggregate_id=run.id,
        event_type="research_run.cancelled",
        payload_json=json.dumps({"run_id": run.id, "workspace_id": run.workspace_id}),
        status="pending",
        created_at=utc_now(),
    )
    db.add(outbox_event)
    db.commit()
    db.refresh(run)
    return run


def list_workspace_runs(
    db: Session,
    auth: AuthContext,
    limit: int = 20,
    offset: int = 0,
) -> List[ResearchRun]:
    """
    List runs strictly filtered by the authenticated workspace.
    """
    auth.require_permission(Permission.READ_RESEARCH)
    return (
        db.query(ResearchRun)
        .filter(ResearchRun.workspace_id == auth.workspace_id)
        .order_by(ResearchRun.created_at.desc())
        .offset(offset)
        .limit(min(limit, 100))
        .all()
    )
