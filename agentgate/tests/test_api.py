"""API integration tests for AgentGate."""

import pytest
from fastapi.testclient import TestClient

from main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "agentgate"


def test_evaluate_task_book_flight(client):
    res = client.post(
        "/evaluate-task",
        json={"task_description": "Book flight to Paris"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "needs_clarification"
    assert len(data["missing_info"]) > 0


def test_evaluate_task_unsafe(client):
    res = client.post(
        "/evaluate-task",
        json={
            "task_description": "Delete production database",
            "proposed_action": "db.drop",
        },
    )
    assert res.status_code == 200
    assert res.json()["status"] == "unsafe"


def test_compare_options(client):
    res = client.post(
        "/compare-options",
        json={
            "decision_goal": "Weather lookup",
            "options": [
                {"id": "a", "label": "Guess city", "action": "search"},
                {"id": "b", "label": "Ask user", "action": "ask"},
            ],
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["recommended_option_id"] in ("a", "b")
    assert len(data["ranking"]) == 2


def test_skill_md(client):
    res = client.get("/skill.md")
    assert res.status_code == 200
    assert "AgentGate" in res.text
    assert "/evaluate-task" in res.text


def test_demo_hello(client):
    res = client.post("/demo/hello", json={"message": "hello"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["service"] == "agentgate"
    assert data["message"] == "hello"
    assert "hello" in data["echo"]


def test_demo_hello_default_message(client):
    res = client.post("/demo/hello", json={})
    assert res.status_code == 200
    assert res.json()["message"] == "hello"
