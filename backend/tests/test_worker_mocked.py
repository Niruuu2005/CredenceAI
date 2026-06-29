from unittest.mock import patch

def test_e2e_mocked_worker_execution(client, db_session):
    fake_searxng_response = {
        "query": "test query for worker",
        "results": [
            {
                "title": "Mocked Search Result",
                "url": "https://mocked-result.com",
                "content": "This is a mocked result snippet",
                "engine": "google"
            }
        ]
    }
    
    # Mock both SearXNG Client and prevent file cleanup error if any
    with patch("app.services.searxng_client.SearXNGClient.search", return_value=fake_searxng_response) as mock_search, \
         patch("app.services.cache_manager.CacheManager.get", return_value=None):
        payload = {
            "job_type": "search_query",
            "input": "test query for worker"
        }
        
        # Submit job. This will persist job and call process_job.delay inline
        response = client.post("/jobs", json=payload)

        assert response.status_code == 202
        data = response.json()
        job_id = data["job_id"]
        
        # Verify SearXNG search was invoked
        mock_search.assert_called_once_with("test query for worker")
        
        # Verify status is completed
        status_response = client.get(f"/jobs/{job_id}")
        assert status_response.status_code == 200
        status_data = status_response.json()
        assert status_data["status"] == "completed"
        assert status_data["results_count"] == 1
        
        # Check that it actually persisted in db_session
        from app.models import SourceResult, NormalizedResult
        src_res = db_session.query(SourceResult).filter(SourceResult.job_id == job_id).first()
        assert src_res is not None
        assert src_res.source == "searxng"
        
        norm_res = db_session.query(NormalizedResult).filter(NormalizedResult.job_id == job_id).first()
        assert norm_res is not None
        assert norm_res.title == "Mocked Search Result"
        assert norm_res.url == "https://mocked-result.com"
