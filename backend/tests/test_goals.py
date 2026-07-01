"""Tests for goal submission on free tier without OpenAI."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.config import settings
from app.api import goals as goals_module
from app.schemas import JobStatusResponse, QualitySummary
from datetime import datetime, timezone


def test_build_direct_search_plan():
    plan = goals_module._build_direct_search_plan("Taiwan semiconductor exports")
    assert len(plan["jobs"]) == 1
    assert plan["jobs"][0]["job_type"] == "search_query"
    assert plan["jobs"][0]["parameters"]["query"] == "Taiwan semiconductor exports"


def test_normalize_job_type_maps_unknown_to_search_query():
    assert goals_module._normalize_job_type("monitor") == "search_query"
    assert goals_module._normalize_job_type("search") == "search_query"
    assert goals_module._normalize_job_type("search_query") == "search_query"


def test_resolve_job_input_prefers_query():
    job_def = {
        "description": "desc",
        "parameters": {"query": "specific query", "entity": "ignored"},
    }
    assert goals_module._resolve_job_input(job_def, "fallback") == "specific query"


@pytest.mark.asyncio
async def test_submit_goal_skips_planner_without_openai_key():
    original_key = settings.OPENAI_API_KEY
    settings.OPENAI_API_KEY = None

    mock_db = MagicMock()
    mock_user = MagicMock()
    mock_user.id = "user_1"

    goal_in = goals_module.GoalCreate(goal="Research Taiwan chips", vertical="general")
    request = MagicMock()
    background_tasks = MagicMock()

    with patch("app.api.goals.check_job_quota"):
        with patch("app.api.goals.create_job") as mock_create:
            with patch("app.api.goals._enqueue_goal_job"):
                with patch("app.api.goals._submitted_job_response") as mock_response:
                    with patch(
                        "app.api.goals.invoke_planner_agent",
                        new_callable=AsyncMock,
                    ) as mock_planner:
                        mock_job = MagicMock()
                        mock_job.id = "job_test"
                        mock_create.return_value = mock_job
                        mock_response.return_value = JobStatusResponse(
                            job_id="job_test",
                            status="submitted",
                            results_count=0,
                            failed_events=0,
                            quality_summary=QualitySummary(
                                accepted=0, rejected=0, manual_review=0
                            ),
                            created_at=datetime.now(timezone.utc),
                        )

                        result = await goals_module.submit_goal(
                            goal_in,
                            request,
                            background_tasks,
                            mock_db,
                            mock_user,
                        )

                        mock_planner.assert_not_called()
                        assert result.goal == "Research Taiwan chips"
                        assert len(result.jobs) == 1

    settings.OPENAI_API_KEY = original_key
