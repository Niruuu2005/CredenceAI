"""API key endpoints require authentication."""
import pytest
from app.models import User
from app.services.security import create_access_token
from app.config import settings


@pytest.fixture
def production_auth_env(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "JWT_SECRET", "ci-test-jwt-secret-not-default-value")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost/callback")


def test_api_keys_require_auth(client, production_auth_env):
    res = client.get("/auth/keys")
    assert res.status_code == 401


def test_create_api_key_requires_auth(client, production_auth_env):
    res = client.post("/auth/keys", json={"owner": "someone", "label": "test"})
    assert res.status_code == 401


def test_authenticated_user_can_create_and_list_keys(client, db_session):
    user = User(id="key_user", email="keys@test.com", name="Key User")
    db_session.add(user)
    db_session.commit()
    token = create_access_token({"sub": user.id, "email": user.email, "name": user.name})
    headers = {"Authorization": f"Bearer {token}"}

    create_res = client.post("/auth/keys", json={"owner": "ignored", "label": "dev"}, headers=headers)
    assert create_res.status_code == 201
    assert "key" in create_res.json()

    list_res = client.get("/auth/keys", headers=headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1
