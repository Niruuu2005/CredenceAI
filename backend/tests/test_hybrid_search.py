import pytest
from app.services.reranker import Reranker
from app.services.search_index import SearchIndexClient
from app.services.benchmark_runner import BenchmarkRunner
from app.services.repository import create_job, create_normalized_result
from app.models import NormalizedResult

def test_reranker_basic():
    """Test Reranker correctly scores and ranks candidate documents."""
    reranker = Reranker()
    
    candidates = [
        {"title": "Unrelated topic page", "snippet": "Bananas are yellow fruit.", "quality_score": 0.8},
        {"title": "Open Source Search Engine", "snippet": "SearXNG is a free search engine aggregator.", "quality_score": 0.7}
    ]
    
    ranked = reranker.rerank("open source search", candidates, top_n=2)
    assert len(ranked) == 2
    # The search engine page should have higher score than banana page
    assert ranked[0]["title"] == "Open Source Search Engine"
    assert ranked[0]["rerank_score"] > ranked[1]["rerank_score"]

def test_hybrid_search_with_mock_data(db_session):
    """Test SearchIndexClient.hybrid_search with database fallback results."""
    # Populate DB with normalized results
    job = create_job(
        db=db_session,
        job_id="job_hs_123",
        trace_id="trace_hs_123",
        job_type="search_query",
        input_val="open source search",
        vertical="web"
    )
    
    create_normalized_result(
        db=db_session,
        normalized_result_id="res_hs_1",
        job_id=job.id,
        source_result_id="src_hs_1",
        title="SearXNG Engine Info",
        url="https://github.com/searxng/searxng",
        source="searxng",
        snippet="SearXNG is an open source engine."
    )
    
    create_normalized_result(
        db=db_session,
        normalized_result_id="res_hs_2",
        job_id=job.id,
        source_result_id="src_hs_1",
        title="Unrelated Fruit Page",
        url="https://fruit.com",
        source="searxng",
        snippet="This page talks about apple fruit varieties."
    )
    
    client = SearchIndexClient()
    # Test hybrid search
    results = client.hybrid_search("open source engine", db=db_session)
    assert len(results) >= 1
    assert results[0]["title"] == "SearXNG Engine Info"
    assert "ranking_details" in results[0]
    rd = results[0]["ranking_details"]
    assert rd["base_score"] == 1.0
    assert rd["jaccard_similarity"] > 0.0
    assert "phrase_boost" in rd
    assert rd["final_score"] > 0.0
    assert rd["formula"] == "0.4 * base_score + 0.6 * jaccard_similarity"
    
    # Test filters
    filtered_results = client.hybrid_search("open source engine", db=db_session, filters={"source": "wikipedia"})
    assert len(filtered_results) == 0

def test_benchmark_runner(db_session):
    """Test BenchmarkRunner computes metrics correctly."""
    # Seed DB with some expected result URLs
    job = create_job(
        db=db_session,
        job_id="job_bench_1",
        trace_id="trace_bench_1",
        job_type="search_query",
        input_val="open source search engines",
        vertical="web"
    )
    
    create_normalized_result(
        db=db_session,
        normalized_result_id="res_b1",
        job_id=job.id,
        source_result_id="src_b1",
        title="Mocked Search Result",
        url="https://mocked-result.com",
        source="google",
        snippet="We have a query match here."
    )
    
    runner = BenchmarkRunner(db=db_session)
    report = runner.run_benchmark(use_hybrid=True)
    
    assert "summary" in report
    assert report["summary"]["total_queries"] > 0
    assert "average_precision" in report["summary"]
    assert len(report["details"]) > 0
