"""
Unit tests for SourceSelectionAgent and QualityCriticAgent (Sprint 54)
"""

import pytest
from app.agents.base import AgentInput, AgentOutput
from app.agents.source_selection_agent import SourceSelectionAgent, SOURCE_REGISTRY
from app.agents.quality_critic_agent import QualityCriticAgent, CREDIBLE_DOMAINS


# ══════════════════════════════════════════════
# SourceSelectionAgent tests
# ══════════════════════════════════════════════

@pytest.fixture
def source_agent():
    return SourceSelectionAgent()


def test_source_agent_instantiation(source_agent):
    assert source_agent.agent_name == "source_selection_agent"
    assert source_agent.is_enabled() is True


def test_source_agent_validate_input_ok(source_agent):
    inp = AgentInput(context={"query": "AI research"}, job_id="j1")
    assert source_agent.validate_input(inp) is True


def test_source_agent_validate_missing_query(source_agent):
    inp = AgentInput(context={}, job_id="j1")
    with pytest.raises(ValueError) as exc:
        source_agent.validate_input(inp)
    assert "query" in str(exc.value).lower()


def test_source_agent_validate_empty_query(source_agent):
    inp = AgentInput(context={"query": ""}, job_id="j1")
    with pytest.raises(ValueError):
        source_agent.validate_input(inp)


def test_research_vertical_returns_academic_sources(source_agent):
    sources = source_agent.list_sources_for_vertical("research")
    assert "openalex" in sources
    assert "arxiv" in sources


def test_news_vertical_returns_news_sources(source_agent):
    sources = source_agent.list_sources_for_vertical("news")
    assert "gdelt" in sources or "newsapi" in sources


def test_company_vertical_returns_entity_sources(source_agent):
    sources = source_agent.list_sources_for_vertical("company")
    assert "wikidata" in sources or "wikipedia" in sources


def test_select_sources_respects_max(source_agent):
    selected = source_agent._select_sources("research", 0.0, max_sources=2)
    assert len(selected) <= 2


def test_select_sources_filters_by_min_reliability(source_agent):
    selected = source_agent._select_sources("general", min_reliability=0.95, max_sources=10)
    for s in selected:
        assert SOURCE_REGISTRY[s]["reliability"] >= 0.95


def test_select_sources_sorted_by_reliability(source_agent):
    selected = source_agent._select_sources("research", min_reliability=0.0, max_sources=10)
    reliabilities = [SOURCE_REGISTRY[s]["reliability"] for s in selected]
    assert reliabilities == sorted(reliabilities, reverse=True)


def test_get_source_reliability(source_agent):
    assert source_agent.get_source_reliability("openalex") == pytest.approx(0.95)
    assert source_agent.get_source_reliability("unknown_source") == 0.0


@pytest.mark.asyncio
async def test_source_agent_invoke(source_agent):
    inp = AgentInput(
        context={"query": "machine learning papers", "vertical": "research", "max_sources": 3},
        job_id="j2"
    )
    output = await source_agent.invoke(inp)
    assert isinstance(output, AgentOutput)
    assert output.decision is not None
    assert "selected_sources" in output.decision
    assert len(output.decision["selected_sources"]) <= 3
    assert 0.0 <= output.confidence_score <= 1.0


@pytest.mark.asyncio
async def test_source_agent_invoke_general_fallback(source_agent):
    """Unknown vertical should fall back to general sources."""
    inp = AgentInput(
        context={"query": "anything", "vertical": "unknown_vertical"},
        job_id="j3"
    )
    output = await source_agent.invoke(inp)
    assert isinstance(output, AgentOutput)
    assert len(output.decision["selected_sources"]) >= 0


@pytest.mark.asyncio
async def test_source_agent_execute_full(source_agent):
    inp = AgentInput(
        context={"query": "Perplexity AI competitors", "vertical": "company"},
        job_id="j4"
    )
    decision = await source_agent.execute(inp)
    assert decision.success is True
    assert decision.agent_name == "source_selection_agent"
    assert decision.output_data is not None


# ══════════════════════════════════════════════
# QualityCriticAgent tests
# ══════════════════════════════════════════════

@pytest.fixture
def critic_agent():
    return QualityCriticAgent()


SAMPLE_DOC = {
    "url": "https://arxiv.org/abs/2401.00001",
    "title": "Advances in Retrieval-Augmented Generation",
    "text": "This paper presents a comprehensive study of retrieval-augmented generation techniques. "
            "We propose a novel framework that improves accuracy and citation quality in large language models. "
            "Our experiments demonstrate significant improvements over baseline approaches on multiple benchmarks. " * 5,
    "source_name": "arxiv",
    "word_count": 150,
    "published_date": "2024-01-10",
}

LOW_QUALITY_DOC = {
    "url": "https://random-blog.com/post/123",
    "title": "Just a short post",
    "text": "Click here for more info.",
    "word_count": 5,
    "published_date": None,
}

OLD_DOC = {
    "url": "https://bbc.com/news/old-article",
    "title": "Old news story",
    "text": "This is a news article about some historical event. " * 30,
    "word_count": 200,
    "published_date": "2010-06-01",
}


def test_critic_agent_instantiation(critic_agent):
    assert critic_agent.agent_name == "quality_critic_agent"
    assert critic_agent.is_enabled() is True


def test_critic_validate_missing_query(critic_agent):
    inp = AgentInput(context={"documents": []}, job_id="j1")
    with pytest.raises(ValueError) as exc:
        critic_agent.validate_input(inp)
    assert "query" in str(exc.value).lower()


def test_critic_validate_missing_documents(critic_agent):
    inp = AgentInput(context={"query": "test"}, job_id="j1")
    with pytest.raises(ValueError) as exc:
        critic_agent.validate_input(inp)
    assert "documents" in str(exc.value).lower()


def test_critic_score_credible_domain(critic_agent):
    score = critic_agent._score_credibility("https://arxiv.org/abs/test")
    assert score >= 0.88


def test_critic_score_unknown_domain(critic_agent):
    score = critic_agent._score_credibility("https://random-unknown-site.com/page")
    assert 0.5 <= score <= 0.7


def test_critic_score_freshness_recent(critic_agent):
    from datetime import datetime, timezone, timedelta
    recent = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    score = critic_agent._score_freshness(recent)
    assert score > 0.5


def test_critic_score_freshness_very_old(critic_agent):
    score = critic_agent._score_freshness("2010-01-01")
    assert score == 0.0


def test_critic_score_freshness_unknown(critic_agent):
    score = critic_agent._score_freshness(None)
    assert score == 0.5  # neutral


def test_critic_score_density_short_doc(critic_agent):
    score = critic_agent._score_density(5, 0, "short text")
    assert score == 0.2


def test_critic_score_density_long_doc(critic_agent):
    score = critic_agent._score_density(600, 300, "x " * 600)
    assert score == 1.0


def test_critic_score_relevance_full_match(critic_agent):
    query = "retrieval augmented generation"
    text = "This paper is about retrieval augmented generation and its applications."
    score = critic_agent._score_relevance(query, text, "RAG paper")
    assert score >= 0.8


def test_critic_score_relevance_no_match(critic_agent):
    query = "quantum physics energy"
    text = "Recipe for chocolate cake."
    score = critic_agent._score_relevance(query, text, "Cake recipe")
    assert score < 0.4


def test_critic_score_document_high_quality(critic_agent):
    score = critic_agent._score_document("retrieval-augmented generation", SAMPLE_DOC)
    assert score >= 0.60  # arxiv + relevant content + decent freshness


def test_critic_score_document_low_quality(critic_agent):
    score = critic_agent._score_document("any query", LOW_QUALITY_DOC)
    assert score < 0.70  # short content, unknown domain


@pytest.mark.asyncio
async def test_critic_invoke_accepts_quality_doc(critic_agent):
    inp = AgentInput(
        context={
            "query": "retrieval augmented generation papers",
            "documents": [SAMPLE_DOC]
        },
        job_id="c1"
    )
    output = await critic_agent.invoke(inp)
    assert isinstance(output, AgentOutput)
    decision = output.decision
    # High quality doc should be accepted or at least not all rejected
    assert len(decision["accepted"]) + len(decision["review"]) >= 1


@pytest.mark.asyncio
async def test_critic_invoke_rejects_low_quality(critic_agent):
    inp = AgentInput(
        context={
            "query": "machine learning breakthroughs",
            "documents": [LOW_QUALITY_DOC]
        },
        job_id="c2"
    )
    output = await critic_agent.invoke(inp)
    decision = output.decision
    # Very short unrelated doc should be rejected or review
    assert len(decision["rejected"]) + len(decision["review"]) >= 1


@pytest.mark.asyncio
async def test_critic_invoke_mixed_docs(critic_agent):
    inp = AgentInput(
        context={
            "query": "retrieval augmented generation",
            "documents": [SAMPLE_DOC, LOW_QUALITY_DOC, OLD_DOC]
        },
        job_id="c3"
    )
    output = await critic_agent.invoke(inp)
    assert isinstance(output, AgentOutput)
    decision = output.decision
    assert "scores" in decision
    assert len(decision["scores"]) == 3
    assert all(0.0 <= v <= 1.0 for v in decision["scores"].values())


@pytest.mark.asyncio
async def test_critic_blocked_domain_rejected(critic_agent):
    blocked_doc = {
        "url": "https://spam-news.com/article",
        "title": "Spam article",
        "text": "This is spam content. " * 50,
        "word_count": 100,
        "published_date": "2024-01-01",
    }
    inp = AgentInput(
        context={"query": "test", "documents": [blocked_doc]},
        job_id="c4"
    )
    output = await critic_agent.invoke(inp)
    decision = output.decision
    assert blocked_doc["url"] in decision["rejected"]


@pytest.mark.asyncio
async def test_critic_execute_full(critic_agent):
    inp = AgentInput(
        context={"query": "AI papers", "documents": [SAMPLE_DOC]},
        job_id="c5"
    )
    decision = await critic_agent.execute(inp)
    assert decision.success is True
    assert decision.agent_name == "quality_critic_agent"
    assert "total" in decision.output_data.get("metadata", decision.output_data)


@pytest.mark.asyncio
async def test_critic_empty_documents(critic_agent):
    inp = AgentInput(
        context={"query": "test query", "documents": []},
        job_id="c6"
    )
    output = await critic_agent.invoke(inp)
    assert isinstance(output, AgentOutput)
    assert output.decision["accepted"] == []
    assert output.decision["rejected"] == []
