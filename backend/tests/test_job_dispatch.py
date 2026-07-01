"""Tests for stale job recovery and eager dispatch."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from app.services import job_dispatch


@patch("app.services.job_dispatch.settings")
@patch("app.worker.process_job")
def test_dispatch_eager_uses_background_tasks(mock_process_job, mock_settings):
    mock_settings.CELERY_ALWAYS_EAGER = True
    bg = MagicMock()

    job_dispatch.dispatch_process_job("job_abc", bg)

    bg.add_task.assert_called_once_with(job_dispatch._run_process_job, "job_abc")
    mock_process_job.delay.assert_not_called()


@patch("app.services.job_dispatch.settings")
@patch("app.worker.process_job")
def test_dispatch_eager_thread_is_non_daemon(mock_process_job, mock_settings):
    mock_settings.CELERY_ALWAYS_EAGER = True

    with patch("app.services.job_dispatch.threading.Thread") as mock_thread_cls:
        mock_thread_cls.return_value = MagicMock()
        job_dispatch.dispatch_process_job("job_abc", None)
        mock_thread_cls.assert_called_once()
        assert mock_thread_cls.call_args.kwargs.get("daemon") is False


@patch("app.services.job_dispatch.dispatch_process_job")
def test_recover_stale_jobs_redispatches_old_queued(mock_dispatch):
    mock_job = MagicMock()
    mock_job.id = "job_stale"
    mock_job.status = "queued"
    mock_job.created_at = datetime.now(timezone.utc) - timedelta(minutes=10)

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.filter.return_value.all.return_value = [
        mock_job
    ]

    count = job_dispatch.recover_stale_jobs(mock_db, max_age_sec=180)

    assert count == 1
    mock_dispatch.assert_called_once_with("job_stale", background_tasks=None)


@patch("app.services.job_dispatch.dispatch_process_job")
def test_maybe_redispatch_stale_job_when_queued_too_long(mock_dispatch):
    mock_job = MagicMock()
    mock_job.status = "queued"
    mock_job.created_at = datetime.now(timezone.utc) - timedelta(minutes=2)

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_job

    assert job_dispatch.maybe_redispatch_stale_job(mock_db, "job_abc") is True
    mock_dispatch.assert_called_once_with("job_abc", background_tasks=None)


@patch("app.services.job_dispatch.dispatch_process_job")
def test_maybe_redispatch_skips_recent_queued(mock_dispatch):
    mock_job = MagicMock()
    mock_job.status = "queued"
    mock_job.created_at = datetime.now(timezone.utc) - timedelta(seconds=10)

    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_job

    assert job_dispatch.maybe_redispatch_stale_job(mock_db, "job_abc") is False
    mock_dispatch.assert_not_called()
