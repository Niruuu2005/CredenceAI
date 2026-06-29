import pytest
from fastapi.testclient import TestClient
from app.main import app as fastapi_app
from app.config import settings


@pytest.fixture(scope="function")
def production_client(monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "JWT_SECRET", "ci-test-jwt-secret-not-default-value")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost/callback")
    monkeypatch.setattr(settings, "DEV_LOGIN_USERNAME", None)
    monkeypatch.setattr(settings, "DEV_LOGIN_PASSWORD", None)

    with TestClient(fastapi_app) as client:
        yield client


def test_google_auth_url_disabled_in_production(production_client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", None)
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", None)
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", None)
    res = production_client.get("/auth/google/url")
    assert res.status_code == 503


def test_dev_login_disabled_in_production(production_client):
    res = production_client.post(
        "/auth/login",
        json={"username": "admin", "password": "secret"},
    )
    assert res.status_code == 503


def test_mock_google_callback_disabled_in_production(production_client, monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", None)
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", None)
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", None)
    res = production_client.post(
        "/auth/google/callback",
        json={"code": "mock_dev_code"},
    )
    assert res.status_code == 503


def test_unauthenticated_jobs_rejected_in_production(production_client):
    res = production_client.get("/jobs")
    assert res.status_code == 401
