"""
Unit and integration tests for AuthContext and multi-tenant workspace security.
Verifies FR-001, IAM-01, IAM-02, IAM-03, Release Gate G2.
"""

import pytest
from fastapi import FastAPI, Depends, HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.models import Base, User, Tenant, Workspace, Membership, ApiKey
from app.database import get_db
from app.services.security import create_access_token
from app.identity.auth_context import AuthContext, WorkspaceRole, Permission, ROLE_PERMISSIONS
from app.identity.dependencies import get_auth_context, require_permission, get_or_create_default_workspace


@pytest.fixture
def db_session():
    """In-memory SQLite session for fast, isolated identity testing."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_app(db_session):
    """Test FastAPI application with protected endpoints."""
    app = FastAPI()

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    @app.get("/api/v2/test/me")
    def get_me(auth: AuthContext = Depends(get_auth_context)):
        return {
            "user_id": auth.user_id,
            "tenant_id": auth.tenant_id,
            "workspace_id": auth.workspace_id,
            "role": auth.role.value,
            "permissions": [p.value for p in auth.permissions],
        }

    @app.post("/api/v2/test/research")
    def create_research(auth: AuthContext = Depends(require_permission(Permission.CREATE_RESEARCH))):
        return {"status": "ok", "workspace_id": auth.workspace_id}

    @app.post("/api/v2/test/review")
    def review_evidence(auth: AuthContext = Depends(require_permission(Permission.REVIEW_EVIDENCE))):
        return {"status": "ok", "workspace_id": auth.workspace_id}

    @app.post("/api/v2/test/manage")
    def manage_workspace(auth: AuthContext = Depends(require_permission(Permission.MANAGE_WORKSPACE))):
        return {"status": "ok", "workspace_id": auth.workspace_id}

    return app


def test_auth_context_permissions():
    """Verify role-to-permission mappings and require_permission helper."""
    admin_ctx = AuthContext(
        user_id="u1",
        tenant_id="t1",
        workspace_id="ws1",
        role=WorkspaceRole.ADMIN,
        permissions=set(ROLE_PERMISSIONS[WorkspaceRole.ADMIN]),
    )
    assert admin_ctx.has_permission(Permission.CREATE_RESEARCH)
    assert admin_ctx.has_permission(Permission.MANAGE_WORKSPACE)
    admin_ctx.require_permission(Permission.CREATE_RESEARCH)

    viewer_ctx = AuthContext(
        user_id="u2",
        tenant_id="t1",
        workspace_id="ws1",
        role=WorkspaceRole.VIEWER,
        permissions=set(ROLE_PERMISSIONS[WorkspaceRole.VIEWER]),
    )
    assert viewer_ctx.has_permission(Permission.READ_RESEARCH)
    assert not viewer_ctx.has_permission(Permission.CREATE_RESEARCH)
    assert not viewer_ctx.has_permission(Permission.REVIEW_EVIDENCE)

    with pytest.raises(HTTPException) as exc_info:
        viewer_ctx.require_permission(Permission.CREATE_RESEARCH)
    assert exc_info.value.status_code == 403


def test_default_workspace_auto_creation(db_session, test_app):
    """Verify an existing user without workspaces automatically gets a default tenant & workspace."""
    user = User(id="user_alice", email="alice@campus.edu", name="Alice Researcher")
    db_session.add(user)
    db_session.commit()

    token = create_access_token({"sub": "user_alice"})
    client = TestClient(test_app)

    response = client.get("/api/v2/test/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "user_alice"
    assert data["role"] == "admin"
    assert "research:create" in data["permissions"]
    assert "workspace:manage" in data["permissions"]
    assert data["workspace_id"].startswith("ws_")
    assert data["tenant_id"].startswith("tenant_")


def test_adversarial_cross_tenant_access_blocked(db_session, test_app):
    """
    CRITICAL RELEASE GATE G2:
    Tenant A must never be able to access Tenant B's workspace via X-Workspace-Id.
    """
    # Create Tenant B and Workspace B
    tenant_b = Tenant(id="tenant_b", name="Organization B")
    ws_b = Workspace(id="ws_b", tenant_id="tenant_b", name="Confidential B")
    user_b = User(id="user_bob", email="bob@victim.org", name="Bob")
    mem_b = Membership(id="mem_b", user_id="user_bob", workspace_id="ws_b", role=WorkspaceRole.ADMIN.value)
    db_session.add_all([tenant_b, ws_b, user_b, mem_b])

    # Create Tenant A (Attacker)
    tenant_a = Tenant(id="tenant_a", name="Organization A")
    ws_a = Workspace(id="ws_a", tenant_id="tenant_a", name="Attacker WS")
    user_a = User(id="user_attacker", email="attacker@adversary.com", name="Eve")
    mem_a = Membership(id="mem_a", user_id="user_attacker", workspace_id="ws_a", role=WorkspaceRole.ADMIN.value)
    db_session.add_all([tenant_a, ws_a, user_a, mem_a])
    db_session.commit()

    token_a = create_access_token({"sub": "user_attacker"})
    client = TestClient(test_app)

    # 1. Attacker queries own workspace -> 200 OK
    resp_own = client.get(
        "/api/v2/test/me",
        headers={"Authorization": f"Bearer {token_a}", "X-Workspace-Id": "ws_a"}
    )
    assert resp_own.status_code == 200
    assert resp_own.json()["workspace_id"] == "ws_a"

    # 2. Attacker probes Victim's workspace -> MUST BE 403 Forbidden
    resp_probe = client.get(
        "/api/v2/test/me",
        headers={"Authorization": f"Bearer {token_a}", "X-Workspace-Id": "ws_b"}
    )
    assert resp_probe.status_code == 403
    assert "Access denied" in resp_probe.json()["detail"]


def test_rbac_permission_enforcement(db_session, test_app):
    """Test fine-grained RBAC permissions across different member roles."""
    tenant = Tenant(id="tenant_uni", name="University")
    workspace = Workspace(id="ws_lab", tenant_id="tenant_uni", name="Research Lab")
    db_session.add_all([tenant, workspace])

    # Researcher user
    u_researcher = User(id="u_researcher", email="res@uni.edu")
    m_researcher = Membership(id="m_res", user_id="u_researcher", workspace_id="ws_lab", role="researcher")
    
    # Reviewer user
    u_reviewer = User(id="u_reviewer", email="rev@uni.edu")
    m_reviewer = Membership(id="m_rev", user_id="u_reviewer", workspace_id="ws_lab", role="reviewer")

    # Viewer user
    u_viewer = User(id="u_viewer", email="view@uni.edu")
    m_viewer = Membership(id="m_view", user_id="u_viewer", workspace_id="ws_lab", role="viewer")

    db_session.add_all([u_researcher, m_researcher, u_reviewer, m_reviewer, u_viewer, m_viewer])
    db_session.commit()

    client = TestClient(test_app)

    token_res = create_access_token({"sub": "u_researcher"})
    token_rev = create_access_token({"sub": "u_reviewer"})
    token_view = create_access_token({"sub": "u_viewer"})

    # Researcher can create research, but cannot manage workspace or review evidence
    resp = client.post("/api/v2/test/research", headers={"Authorization": f"Bearer {token_res}", "X-Workspace-Id": "ws_lab"})
    assert resp.status_code == 200
    resp_manage = client.post("/api/v2/test/manage", headers={"Authorization": f"Bearer {token_res}", "X-Workspace-Id": "ws_lab"})
    assert resp_manage.status_code == 403

    # Reviewer can review evidence, but cannot create research
    resp_rev_evidence = client.post("/api/v2/test/review", headers={"Authorization": f"Bearer {token_rev}", "X-Workspace-Id": "ws_lab"})
    assert resp_rev_evidence.status_code == 200
    resp_rev_create = client.post("/api/v2/test/research", headers={"Authorization": f"Bearer {token_rev}", "X-Workspace-Id": "ws_lab"})
    assert resp_rev_create.status_code == 403

    # Viewer cannot create or review
    assert client.post("/api/v2/test/research", headers={"Authorization": f"Bearer {token_view}", "X-Workspace-Id": "ws_lab"}).status_code == 403
    assert client.post("/api/v2/test/review", headers={"Authorization": f"Bearer {token_view}", "X-Workspace-Id": "ws_lab"}).status_code == 403
