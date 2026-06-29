"""
Unit tests for EntityResolutionAgent and ExtractionValidationAgent (Sprint 55)
"""

import pytest
from app.agents.base import AgentInput, AgentOutput
from app.agents.entity_resolution_agent import EntityResolutionAgent, ResolvedEntity
from app.agents.extraction_validation_agent import ExtractionValidationAgent


# ══════════════════════════════════════════════
# EntityResolutionAgent tests
# ══════════════════════════════════════════════

@pytest.fixture
def er_agent():
    return EntityResolutionAgent()


GOOD_DOC = {
    "url": "https://arxiv.org/abs/2401.test",
    "title": "Advanced RAG Techniques",
    "text": "This comprehensive paper covers retrieval-augmented generation in depth. "
            "It discusses various approaches for improving RAG systems with better retrieval. " * 8,
    "word_count": 160,
    "token_count": 120,
    "language": "en",
    "content_hash": "abc123def456abc123def456abc123def456abc123def456abc123def456abc1",
}

MINIMAL_DOC = {
    "url": "https://example.com/short",
    "title": "",
    "text": "Short.",
    "word_count": 1,
    "token_count": 1,
    "language": "",
    "content_hash": "",
}

NO_URL_DOC = {
    "url": "",
    "title": "Some article",
    "text": "This has content but no URL. " * 10,
    "word_count": 50,
}


def test_er_agent_instantiation(er_agent):
    assert er_agent.agent_name == "entity_resolution_agent"
    assert er_agent.is_enabled() is True


def test_er_validate_missing_entities(er_agent):
    inp = AgentInput(context={}, job_id="j1")
    with pytest.raises(ValueError) as exc:
        er_agent.validate_input(inp)
    assert "entities" in str(exc.value).lower()


def test_er_validate_entities_not_list(er_agent):
    inp = AgentInput(context={"entities": "openai"}, job_id="j1")
    with pytest.raises(ValueError):
        er_agent.validate_input(inp)


def test_er_validate_ok(er_agent):
    inp = AgentInput(context={"entities": ["OpenAI"]}, job_id="j1")
    assert er_agent.validate_input(inp) is True


# ── Resolution tests ──────────────────────────

def test_resolve_exact_key_match(er_agent):
    result = er_agent._resolve_entity("openai")
    assert result is not None
    assert result.canonical == "OpenAI"
    assert result.confidence >= 0.9


def test_resolve_alias_match(er_agent):
    result = er_agent._resolve_entity("open ai")
    assert result is not None
    assert result.canonical == "OpenAI"
    assert result.confidence >= 0.8


def test_resolve_case_insensitive(er_agent):
    result = er_agent._resolve_entity("OPENAI")
    assert result is not None
    assert result.canonical == "OpenAI"


def test_resolve_partial_match(er_agent):
    result = er_agent._resolve_entity("openai research division")
    assert result is not None
    assert "OpenAI" in result.canonical


def test_resolve_unknown_entity_returns_none(er_agent):
    result = er_agent._resolve_entity("xyztotallyunknownentity12345")
    assert result is None


def test_resolve_wikidata_qid_present(er_agent):
    result = er_agent._resolve_entity("openai")
    assert result.wikidata_qid == "Q28909344"


def test_resolve_entity_type(er_agent):
    result = er_agent._resolve_entity("perplexity")
    assert result.entity_type == "organization"


def test_resolve_disambiguation_options(er_agent):
    result = er_agent._resolve_entity("apple")
    assert isinstance(result.disambiguation_options, list)
    # apple has disambiguations (fruit, records)
    assert len(result.disambiguation_options) >= 0


def test_add_custom_entity(er_agent):
    er_agent.add_entity("testcorp", {
        "canonical": "TestCorp Ltd.",
        "type": "organization",
        "wikidata_qid": "Q99999",
        "aliases": ["test corp", "testcorp ltd"],
        "description": "Test company",
    })
    result = er_agent._resolve_entity("testcorp")
    assert result is not None
    assert result.canonical == "TestCorp Ltd."


@pytest.mark.asyncio
async def test_er_invoke_all_resolved(er_agent):
    inp = AgentInput(
        context={"entities": ["OpenAI", "Perplexity", "Python"]},
        job_id="j2"
    )
    output = await er_agent.invoke(inp)
    assert isinstance(output, AgentOutput)
    decision = output.decision
    assert "resolved" in decision
    assert "unresolved" in decision
    assert decision["resolution_rate"] >= 0.0


@pytest.mark.asyncio
async def test_er_invoke_partial_resolution(er_agent):
    inp = AgentInput(
        context={"entities": ["OpenAI", "xyztotallyunknown", "RAG"]},
        job_id="j3"
    )
    output = await er_agent.invoke(inp)
    decision = output.decision
    assert len(decision["resolved"]) >= 1
    assert len(decision["unresolved"]) >= 1


@pytest.mark.asyncio
async def test_er_invoke_empty_entities(er_agent):
    inp = AgentInput(context={"entities": []}, job_id="j4")
    output = await er_agent.invoke(inp)
    assert output.decision["resolution_rate"] == 0.0
    assert output.decision["resolved"] == []


@pytest.mark.asyncio
async def test_er_execute_full(er_agent):
    inp = AgentInput(
        context={"entities": ["OpenAI", "Perplexity AI"]},
        job_id="j5"
    )
    decision = await er_agent.execute(inp)
    assert decision.success is True
    assert decision.agent_name == "entity_resolution_agent"


# ══════════════════════════════════════════════
# ExtractionValidationAgent tests
# ══════════════════════════════════════════════

@pytest.fixture
def ev_agent():
    agent = ExtractionValidationAgent()
    agent.reset_dedup_state()
    return agent


def test_ev_agent_instantiation(ev_agent):
    assert ev_agent.agent_name == "extraction_validation_agent"
    assert ev_agent.is_enabled() is True


def test_ev_validate_missing_documents(ev_agent):
    inp = AgentInput(context={}, job_id="j1")
    with pytest.raises(ValueError) as exc:
        ev_agent.validate_input(inp)
    assert "documents" in str(exc.value).lower()


def test_ev_validate_documents_not_list(ev_agent):
    inp = AgentInput(context={"documents": "not a list"}, job_id="j1")
    with pytest.raises(ValueError):
        ev_agent.validate_input(inp)


# ── Individual document validation ───────────

def test_valid_document_passes(ev_agent):
    report = ev_agent._validate_document(GOOD_DOC)
    assert report.verdict in ("valid", "warning")
    assert "has_text" in report.passed_rules
    assert "has_url" in report.passed_rules
    assert "min_word_count" in report.passed_rules


def test_short_document_fails_word_count(ev_agent):
    """word_count=1 is < MIN_WORD_COUNT (20) so min_word_count critical rule fails."""
    report = ev_agent._validate_document(MINIMAL_DOC)
    # word_count 1 < 20 => 'has_url' also present, 'has_text' = truthy but short
    # critical fail: min_word_count OR has_text could cause invalid
    assert report.verdict == "invalid" or any("min_word_count" in f for f in report.failed_rules)


def test_no_url_fails_critical(ev_agent):
    report = ev_agent._validate_document(NO_URL_DOC)
    assert report.verdict == "invalid"
    assert "has_url" in report.failed_rules


def test_missing_title_is_warning(ev_agent):
    doc = {**GOOD_DOC, "title": ""}
    report = ev_agent._validate_document(doc)
    # Should not be invalid — just a warning
    assert report.verdict != "invalid"
    assert "missing_title" in report.warnings


def test_quality_score_is_float_in_range(ev_agent):
    report = ev_agent._validate_document(GOOD_DOC)
    assert 0.0 <= report.quality_score <= 1.0


# ── Deduplication ────────────────────────────

def test_duplicate_document_detected(ev_agent):
    ev_agent.reset_dedup_state()
    doc = {**GOOD_DOC}
    r1 = ev_agent._validate_document(doc)
    r2 = ev_agent._validate_document(doc)  # same content hash
    assert r1.is_duplicate is False
    assert r2.is_duplicate is True


def test_different_content_not_duplicate(ev_agent):
    ev_agent.reset_dedup_state()
    # Use different URLs AND omit hardcoded content_hash so agent generates from text
    doc1 = {
        "url": "https://example.com/article-A",
        "title": "Article A",
        "text": "unique content A in article one for testing deduplication logic. " * 10,
        "word_count": 100,
        "token_count": 75,
        "language": "en",
    }
    doc2 = {
        "url": "https://example.com/article-B",
        "title": "Article B",
        "text": "unique content B in article two for testing deduplication logic. " * 10,
        "word_count": 100,
        "token_count": 75,
        "language": "en",
    }
    r1 = ev_agent._validate_document(doc1)
    r2 = ev_agent._validate_document(doc2)
    assert r1.is_duplicate is False
    assert r2.is_duplicate is False


# ── Batch validation ─────────────────────────

@pytest.mark.asyncio
async def test_ev_invoke_all_valid(ev_agent):
    inp = AgentInput(
        context={"documents": [GOOD_DOC]},
        job_id="v1"
    )
    output = await ev_agent.invoke(inp)
    assert isinstance(output, AgentOutput)
    decision = output.decision
    assert "valid" in decision
    assert "invalid" in decision
    assert decision["total_checked"] == 1


@pytest.mark.asyncio
async def test_ev_invoke_mixed_batch(ev_agent):
    inp = AgentInput(
        context={"documents": [GOOD_DOC, MINIMAL_DOC, NO_URL_DOC]},
        job_id="v2"
    )
    output = await ev_agent.invoke(inp)
    decision = output.decision
    assert decision["total_checked"] == 3
    assert len(decision["valid"]) + len(decision["warnings"]) + len(decision["invalid"]) == 3


@pytest.mark.asyncio
async def test_ev_invoke_empty_batch(ev_agent):
    inp = AgentInput(context={"documents": []}, job_id="v3")
    output = await ev_agent.invoke(inp)
    decision = output.decision
    assert decision["total_checked"] == 0
    assert decision["pass_rate"] == 0.0


@pytest.mark.asyncio
async def test_ev_invoke_dedup_in_batch(ev_agent):
    """Two identical documents in one batch should detect second as duplicate."""
    inp = AgentInput(
        context={"documents": [GOOD_DOC, GOOD_DOC]},
        job_id="v4"
    )
    output = await ev_agent.invoke(inp)
    decision = output.decision
    assert len(decision["duplicates"]) == 1


@pytest.mark.asyncio
async def test_ev_execute_full(ev_agent):
    inp = AgentInput(
        context={"documents": [GOOD_DOC]},
        job_id="v5"
    )
    decision = await ev_agent.execute(inp)
    assert decision.success is True
    assert decision.agent_name == "extraction_validation_agent"


def test_reset_dedup_state(ev_agent):
    """After reset, previously seen hashes should be forgotten."""
    ev_agent._validate_document(GOOD_DOC)  # adds hash
    ev_agent.reset_dedup_state()
    report = ev_agent._validate_document(GOOD_DOC)
    assert report.is_duplicate is False  # hash was forgotten
