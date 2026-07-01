"""CORS integration tests for cross-origin SPA access."""

import pytest
from fastapi.testclient import TestClient

from app.config import Settings
from app.main import app as fastapi_app

VERCEL_ORIGIN = "https://credence-ai-patilniraj413-5474s-projects.vercel.app"
LOCAL_ORIGIN = "http://localhost:3000"
EVIL_ORIGIN = "https://evil.com"


@pytest.fixture
def cors_client():
    with TestClient(fastapi_app) as client:
        yield client


def test_options_goals_preflight_allowed_origin(cors_client):
    response = cors_client.options(
        "/api/goals",
        headers={
            "Origin": LOCAL_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == LOCAL_ORIGIN
    assert "POST" in response.headers.get("access-control-allow-methods", "")


def test_options_goals_preflight_vercel_regex(cors_client):
    response = cors_client.options(
        "/api/goals",
        headers={
            "Origin": VERCEL_ORIGIN,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == VERCEL_ORIGIN


def test_options_jobs_preflight_without_api_key(cors_client):
    response = cors_client.options(
        "/api/jobs",
        headers={
            "Origin": LOCAL_ORIGIN,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == LOCAL_ORIGIN


def test_get_health_includes_cors_header(cors_client):
    response = cors_client.get("/api/health", headers={"Origin": LOCAL_ORIGIN})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == LOCAL_ORIGIN
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "credenceai-api"


def test_options_health_preflight_includes_patch(cors_client):
    response = cors_client.options(
        "/api/health",
        headers={
            "Origin": LOCAL_ORIGIN,
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "authorization,content-type",
        },
    )
    assert response.status_code == 200
    methods = response.headers.get("access-control-allow-methods", "")
    assert "PATCH" in methods
    allowed_headers = response.headers.get("access-control-allow-headers", "")
    assert "Authorization" in allowed_headers
    assert "Content-Type" in allowed_headers


def test_disallowed_origin_has_no_cors_header(cors_client):
    response = cors_client.get("/api/health", headers={"Origin": EVIL_ORIGIN})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") is None


@pytest.mark.parametrize(
    "raw,expected",
    [
        (
            '["https://app.example.com/","https://other.example.com"]',
            ["https://app.example.com", "https://other.example.com"],
        ),
        (
            "https://one.example.com, https://two.example.com",
            ["https://one.example.com", "https://two.example.com"],
        ),
        (
            "https://single.example.com",
            ["https://single.example.com"],
        ),
    ],
)
def test_cors_origins_parsing(raw, expected):
    settings = Settings(CORS_ALLOWED_ORIGINS=raw)
    assert settings.CORS_ALLOWED_ORIGINS == expected
