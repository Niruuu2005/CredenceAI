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
        assert data["error"] == "missing_api_key"
        
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
