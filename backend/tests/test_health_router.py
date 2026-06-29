import pytest
from app.services.health_router import HealthRouter

def test_health_router_success_routing():
    """Test health router returns default route when healthy."""
    router = HealthRouter()
    
    # Ensure it's healthy
    router.record_result("searxng", success=True)
    assert router.get_route("searxng") == "searxng"
    
    # Record failures below threshold
    router.record_result("searxng", success=False)
    router.record_result("searxng", success=False)
    assert router.get_route("searxng") == "searxng"
    
    # Record a success to reset counter
    router.record_result("searxng", success=True)
    router.record_result("searxng", success=False)
    assert router.get_route("searxng") == "searxng"

def test_health_router_degraded_routing():
    """Test health router redirects to fallback when degraded."""
    router = HealthRouter(failure_threshold=2)
    
    # Record 2 consecutive failures
    router.record_result("searxng", success=False)
    router.record_result("searxng", success=False)
    
    # Should resolve to its fallback provider "duckduckgo"
    assert router.get_route("searxng") == "duckduckgo"
    
    # Reset on success
    router.record_result("searxng", success=True)
    assert router.get_route("searxng") == "searxng"

def test_api_health_endpoint(client):
    """Test health check API contains provider health reports."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "providers" in data
    assert "searxng" in data["providers"]
    assert data["providers"]["searxng"]["status"] in ["healthy", "degraded"]
