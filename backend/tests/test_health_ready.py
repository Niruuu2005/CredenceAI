"""Health readiness endpoint tests."""

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app as fastapi_app
from app.services import search_index, storage


@pytest.fixture
def health_client():
    search_index._opensearch_available = None
    search_index._cached_opensearch_client = None
    storage._s3_available = None
    storage._cached_client = None
    with TestClient(fastapi_app) as client:
        yield client
    search_index._opensearch_available = None
    storage._s3_available = None


def test_health_ready_degraded_mode(health_client):
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(settings, "SEARCH_BACKEND", "database")
        mp.setattr(settings, "STORAGE_BACKEND", "local")
        mp.setattr(settings, "CELERY_ALWAYS_EAGER", True)
        response = health_client.get("/api/health/ready")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] in ("ready", "degraded")
    assert body["database"] == "ok"
    assert body["search"] == "database_fallback"
    assert body["storage"] == "local_fallback"
    assert body["celery_mode"] == "eager"
    assert body["worker_available"] is False


def test_health_liveness_no_db(health_client):
    response = health_client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "credenceai-api"}
