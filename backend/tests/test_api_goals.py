from unittest.mock import patch

def test_submit_goal_success(client):
    payload = {
        "goal": "Research Perplexity AI and its competitors",
        "vertical": "company"
    }
    response = client.post("/goals", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "goal" in data
    assert "plan_id" in data
    assert "jobs" in data
    assert len(data["jobs"]) > 0
    
    # Check that job fields match the frontend requirements
    job = data["jobs"][0]
    assert "job_id" in job
    assert job["status"] == "submitted" or job["status"] == "completed"  # celery is eager, so it runs immediately and is completed
    assert "job_type" in job
    assert "input" in job
    assert "submitted_at" in job

def test_submit_goal_too_short(client):
    payload = {
        "goal": "AI",
        "vertical": "company"
    }
    response = client.post("/goals", json=payload)
    assert response.status_code == 400
    assert "at least 3 characters" in response.json()["detail"]

def test_submit_goal_fallback(client):
    payload = {
        "goal": "Some generic question",
        "vertical": "general"
    }
    # Mock invoke_planner_agent to return None to trigger the fallback logic
    with patch("app.api.goals.invoke_planner_agent", return_value=None):
        response = client.post("/goals", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["goal"] == "Some generic question"
        assert len(data["jobs"]) == 1
        assert data["jobs"][0]["job_type"] == "search_query"
        assert data["jobs"][0]["input"] == "Some generic question"
