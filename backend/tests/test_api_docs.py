"""OpenAPI /docs must be available when ENABLE_API_DOCS is on (default)."""

from fastapi.testclient import TestClient

from app.config import settings
from app.main import app


def test_root_advertises_docs_when_enabled():
    assert settings.ENABLE_API_DOCS is True
    client = TestClient(app)
    res = client.get("/")
    assert res.status_code == 200
    assert res.json().get("docs") == "/docs"


def test_openapi_docs_routes_exist():
    client = TestClient(app)
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200
    assert client.get("/redoc").status_code == 200


def test_docs_csp_allows_swagger_cdn():
    """Blank Swagger page is caused by CSP blocking cdn.jsdelivr.net."""
    client = TestClient(app)
    res = client.get("/docs")
    csp = res.headers.get("content-security-policy", "")
    assert "cdn.jsdelivr.net" in csp
    assert "script-src" in csp
