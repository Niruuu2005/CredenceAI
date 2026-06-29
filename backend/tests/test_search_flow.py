from unittest.mock import patch

def test_end_to_end_search_flow(client):
    # Fake search response containing the word "antigravity"
    fake_searxng_response = {
        "query": "physics papers",
        "results": [
            {
                "title": "Antigravity Research Paper",
                "url": "https://physics.example/antigravity",
                "content": "A breakthrough study on gravitational propulsion",
                "engine": "google"
            }
        ]
    }
    
    with patch("app.services.searxng_client.SearXNGClient.search", return_value=fake_searxng_response) as mock_search:
        # 1. Submit a job that will trigger worker and run routing/indexing synchronously
        payload = {
            "job_type": "search_query",
            "input": "physics papers"
        }
        submit_res = client.post("/jobs", json=payload)
        assert submit_res.status_code == 202
        job_id = submit_res.json()["job_id"]
        
        # 2. Query job status to verify it completed and saved 1 result
        status_res = client.get(f"/jobs/{job_id}")
        assert status_res.status_code == 200
        assert status_res.json()["status"] == "completed"
        assert status_res.json()["results_count"] == 1
        
        # 3. Query internal search index endpoint and find the indexed result
        search_res = client.get("/search?q=antigravity")
        assert search_res.status_code == 200
        search_data = search_res.json()
        assert search_data["query"] == "antigravity"
        assert len(search_data["results"]) == 1
        assert search_data["results"][0]["document"]["title"] == "Antigravity Research Paper"
        assert search_data["results"][0]["document"]["url"] == "https://physics.example/antigravity"
