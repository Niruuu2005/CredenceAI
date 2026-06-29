"""
Unit tests for PlannerAgent.
Aligned with actual planner_agent.py API (Sprint 54 fix).
"""

import pytest
from app.agents.planner_agent import PlannerAgent, PlannerInput, PlannerOutput, Job
from app.agents.base import AgentInput, AgentOutput


@pytest.fixture
def planner_agent():
    """Create a PlannerAgent instance for testing."""
    config = {
        "enabled": True,
        "model": "gpt-3.5-turbo",
        "temperature": 0.3,
        "max_tokens": 1000,
    }
    return PlannerAgent(config=config)


def test_planner_agent_instantiation(planner_agent):
    """Test that PlannerAgent can be instantiated."""
    assert planner_agent.agent_name == "planner_agent"
    assert "Decomposes" in planner_agent.agent_description
    assert planner_agent.is_enabled() is True


def test_planner_input_validation_success(planner_agent):
    """Test successful input validation."""
    agent_input = AgentInput(
        context={"user_goal": "Research Perplexity AI and its competitors"},
        job_id="job_123"
    )
    assert planner_agent.validate_input(agent_input) is True


def test_planner_input_validation_missing_goal(planner_agent):
    """Test input validation fails when user_goal is missing."""
    agent_input = AgentInput(
        context={},
        job_id="job_123"
    )
    with pytest.raises(ValueError) as exc_info:
        planner_agent.validate_input(agent_input)
    assert "user_goal" in str(exc_info.value).lower()


def test_planner_input_validation_empty_goal(planner_agent):
    """Test input validation fails when user_goal is empty."""
    agent_input = AgentInput(
        context={"user_goal": ""},
        job_id="job_123"
    )
    with pytest.raises(ValueError):
        planner_agent.validate_input(agent_input)


def test_planner_input_validation_short_goal(planner_agent):
    """Test input validation fails when user_goal is too short (< 3 chars)."""
    agent_input = AgentInput(
        context={"user_goal": "AI"},
        job_id="job_123"
    )
    with pytest.raises(ValueError) as exc_info:
        planner_agent.validate_input(agent_input)
    assert "too short" in str(exc_info.value).lower()


def test_job_model_creation():
    """Test Job model (the actual export from planner_agent)."""
    job = Job(
        job_type="search",
        description="Search for company info",
        priority=1,
        parameters={"query": "Perplexity AI"}
    )
    assert job.job_type == "search"
    assert job.description == "Search for company info"
    assert job.priority == 1
    assert job.parameters["query"] == "Perplexity AI"


def test_planner_output_model_creation():
    """Test PlannerOutput model."""
    job = Job(
        job_type="search",
        description="Search for company info",
        priority=1,
        parameters={}
    )
    output = PlannerOutput(
        jobs=[job],
        entities=["Perplexity AI", "OpenAI"],
        recommended_verticals=["company", "research"],
        success_metrics=["Find company information", "Identify competitors"],
        reasoning="User goal requires company research"
    )
    assert len(output.jobs) == 1
    assert output.jobs[0].job_type == "search"
    assert len(output.entities) == 2
    assert len(output.recommended_verticals) == 2
    assert len(output.success_metrics) == 2


def test_build_prompt_contains_goal(planner_agent):
    """_build_prompt should embed the user goal in the prompt."""
    prompt = planner_agent._build_prompt(
        user_goal="Research Perplexity AI",
        context={"previous_query": "AI search engines"},
        constraints={"time_limit": "24h"}
    )
    assert "Research Perplexity AI" in prompt
    assert "time_limit" in prompt


def test_build_prompt_with_empty_context(planner_agent):
    """_build_prompt handles empty context and constraints gracefully."""
    prompt = planner_agent._build_prompt(
        user_goal="Find AI papers",
        context="",
        constraints={}
    )
    assert "Find AI papers" in prompt
    assert isinstance(prompt, str)


def test_build_prompt_contains_json_guidance(planner_agent):
    """System prompt should reference JSON output format."""
    assert "JSON" in planner_agent.system_prompt
    assert "verticals" in planner_agent.system_prompt.lower() or "vertical" in planner_agent.system_prompt


def test_parse_output_valid_json(planner_agent):
    """Test parsing valid JSON output."""
    raw_output = """
    {
        "jobs": [
            {
                "job_type": "search",
                "description": "Search for company information",
                "priority": 1,
                "parameters": {}
            }
        ],
        "entities": ["Perplexity AI"],
        "recommended_verticals": ["company"],
        "success_metrics": ["Find company information"],
        "reasoning": "Company research required"
    }
    """
    output = planner_agent.parse_output(raw_output)
    assert isinstance(output, AgentOutput)
    assert output.decision is not None
    assert len(output.decision["jobs"]) == 1
    assert output.decision["entities"] == ["Perplexity AI"]


def test_parse_output_json_in_markdown(planner_agent):
    """Test parsing JSON embedded in markdown code block."""
    raw_output = """
    Here's the plan:

    ```json
    {
        "jobs": [{"job_type": "search", "description": "Search", "priority": 1, "parameters": {}}],
        "entities": [],
        "recommended_verticals": ["general"],
        "success_metrics": ["Find results"],
        "reasoning": "General search needed"
    }
    ```
    """
    output = planner_agent.parse_output(raw_output)
    assert isinstance(output, AgentOutput)
    assert output.decision is not None
    assert len(output.decision["jobs"]) == 1


def test_parse_output_invalid_json_returns_fallback(planner_agent):
    """Invalid JSON returns a fallback output (low confidence), does not raise."""
    raw_output = "This is not valid JSON at all"
    # The planner uses _create_fallback_output internally, returns AgentOutput
    output = planner_agent.parse_output(raw_output)
    assert isinstance(output, AgentOutput)
    # Fallback has very low confidence
    assert output.confidence_score <= 0.2


def test_create_fallback_output(planner_agent):
    """Test that _create_fallback_output returns properly structured AgentOutput."""
    fallback = planner_agent._create_fallback_output(
        raw_output="broken output",
        error_message="LLM timeout"
    )
    assert isinstance(fallback, AgentOutput)
    assert fallback.decision is not None
    assert isinstance(fallback.decision, dict)
    assert "jobs" in fallback.decision
    assert fallback.confidence_score <= 0.2
    assert fallback.decision.get("fallback") is True


def test_planner_is_enabled_by_default(planner_agent):
    """PlannerAgent should be enabled by default."""
    assert planner_agent.is_enabled() is True


def test_planner_agent_has_llm_client(planner_agent):
    """PlannerAgent should have a configured LLM client."""
    assert planner_agent.llm_client is not None


def test_planner_agent_system_prompt_not_empty(planner_agent):
    """System prompt should not be empty."""
    assert isinstance(planner_agent.system_prompt, str)
    assert len(planner_agent.system_prompt) > 50


@pytest.mark.asyncio
async def test_planner_agent_invoke_structure(planner_agent):
    """Test PlannerAgent invoke method returns properly structured AgentOutput."""
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_response = MagicMock()
    mock_response.content = """
    {
        "jobs": [{"job_type": "search", "description": "Search for Perplexity AI", "priority": 1, "parameters": {}}],
        "entities": ["Perplexity AI"],
        "recommended_verticals": ["company"],
        "success_metrics": ["Find company information"],
        "reasoning": "User wants to research a company"
    }
    """
    mock_response.tokens_used = 150
    mock_response.model = "gpt-3.5-turbo"

    agent_input = AgentInput(
        context={
            "user_goal": "Research Perplexity AI and its competitors",
            "context": {},
            "constraints": {}
        },
        job_id="job_456"
    )

    with patch.object(planner_agent.llm_client, "call_llm", new=AsyncMock(return_value=mock_response)):
        output = await planner_agent.invoke(agent_input)

    assert isinstance(output, AgentOutput)
    assert output.decision is not None
    assert isinstance(output.decision, dict)
    assert "jobs" in output.decision
    assert "entities" in output.decision
    assert 0.0 <= output.confidence_score <= 1.0


@pytest.mark.asyncio
async def test_planner_agent_execute_success(planner_agent):
    """Test full PlannerAgent execute workflow with mocked LLM."""
    from unittest.mock import AsyncMock, MagicMock, patch

    mock_response = MagicMock()
    mock_response.content = """
    {
        "jobs": [{"job_type": "search", "description": "Find RAG papers", "priority": 1, "parameters": {}}],
        "entities": ["RAG"],
        "recommended_verticals": ["research"],
        "success_metrics": ["Find at least 10 papers"],
        "reasoning": "Academic research required"
    }
    """
    mock_response.tokens_used = 120
    mock_response.model = "gpt-3.5-turbo"

    agent_input = AgentInput(
        context={"user_goal": "Find recent papers on retrieval-augmented generation"},
        job_id="job_789"
    )

    with patch.object(planner_agent.llm_client, "call_llm", new=AsyncMock(return_value=mock_response)):
        decision = await planner_agent.execute(agent_input)

    assert decision.agent_name == "planner_agent"
    assert decision.job_id == "job_789"
    assert decision.success is True
    assert decision.output_data is not None
    assert decision.execution_time_ms is not None
    assert decision.execution_time_ms >= 0  # may be 0ms on fast machines with mocked LLM
