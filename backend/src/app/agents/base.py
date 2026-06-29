"""
Base Agent Architecture for CredenceAI Iteration 0.4

This module provides the abstract base class for all AI agents in the system.
Agents are designed to assist with ambiguous, high-value, and synthesis-heavy
decisions while maintaining strict governance boundaries.

Key Principles:
- Agents cannot bypass security policies (robots.txt, SSRF, MIME validation)
- All agent decisions must be logged with full context
- Agents operate within budget constraints
- Graceful fallback when AI is unavailable
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class AgentInput(BaseModel):
    """
    Standard input structure for all agents.
    
    Attributes:
        context: Domain-specific data needed for the agent decision
        job_id: Job identifier for tracking and logging
        user_request: Original user query or goal (optional)
        metadata: Additional contextual information
    """
    context: Dict[str, Any]
    job_id: str
    user_request: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentOutput(BaseModel):
    """
    Standard output structure for all agents.
    
    Attributes:
        decision: The agent's primary decision or recommendation
        reasoning: Explanation of why the agent made this decision
        confidence_score: Confidence level (0.0 to 1.0)
        alternative_options: Other viable options considered (optional)
        metadata: Additional output data
    """
    decision: Any
    reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    alternative_options: Optional[list] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentDecision(BaseModel):
    """
    Complete record of an agent decision for logging and audit.
    
    Attributes:
        agent_name: Name of the agent that made the decision
        job_id: Job identifier
        input_data: Input provided to the agent
        output_data: Output produced by the agent
        reasoning: Explanation of the decision
        confidence_score: Confidence level
        execution_time_ms: Time taken to execute (milliseconds)
        timestamp: When the decision was made
        success: Whether the agent execution succeeded
        error_message: Error details if execution failed
    """
    agent_name: str
    job_id: str
    input_data: Dict[str, Any]
    output_data: Optional[Dict[str, Any]] = None
    reasoning: str
    confidence_score: float = Field(ge=0.0, le=1.0)
    execution_time_ms: Optional[int] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    success: bool = True
    error_message: Optional[str] = None


class BaseAgent(ABC):
    """
    Abstract base class for all AI agents in CredenceAI.
    
    All agents must implement:
    - validate_input(): Verify input meets agent requirements
    - invoke(): Execute the agent's core logic
    - parse_output(): Structure the agent's raw output
    
    Subclasses should set:
    - agent_name: Unique identifier for the agent
    - agent_description: Human-readable description
    """
    
    agent_name: str = "BaseAgent"
    agent_description: str = "Abstract base agent"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the agent with optional configuration.
        
        Args:
            config: Agent-specific configuration parameters
        """
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)
    
    @abstractmethod
    def validate_input(self, agent_input: AgentInput) -> bool:
        """
        Validate that the input meets the agent's requirements.
        
        Args:
            agent_input: Input data for the agent
            
        Returns:
            True if input is valid, False otherwise
            
        Raises:
            ValueError: If input is invalid with explanation
        """
        pass
    
    @abstractmethod
    async def invoke(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute the agent's core decision-making logic.
        
        This is the main entry point for agent execution. It should:
        1. Process the input context
        2. Make the agent's decision (may involve LLM calls)
        3. Generate reasoning and confidence scores
        4. Return structured output
        
        Args:
            agent_input: Input data for the agent
            
        Returns:
            AgentOutput with decision, reasoning, and confidence
            
        Raises:
            Exception: If agent execution fails
        """
        pass
    
    @abstractmethod
    def parse_output(self, raw_output: Any) -> AgentOutput:
        """
        Parse and validate the agent's raw output into structured form.
        
        This method handles:
        - Parsing LLM responses (JSON, text, etc.)
        - Validating output schema
        - Extracting reasoning and confidence
        - Handling malformed outputs
        
        Args:
            raw_output: Raw response from LLM or processing logic
            
        Returns:
            Structured AgentOutput
            
        Raises:
            ValueError: If output cannot be parsed
        """
        pass
    
    async def execute(self, agent_input: AgentInput) -> AgentDecision:
        """
        Execute the full agent workflow with logging and error handling.
        
        This is the public API for invoking agents. It handles:
        - Input validation
        - Agent execution
        - Output parsing
        - Timing and logging
        - Error handling
        
        Args:
            agent_input: Input data for the agent
            
        Returns:
            AgentDecision with complete execution record
        """
        start_time = datetime.now(timezone.utc)
        decision = AgentDecision(
            agent_name=self.agent_name,
            job_id=agent_input.job_id,
            input_data=agent_input.model_dump(),
            reasoning="",
            confidence_score=0.0,
            timestamp=start_time,
        )
        
        try:
            # Step 1: Validate input
            if not self.validate_input(agent_input):
                raise ValueError(f"Invalid input for agent {self.agent_name}")
            
            # Step 2: Invoke agent logic
            output = await self.invoke(agent_input)
            
            # Step 3: Record results
            decision.output_data = output.model_dump()
            decision.reasoning = output.reasoning
            decision.confidence_score = output.confidence_score
            decision.success = True
            
        except Exception as e:
            # Handle errors gracefully
            decision.success = False
            decision.error_message = str(e)
            decision.reasoning = f"Agent execution failed: {str(e)}"
            decision.confidence_score = 0.0
        
        finally:
            # Calculate execution time
            end_time = datetime.now(timezone.utc)
            decision.execution_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        return decision
    
    def is_enabled(self) -> bool:
        """Check if the agent is enabled."""
        return self.enabled
    
    def get_name(self) -> str:
        """Get the agent's unique name."""
        return self.agent_name
    
    def get_description(self) -> str:
        """Get the agent's description."""
        return self.agent_description
