"""
Unit and integration tests for Research Run lifecycle, transactional outbox, and execution pipeline.
Verifies FR-002, FR-003, NFR-001, NFR-002, AT-01, AT-07, Release Gate G4.
"""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, Tenant, Workspace, User, Membership, ResearchRun, RunStep, OutboxEvent, Report
from app.identity.auth_context import AuthContext, WorkspaceRole, Permission, ROLE_PERMISSIONS
from app.research.service import create_research_run, get_research_run, cancel_research_run, list_workspace_runs
from app.research.outbox_dispatcher import OutboxDispatcher
from app.research.pipeline import execute_research_run
from app.sources.registry import SourceRegistry
from app.sources.protocol import SourceAdapter, AdapterManifest, AdapterHit, AdapterResponse, SourceClass


class MockPipelineAdapter(SourceAdapter):
    def __init__(self, source_id: str, source_class: SourceClass):
        self._manifest = AdapterManifest(
            source_id=source_id,
            version="1.0",
            name=f"Mock {source_id}",
            source_class=source_class,
        )

    @property
    def manifest(self):
        return self._manifest

    async def health_check(self):
        return True

    async def search(self, query: str, filters=None, budget=None):
        return AdapterResponse(
            source_id=self._manifest.source_id,
            hits=[
                AdapterHit(
                    url=f"https://{self._manifest.source_id}.org/evidence1",
                    title="Economic Policy Analysis 2026",
                    snippet=f"Official statistics establish attendance increased by 12% following the policy update. Query: {query}",
                    publisher="State Bureau of Statistics",
                    source_class=self._manifest.source_class,
                )
            ],
            latency_ms=10.0,
            success=True,
            coverage_notes=["Successfully retrieved corroborating data"],
        )


@pytest.fixture
def pipeline_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()

    tenant = Tenant(id="tenant_p1", name="Testing NGO")
    ws = Workspace(id="ws_p1", tenant_id="tenant_p1", name="Policy Research")
    user = User(id="user_p1", email="researcher@ngo.org", name="Lead Researcher")
    mem = Membership(id="mem_p1", user_id="user_p1", workspace_id="ws_p1", role="researcher")
    db.add_all([tenant, ws, user, mem])
    db.commit()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_ctx():
    return AuthContext(
        user_id="user_p1",
        tenant_id="tenant_p1",
        workspace_id="ws_p1",
        role=WorkspaceRole.RESEARCHER,
        permissions=set(ROLE_PERMISSIONS[WorkspaceRole.RESEARCHER]),
    )


def test_at_01_idempotent_run_creation(pipeline_db, auth_ctx):
    """
    ACCEPTANCE TEST AT-01:
    Researcher submits same request twice with identical idempotency_key.
    Must return the same logical run without duplication.
    """
    key = "unique-idempotency-key-12345"
    question = "Did the local education policy improve school attendance in 2026?"

    run1, created1 = create_research_run(
        db=pipeline_db,
        auth=auth_ctx,
        question=question,
        idempotency_key=key,
    )
    assert created1 is True
    assert run1.id.startswith("run_")

    run2, created2 = create_research_run(
        db=pipeline_db,
        auth=auth_ctx,
        question=question,
        idempotency_key=key,
    )
    assert created2 is False
    assert run1.id == run2.id

    # Verify database has exactly 1 run record with this idempotency key
    count = pipeline_db.query(ResearchRun).filter(ResearchRun.idempotency_key == key).count()
    assert count == 1


def test_transactional_outbox_atomicity(pipeline_db, auth_ctx):
    """
    NFR-001 & DATA-08:
    ResearchRun and OutboxEvent must be committed atomically in the same transaction.
    """
    run, created = create_research_run(
        db=pipeline_db,
        auth=auth_ctx,
        question="Analysis of solar tariff reforms",
    )
    assert created is True

    # Check outbox event exists
    outbox_event = (
        pipeline_db.query(OutboxEvent)
        .filter(OutboxEvent.aggregate_id == run.id)
        .first()
    )
    assert outbox_event is not None
    assert outbox_event.event_type == "research_run.created"
    assert outbox_event.status == "pending"

    # Verify OutboxDispatcher processes the event
    dispatched = []
    dispatcher = OutboxDispatcher(handler=lambda evt, db: dispatched.append(evt.aggregate_id))
    processed = dispatcher.process_pending_events(pipeline_db)

    assert processed == 1
    assert run.id in dispatched
    pipeline_db.refresh(outbox_event)
    assert outbox_event.status == "dispatched"
    assert outbox_event.processed_at is not None


@pytest.mark.asyncio
async def test_full_pipeline_execution_and_frozen_report(pipeline_db, auth_ctx):
    """
    End-to-end pipeline execution:
    planning -> retrieving -> extracting -> verifying -> reporting -> completed
    Verifies Gate G4, Gate G5, Gate G6, Gate G7.
    """
    from app.sources.router import SourceRouter

    registry = SourceRegistry()
    registry.register(MockPipelineAdapter("stat_bureau", SourceClass.REFERENCE))
    router = SourceRouter(registry)

    run, _ = create_research_run(
        db=pipeline_db,
        auth=auth_ctx,
        question="Did the attendance policy work?",
    )

    completed_run = await execute_research_run(run.id, pipeline_db, router=router)

    assert completed_run.status == "completed"
    assert completed_run.completed_at is not None

    # Verify stages
    steps = pipeline_db.query(RunStep).filter(RunStep.run_id == run.id).all()
    step_keys = [s.step_key for s in steps]
    assert "planning" in step_keys
    assert "retrieving" in step_keys
    assert "extracting" in step_keys
    assert "verifying" in step_keys
    assert "reporting" in step_keys

    # Verify Frozen Report generated with citations
    report = pipeline_db.query(Report).filter(Report.run_id == run.id).first()
    assert report is not None
    assert report.status == "frozen"
    assert "Passage: `pas_" in report.body_markdown
    assert report.manifest_hash != ""


def test_at_07_cancellation_preserves_trustworthy_terminal_state(pipeline_db, auth_ctx):
    """
    ACCEPTANCE TEST AT-07 & RUN-11:
    Cancelling a run transitions it to 'cancelled' and prevents subsequent work.
    """
    run, _ = create_research_run(
        db=pipeline_db,
        auth=auth_ctx,
        question="Long running query to be cancelled",
    )

    cancelled_run = cancel_research_run(pipeline_db, auth_ctx, run.id)
    assert cancelled_run.status == "cancelled"

    # Outbox event emitted for cancellation
    cancel_evt = (
        pipeline_db.query(OutboxEvent)
        .filter(OutboxEvent.aggregate_id == run.id, OutboxEvent.event_type == "research_run.cancelled")
        .first()
    )
    assert cancel_evt is not None
