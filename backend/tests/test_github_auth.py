"""Tests for GitHub OAuth endpoints."""

from app.config import settings


def test_github_auth_url_mock_in_local(client):
    original = settings.APP_ENV
    settings.APP_ENV = "local"
    try:
        settings.GITHUB_CLIENT_ID = None
        settings.GITHUB_REDIRECT_URI = None
        response = client.get("/auth/github/url")
        assert response.status_code == 200
        data = response.json()
        assert data["mock"] is True
        assert "mock_github_code" in data["url"]
    finally:
        settings.APP_ENV = original


def test_github_callback_mock_in_local(client):
    original = settings.APP_ENV
    settings.APP_ENV = "local"
    try:
        response = client.post("/auth/github/callback", json={"code": "mock_github_code"})
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["id"] == "gh_mock_dev"
        assert data["user"]["email"] == "dev@github.local"
    finally:
        settings.APP_ENV = original


def test_github_auth_url_requires_config_in_production(client):
    original_env = settings.APP_ENV
    original_id = settings.GITHUB_CLIENT_ID
    original_uri = settings.GITHUB_REDIRECT_URI
    settings.APP_ENV = "production"
    settings.GITHUB_CLIENT_ID = None
    settings.GITHUB_REDIRECT_URI = None
    try:
        response = client.get("/auth/github/url")
        assert response.status_code == 503
    finally:
        settings.APP_ENV = original_env
        settings.GITHUB_CLIENT_ID = original_id
        settings.GITHUB_REDIRECT_URI = original_uri
