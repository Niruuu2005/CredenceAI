import pytest
from app.config import settings
from app.services.api_key_service import create_api_key

def test_api_key_creation_and_validation(client):
    # Enable API key authentication for this test
    original_auth_setting = settings.ENABLE_API_KEY_AUTH
    settings.ENABLE_API_KEY_AUTH = True
    try:
        # 1. Create a key
        create_payload = {
            "owner": "test_developer",
            "label": "Test Key"
        }
        response = client.post("/auth/keys", json=create_payload)
        assert response.status_code == 201
        data = response.json()
        assert "key" in data
        assert data["owner"] == "mock_jane_doe"
        assert data["label"] == "Test Key"
        
        raw_key = data["key"]
        
        # 2. Validate the key
        validate_headers = {"X-API-Key": raw_key}
        response = client.get("/auth/validate", headers=validate_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["owner"] == "mock_jane_doe"
    finally:
        settings.ENABLE_API_KEY_AUTH = original_auth_setting

def test_middleware_blocking_and_allowing(client, db_session):
    # Enable API key authentication for this test
    original_auth_setting = settings.ENABLE_API_KEY_AUTH
    settings.ENABLE_API_KEY_AUTH = True
    try:
        # 1. Access protected endpoint /jobs without key -> 401
        response = client.post("/jobs", json={"job_type": "search_query", "input": "test"})
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "missing_auth"
        
        # 2. Access protected endpoint with invalid key format -> 401
        response = client.post("/jobs", json={"job_type": "search_query", "input": "test"}, headers={"X-API-Key": "invalid_key"})
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "invalid_api_key_format"
        
        # 3. Access protected endpoint with unrecognized key -> 401
        response = client.post("/jobs", json={"job_type": "search_query", "input": "test"}, headers={"X-API-Key": "cred_sk_someunrecognizedkey1234567890abcdef"})
        assert response.status_code == 401
        data = response.json()
        assert data["error"] == "invalid_api_key"
        
        # 4. Access protected endpoint with a valid key -> 202
        from app.models import User
        db_session.add(User(id="test_dev_2", email="dev2@test.com", name="Dev 2"))
        db_session.commit()
        key_info = create_api_key(db_session, owner="test_dev_2", label="Active Key", user_id="test_dev_2")
        headers = {"X-API-Key": key_info["key"]}
        response = client.post("/jobs", json={"job_type": "search_query", "input": "test"}, headers=headers)
        assert response.status_code == 202
        
        # 5. Access health endpoint without key -> 200 (exempt)
        response = client.get("/health")
        assert response.status_code == 200
    finally:
        settings.ENABLE_API_KEY_AUTH = original_auth_setting

def test_middleware_protects_monitors_and_collections(client, db_session):
    original_auth_setting = settings.ENABLE_API_KEY_AUTH
    settings.ENABLE_API_KEY_AUTH = True
    try:
        response = client.get("/monitors")
        assert response.status_code == 401
        assert response.json()["error"] == "missing_auth"

        response = client.get("/collections")
        assert response.status_code == 401
        assert response.json()["error"] == "missing_auth"

        from app.models import User
        db_session.add(User(id="test_dev_3", email="dev3@test.com", name="Dev 3"))
        db_session.commit()
        key_info = create_api_key(db_session, owner="test_dev_3", label="Monitor Key", user_id="test_dev_3")
        headers = {"X-API-Key": key_info["key"]}

        response = client.get("/monitors", headers=headers)
        assert response.status_code == 200

        response = client.get("/collections", headers=headers)
        assert response.status_code == 200
    finally:
        settings.ENABLE_API_KEY_AUTH = original_auth_setting


def test_middleware_accepts_jwt_bearer_in_production(client, db_session, monkeypatch):
    monkeypatch.setattr(settings, "APP_ENV", "production")
    monkeypatch.setattr(settings, "JWT_SECRET", "ci-test-jwt-secret-not-default-value")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setattr(settings, "GOOGLE_CLIENT_SECRET", "test-secret")
    monkeypatch.setattr(settings, "GOOGLE_REDIRECT_URI", "http://localhost/callback")
    original_auth_setting = settings.ENABLE_API_KEY_AUTH
    settings.ENABLE_API_KEY_AUTH = True
    try:
        from app.models import User
        from app.services.security import create_access_token

        db_session.add(User(id="jwt_user", email="jwt@test.com", name="JWT User"))
        db_session.commit()
        token = create_access_token({"sub": "jwt_user", "email": "jwt@test.com", "name": "JWT User"})
        headers = {"Authorization": f"Bearer {token}"}

        response = client.get("/jobs", headers=headers)
        assert response.status_code == 200

        response = client.post(
            "/jobs",
            json={"job_type": "search_query", "input": "jwt test"},
            headers=headers,
        )
        assert response.status_code == 202
    finally:
        settings.ENABLE_API_KEY_AUTH = original_auth_setting


def test_api_key_bypass_when_disabled(client):
    # Disable API key authentication
    original_auth_setting = settings.ENABLE_API_KEY_AUTH
    settings.ENABLE_API_KEY_AUTH = False
    try:
        # Access protected endpoint without key -> should succeed
        response = client.post("/jobs", json={"job_type": "search_query", "input": "test"})
        assert response.status_code == 202
    finally:
        settings.ENABLE_API_KEY_AUTH = original_auth_setting
