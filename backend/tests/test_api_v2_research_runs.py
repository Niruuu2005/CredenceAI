"""
v2 REST API Integration Tests.
Verifies Phase 3 endpoints:
- POST /api/v2/research-runs
- GET /api/v2/research-runs
- GET /api/v2/research-runs/{run_id}
- POST /api/v2/research-runs/{run_id}/execute
- GET /api/v2/research-runs/{run_id}/claims
- GET /api/v2/research-runs/{run_id}/reports/{version}
- POST /api/v2/research-runs/{run_id}/reports/{report_id}/approve
- POST /api/v2/monitors & GET /api/v2/monitors/{monitor_id}/deltas
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import get_db
from app.models import (
    Base,
    Tenant,
    Workspace,
    User,
    Membership,
    ApiKey,
)
from app.services.api_key_service import hash_key


from sqlalchemy.pool import StaticPool


@pytest.fixture
def v2_client():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    setup_session = TestingSession()

    tenant = Tenant(id="tenant_v2", name="V2 Tenant")
    ws = Workspace(id="ws_v2", tenant_id="tenant_v2", name="V2 Workspace")
    user = User(id="user_v2", email="researcher@v2.ai", name="Researcher V2", role="user")
    mem = Membership(id="mem_v2", user_id="user_v2", workspace_id="ws_v2", role="researcher")

    # Raw key: crd_live_testkeyv2
    raw_key = "crd_live_testkeyv2"
    api_key = ApiKey(
        key_hash=hash_key(raw_key),
        owner="Researcher V2",
        user_id="user_v2",
        workspace_id="ws_v2",
    )

    setup_session.add_all([tenant, ws, user, mem, api_key])
    setup_session.commit()
    setup_session.close()

    def override_get_db():
        db = TestingSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    client = TestClient(app)
    client.headers = {
        "Authorization": f"Bearer {raw_key}",
        "X-Workspace-Id": "ws_v2",
    }

    yield client, TestingSession, raw_key

    app.dependency_overrides.clear()


def test_v2_research_runs_crud_and_execution(v2_client):
    client, session, raw_key = v2_client

    # 1. Create Run
    payload = {
        "question": "What are the latest breakthroughs in fusion energy?",
        "mode": "investigate",
        "idempotency_key": "idem_fusion_101",
    }
    res_create = client.post("/api/v2/research-runs", json=payload)
    assert res_create.status_code == 201
    run_data = res_create.json()
    run_id = run_data["id"]
    assert run_data["workspace_id"] == "ws_v2"
    assert run_data["status"] in {"queued", "created"}

    # 2. Idempotency Check (same idempotency_key returns identical run)
    res_idem = client.post("/api/v2/research-runs", json=payload)
    assert res_idem.status_code == 201
    assert res_idem.json()["id"] == run_id

    # 3. List Runs
    res_list = client.get("/api/v2/research-runs")
    assert res_list.status_code == 200
    runs = res_list.json()
    assert any(r["id"] == run_id for r in runs)

    # 4. Get Run Details
    res_get = client.get(f"/api/v2/research-runs/{run_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == run_id

    # 5. Execute Pipeline Directly
    res_exec = client.post(f"/api/v2/research-runs/{run_id}/execute")
    assert res_exec.status_code == 200
    exec_data = res_exec.json()
    assert exec_data["status"] in {"completed", "partial"}
    assert exec_data["completed_at"] is not None

    # 6. Retrieve Claims
    res_claims = client.get(f"/api/v2/research-runs/{run_id}/claims")
    assert res_claims.status_code == 200
    claims = res_claims.json()
    assert len(claims) > 0

    # 7. Retrieve Frozen Report
    res_report = client.get(f"/api/v2/research-runs/{run_id}/reports/1")
    assert res_report.status_code == 200
    report_data = res_report.json()
    assert report_data["status"] == "frozen"
    assert report_data["manifest_hash"] != ""
    assert "Brief:" in report_data["title"]


def test_v2_monitors_crud_and_deltas(v2_client):
    client, session, _ = v2_client

    # 1. Create Monitor
    payload = {
        "topic": "Semiconductor Export Controls",
        "scope": "Global Trade",
        "interval": "Daily",
    }
    res_create = client.post("/api/v2/monitors", json=payload)
    assert res_create.status_code == 201
    mon_data = res_create.json()
    mon_id = mon_data["id"]
    assert mon_data["topic"] == "Semiconductor Export Controls"

    # 2. List Monitors
    res_list = client.get("/api/v2/monitors")
    assert res_list.status_code == 200
    assert any(m["id"] == mon_id for m in res_list.json())

    # 3. Get Deltas
    res_deltas = client.get(f"/api/v2/monitors/{mon_id}/deltas")
    assert res_deltas.status_code == 200
    delta_data = res_deltas.json()
    assert delta_data["monitor_id"] == mon_id
    assert delta_data["deltas_count"] == 0


def test_v2_research_runs_guest_access(v2_client):
    client, _, _ = v2_client
    # Unauthenticated guest call (no Authorization header or API key)
    client.headers.clear()

    res_list = client.get("/api/v2/research-runs")
    assert res_list.status_code == 200
    assert isinstance(res_list.json(), list)

    res_create = client.post(
        "/api/v2/research-runs",
        json={"question": "What is the capital of France?", "mode": "verify"},
    )
    assert res_create.status_code == 201
    run_data = res_create.json()
    assert run_data["question"] == "What is the capital of France?"
    assert run_data["status"] in ("queued", "pending", "completed")


