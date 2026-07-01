def test_submit_job_success(client):
    payload = {
        "job_type": "search_query",
        "input": "open source search engines",
        "vertical": "web",
        "priority": "normal",
        "routing_mode": "free_first",
        "execution_mode": "standard"
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert "job_id" in data
    assert "trace_id" in data
    assert data["status"] == "queued"
    
    # Check trace ID header is returned
    assert response.headers["x-trace-id"] == data["trace_id"]

def test_submit_job_missing_fields(client):
    payload = {
        "job_type": "search_query"
        # "input" is missing
    }
    response = client.post("/jobs", json=payload)
    assert response.status_code == 422

def test_get_job_status_success(client):
    # Submit job first
    payload = {
        "job_type": "search_query",
        "input": "open source search engines"
    }
    submit_response = client.post("/jobs", json=payload)
    job_id = submit_response.json()["job_id"]
    
    # Get status
    status_response = client.get(f"/jobs/{job_id}")
    assert status_response.status_code == 200
    data = status_response.json()
    assert data["job_id"] == job_id
    assert data["status"] == "completed"
    assert data["results_count"] == 1
    assert data["quality_summary"]["manual_review"] == 1

def test_get_job_not_found(client):
    response = client.get("/jobs/job_invalid_id")
    assert response.status_code == 404
