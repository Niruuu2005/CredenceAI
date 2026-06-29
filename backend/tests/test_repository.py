from app.services.repository import (
    create_job,
    get_job,
    update_job_status,
    create_source_result,
    create_normalized_result,
    get_job_normalized_results
)

def test_job_crud(db_session):
    # Create job
    job = create_job(
        db=db_session,
        job_id="job_test_123",
        trace_id="trace_abc",
        job_type="search_query",
        input_val="AI platforms",
        vertical="web"
    )
    assert job.id == "job_test_123"
    assert job.status == "queued"
    assert job.trace_id == "trace_abc"

    # Get job
    fetched_job = get_job(db_session, "job_test_123")
    assert fetched_job is not None
    assert fetched_job.input == "AI platforms"

    # Update job
    updated = update_job_status(db_session, "job_test_123", "completed")
    assert updated.status == "completed"
    assert updated.completed_at is None

def test_source_and_normalized_results(db_session):
    # Create parent job
    create_job(
        db=db_session,
        job_id="job_test_456",
        trace_id="trace_def",
        job_type="search_query",
        input_val="Open source search"
    )

    # Create source result
    src_res = create_source_result(
        db=db_session,
        source_result_id="src_res_1",
        job_id="job_test_456",
        source="searxng",
        source_type="web",
        input_value="Open source search",
        status="success",
        confidence=0.9
    )
    assert src_res.id == "src_res_1"
    assert src_res.job_id == "job_test_456"

    # Create normalized result
    norm_res = create_normalized_result(
        db=db_session,
        normalized_result_id="norm_res_1",
        job_id="job_test_456",
        source_result_id="src_res_1",
        title="SearXNG Project",
        url="https://searxng.github.io",
        source="searxng",
        snippet="A free internet metasearch engine"
    )
    assert norm_res.id == "norm_res_1"
    assert norm_res.job_id == "job_test_456"

    # Get job's normalized results
    results = get_job_normalized_results(db_session, "job_test_456")
    assert len(results) == 1
    assert results[0].title == "SearXNG Project"
