"""Tests for background job dispatch when CELERY_ALWAYS_EAGER is set."""
import pytest
from unittest.mock import MagicMock, patch

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
def test_dispatch_async_uses_celery_delay(mock_process_job, mock_settings):
    mock_settings.CELERY_ALWAYS_EAGER = False

    job_dispatch.dispatch_process_job("job_abc", None)

    mock_process_job.delay.assert_called_once_with("job_abc")


@patch("app.services.job_dispatch.settings")
@patch("app.worker.process_job")
def test_dispatch_async_raises_job_enqueue_error(mock_process_job, mock_settings):
    mock_settings.CELERY_ALWAYS_EAGER = False
    mock_process_job.delay.side_effect = ValueError("rediss ssl_cert_reqs")

    with pytest.raises(job_dispatch.JobEnqueueError) as exc_info:
        job_dispatch.dispatch_process_job("job_abc", None)

    assert exc_info.value.job_id == "job_abc"
