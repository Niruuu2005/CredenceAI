"""
Unit tests for BaseAgent and related data models.
"""

import pytest
from datetime import datetime
from typing import Any
from app.agents.base import BaseAgent, AgentInput, AgentOutput, AgentDecision



# Test data models


def test_agent_input_creation():
    """Test AgentInput model creation and validation."""
    agent_input = AgentInput(
        context={"query": "test query", "source": "test"},
        job_id="job_123",
        user_request="find information about AI",
        metadata={"priority": "high"}
    )
    
    assert agent_input.context["query"] == "test query"
    assert agent_input.job_id == "job_123"
    assert agent_input.user_request == "find information about AI"
    assert agent_input.metadata["priority"] == "high"


def test_agent_input_minimal():
    """Test AgentInput with minimal required fields."""
    agent_input = AgentInput(
        context={},
        job_id="job_456"
    )
    
    assert agent_input.context == {}
    assert agent_input.job_id == "job_456"
    assert agent_input.user_request is None
    assert agent_input.metadata == {}


def test_agent_output_creation():
    """Test AgentOutput model creation and validation."""
    agent_output = AgentOutput(
        decision="approve",
        reasoning="High quality source with recent timestamp",
        confidence_score=0.85,
        alternative_options=["review", "reject"],
        metadata={"factors": ["freshness", "reliability"]}
    )
    
    assert agent_output.decision == "approve"
    assert agent_output.reasoning == "High quality source with recent timestamp"
    assert agent_output.confidence_score == 0.85
    assert agent_output.alternative_options == ["review", "reject"]
    assert agent_output.metadata["factors"] == ["freshness", "reliability"]


def test_agent_output_confidence_validation():
    """Test that confidence_score is validated to be between 0.0 and 1.0."""
    # Valid confidence scores
    AgentOutput(decision="test", reasoning="test", confidence_score=0.0)
    AgentOutput(decision="test", reasoning="test", confidence_score=0.5)
    AgentOutput(decision="test", reasoning="test", confidence_score=1.0)
    
    # Invalid confidence scores should raise validation error
    with pytest.raises(Exception):  # Pydantic ValidationError
        AgentOutput(decision="test", reasoning="test", confidence_score=1.5)
    
    with pytest.raises(Exception):  # Pydantic ValidationError
        AgentOutput(decision="test", reasoning="test", confidence_score=-0.1)


def test_agent_decision_creation():
    """Test AgentDecision model creation."""
    agent_decision = AgentDecision(
        agent_name="TestAgent",
        job_id="job_789",
        input_data={"query": "test"},
        output_data={"decision": "approve"},
        reasoning="Valid input",
        confidence_score=0.9,
        execution_time_ms=250,
        success=True
    )
    
    assert agent_decision.agent_name == "TestAgent"
    assert agent_decision.job_id == "job_789"
    assert agent_decision.success is True
    assert agent_decision.confidence_score == 0.9
    assert agent_decision.execution_time_ms == 250
    assert isinstance(agent_decision.timestamp, datetime)


def test_agent_decision_failure():
    """Test AgentDecision for failed execution."""
    agent_decision = AgentDecision(
        agent_name="TestAgent",
        job_id="job_999",
        input_data={"query": "test"},
        reasoning="Execution failed",
        confidence_score=0.0,
        success=False,
        error_message="LLM timeout"
    )
    
    assert agent_decision.success is False
    assert agent_decision.error_message == "LLM timeout"
    assert agent_decision.confidence_score == 0.0


# Test BaseAgent abstract class


class MockAgent(BaseAgent):
    """Mock agent implementation for testing."""
    
    agent_name = "MockAgent"
    agent_description = "Mock agent for testing"
    
    def validate_input(self, agent_input: AgentInput) -> bool:
        """Validate that context contains 'query' field."""
        if "query" not in agent_input.context:
            raise ValueError("Context must contain 'query' field")
        return True
    
    async def invoke(self, agent_input: AgentInput) -> AgentOutput:
        """Mock invoke that returns a simple decision."""
        query = agent_input.context.get("query", "")
        
        # Simple mock logic
        if "approve" in query.lower():
            decision = "approved"
            confidence = 0.9
        else:
            decision = "rejected"
            confidence = 0.7
        
        return AgentOutput(
            decision=decision,
            reasoning=f"Decision based on query: {query}",
            confidence_score=confidence
        )
    
    def parse_output(self, raw_output: Any) -> AgentOutput:
        """Mock parse_output."""
        if isinstance(raw_output, AgentOutput):
            return raw_output
        return AgentOutput(
            decision=str(raw_output),
            reasoning="Parsed from raw output",
            confidence_score=0.5
        )


@pytest.mark.asyncio
async def test_base_agent_instantiation():
    """Test that BaseAgent can be instantiated through a concrete subclass."""
    agent = MockAgent()
    
    assert agent.agent_name == "MockAgent"
    assert agent.agent_description == "Mock agent for testing"
    assert agent.is_enabled() is True


@pytest.mark.asyncio
async def test_base_agent_with_config():
    """Test agent initialization with configuration."""
    config = {"enabled": False, "max_retries": 3}
    agent = MockAgent(config=config)
    
    assert agent.is_enabled() is False
    assert agent.config["max_retries"] == 3


@pytest.mark.asyncio
async def test_agent_execute_success():
    """Test successful agent execution workflow."""
    agent = MockAgent()
    agent_input = AgentInput(
        context={"query": "approve this request"},
        job_id="job_success_123"
    )
    
    decision = await agent.execute(agent_input)
    
    assert decision.agent_name == "MockAgent"
    assert decision.job_id == "job_success_123"
    assert decision.success is True
    assert decision.output_data is not None
    assert decision.output_data["decision"] == "approved"
    assert decision.confidence_score == 0.9
    assert decision.reasoning is not None
    assert decision.execution_time_ms is not None
    assert decision.execution_time_ms >= 0  # may be 0ms on fast machines
    assert decision.error_message is None


@pytest.mark.asyncio
async def test_agent_execute_input_validation_failure():
    """Test agent execution with invalid input."""
    agent = MockAgent()
    agent_input = AgentInput(
        context={},  # Missing required 'query' field
        job_id="job_invalid_123"
    )
    
    decision = await agent.execute(agent_input)
    
    assert decision.success is False
    assert decision.error_message is not None
    assert "query" in decision.error_message.lower()
    assert decision.confidence_score == 0.0
    assert decision.execution_time_ms is not None


class FailingAgent(BaseAgent):
    """Mock agent that always fails during invoke."""
    
    agent_name = "FailingAgent"
    agent_description = "Agent that fails for testing"
    
    def validate_input(self, agent_input: AgentInput) -> bool:
        return True
    
    async def invoke(self, agent_input: AgentInput) -> AgentOutput:
        raise RuntimeError("Simulated agent failure")
    
    def parse_output(self, raw_output: Any) -> AgentOutput:
        return AgentOutput(
            decision="error",
            reasoning="Should not reach here",
            confidence_score=0.0
        )


@pytest.mark.asyncio
async def test_agent_execute_invoke_failure():
    """Test agent execution when invoke() raises exception."""
    agent = FailingAgent()
    agent_input = AgentInput(
        context={"query": "test"},
        job_id="job_fail_123"
    )
    
    decision = await agent.execute(agent_input)
    
    assert decision.success is False
    assert decision.error_message is not None
    assert "Simulated agent failure" in decision.error_message
    assert decision.confidence_score == 0.0


@pytest.mark.asyncio
async def test_agent_get_methods():
    """Test agent getter methods."""
    agent = MockAgent()
    
    assert agent.get_name() == "MockAgent"
    assert agent.get_description() == "Mock agent for testing"
    assert agent.is_enabled() is True


@pytest.mark.asyncio
async def test_agent_disabled():
    """Test agent behavior when disabled."""
    agent = MockAgent(config={"enabled": False})
    
    assert agent.is_enabled() is False
    # Agent can still be executed even if disabled - the caller should check is_enabled()
