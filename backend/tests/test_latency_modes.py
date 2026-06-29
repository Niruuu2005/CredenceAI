import pytest
from unittest.mock import patch
from app.services.cache_manager import CacheManager
from app.services.orchestrator import route_and_execute_job
from app.services.repository import get_job, create_job, get_job_normalized_results
from app.database import SessionLocal

@pytest.fixture(autouse=True)
def mock_cache_manager():
    def dummy_init(self, default_ttl_seconds: int = 3600):
        self.default_ttl = default_ttl_seconds
        self.redis_client = None
    with patch("app.services.cache_manager.CacheManager.__init__", dummy_init):
        yield

def test_cache_manager_in_memory():
    """Test CacheManager basic set/get/delete using in-memory fallback."""
    cache = CacheManager()
    
    key = "test_key_abc"
    val = {"data": "hello_world"}
    
    cache.set(key, val, ttl_seconds=60)
    assert cache.get(key) == val
    
    cache.delete(key)
    assert cache.get(key) is None


def test_orchestrator_fast_mode_cache_hit(db_session):
    """Test orchestrator short-circuiting on cache hit in fast mode."""
    cache = CacheManager()
    cache.redis_client = None
    cache.clear_all()
    
    query = "cache hit test query"
    vertical = "web"
    cache_key = f"query_cache:{query}:{vertical}"
    
    cached_results = [
        {
            "title": "Cached Page",
            "url": "https://cached-url.com",
            "source": "searxng",
            "snippet": "This is cached snippet text.",
            "quality_scores": {
                "final_trust_score": 0.95,
                "decision": "accept"
            }
        }
    ]
    cache.set(cache_key, cached_results, ttl_seconds=100)
    
    # Create job in fast execution mode
    job = create_job(
        db=db_session,
        job_id="job_fast_test_123",
        trace_id="trace_fast_test_123",
        job_type="search_query",
        input_val=query,
        vertical=vertical,
        execution_mode="fast"
    )
    
    route_and_execute_job(db_session, job.id)
    
    # Verify results retrieved are from cache
    db_results = get_job_normalized_results(db_session, job.id)
    assert len(db_results) == 1
    assert db_results[0].title == "Cached Page"
    assert db_results[0].url == "https://cached-url.com"

@patch("app.services.searxng_client.SearXNGClient.search")
def test_orchestrator_fast_mode_cache_miss(mock_search, db_session):
    """Test orchestrator in fast mode with cache miss."""
    cache = CacheManager()
    cache.redis_client = None
    cache.clear_all()
    
    mock_search.return_value = {
        "results": [
            {"title": f"Result {i}", "url": f"https://res{i}.com", "content": f"content {i}", "engine": "searxng"}
            for i in range(10)
        ]
    }
    
    query = "cache miss test query"
    job = create_job(
        db=db_session,
        job_id="job_fast_miss_123",
        trace_id="trace_fast_miss_123",
        job_type="search_query",
        input_val=query,
        vertical="web",
        execution_mode="fast"
    )
    
    route_and_execute_job(db_session, job.id)
    
    db_results = get_job_normalized_results(db_session, job.id)
    # Fast mode should restrict result counts to 5 (or fewer)
    assert len(db_results) <= 5
