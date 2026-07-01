"""
Planner Agent for CredenceAI Iteration 0.4

The Planner Agent decomposes ambiguous user goals into structured execution plans.
It identifies entities, selects appropriate verticals, recommends sources, and defines success metrics.

Activation Conditions:
- Ambiguous or complex queries
- Multi-step research goals
- Queries requiring decomposition into multiple jobs

Example Inputs:
- "Research Perplexity AI and its main competitors"
- "Track breaking news on climate policy for the next week"
- "Build a RAG dataset on AI safety research"

Example Outputs:
- List of jobs to execute (entity search, news monitoring, etc.)
- Entities to track
- Recommended verticals (company, research, news, RAG)
- Success metrics for evaluation
"""

import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from app.agents.base import BaseAgent, AgentInput, AgentOutput
from app.services.llm_client import LLMClient
from app.services.agent_output_parser import AgentOutputParser
from app.services.agent_config_manager import get_config_manager

logger = logging.getLogger(__name__)


class PlannerInput(BaseModel):
    """
    Input schema for Planner Agent.
    
    Attributes:
        user_goal: The user's research goal or question
        context: Optional additional context about the goal
        constraints: Optional constraints (time range, source preferences, etc.)
    """
    user_goal: str
    context: Optional[str] = None
    constraints: Optional[Dict[str, Any]] = Field(default_factory=dict)


class Job(BaseModel):
    """
    A single job in the execution plan.
    
    Attributes:
        job_type: Type of job (search, monitor, extract, analyze)
        description: What this job should accomplish
        parameters: Job-specific parameters
        priority: Execution priority (1=highest)
        dependencies: List of job IDs this depends on
    """
    job_type: str
    description: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1
    dependencies: List[str] = Field(default_factory=list)


class PlannerOutput(BaseModel):
    """
    Output schema for Planner Agent.
    
    Attributes:
        jobs: List of jobs to execute
        entities: Key entities mentioned in the goal
        recommended_verticals: Which vertical packs to use
        success_metrics: How to measure success
        reasoning: Explanation of the plan
    """
    jobs: List[Job]
    entities: List[str]
    recommended_verticals: List[str]
    success_metrics: List[str]
    reasoning: str


class PlannerAgent(BaseAgent):
    """
    Planner Agent for goal decomposition and execution planning.
    
    The agent uses an LLM to:
    1. Parse the user goal and identify key components
    2. Determine which entities need research
    3. Select appropriate verticals (company, research, news, RAG)
    4. Recommend sources for each entity/vertical combination
    5. Define success criteria
    6. Generate a structured execution plan
    """
    
    agent_name = "planner_agent"
    agent_description = "Decomposes user goals into structured execution plans"
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Planner Agent.
        
        Args:
            config: Optional configuration overrides
        """
        # Load configuration
        config_manager = get_config_manager()
        agent_config = config_manager.get_agent_config(self.agent_name)
        
        # Override with provided config
        if config:
            agent_config.update(config)
        
        super().__init__(config=agent_config)
        
        # Initialize LLM client
        self.llm_client = LLMClient(config={
            "model": self.config.get("model", "gpt-3.5-turbo"),
            "timeout": self.config.get("timeout", 30),
        })
        
        # Get system prompt from config
        self.system_prompt = self.config.get("system_prompt") or self._get_default_system_prompt()
        
        logger.info(f"Initialized {self.agent_name} with model {self.config.get('model')}")
    
    def _get_default_system_prompt(self) -> str:
        """Get default system prompt if not in config."""
        return """You are an intelligent planning agent for CredenceAI.
Your role is to decompose user goals into executable jobs.

For each goal:
1. Identify key entities mentioned (companies, people, topics, concepts)
2. Determine the best vertical pack:
   - company: For company research, competitor analysis, market intelligence
   - research: For academic papers, citations, author tracking
   - news: For breaking news, event tracking, story evolution
   - rag: For building curated document datasets
3. Recommend appropriate sources:
   - Scholarly research: OpenAlex, Crossref, arXiv, Google Scholar
   - Breaking news: GDELT, SearXNG news, news APIs
   - Entity lookup: Wikidata, Wikipedia
   - General web: SearXNG
4. Define success metrics

Output your plan as structured JSON with this format:
{
    "jobs": [
        {
            "job_type": "search|monitor|extract|analyze",
            "description": "What this job does",
            "parameters": {"entity": "...", "vertical": "...", "sources": [...]},
            "priority": 1,
            "dependencies": []
        }
    ],
    "entities": ["Entity1", "Entity2"],
    "recommended_verticals": ["company", "research"],
    "success_metrics": ["metric1", "metric2"],
    "reasoning": "Explanation of the plan"
}
"""
    
    def validate_input(self, agent_input: AgentInput) -> bool:
        """
        Validate that input contains a user goal.
        
        Args:
            agent_input: Input data for the agent
            
        Returns:
            True if valid, False otherwise
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Check that context contains user_goal
            if "user_goal" not in agent_input.context:
                raise ValueError("Missing required field: user_goal")
            
            user_goal = agent_input.context["user_goal"]
            
            # Validate user goal is non-empty string
            if not user_goal or not isinstance(user_goal, str):
                raise ValueError("user_goal must be a non-empty string")
            
            if len(user_goal.strip()) < 3:
                raise ValueError("user_goal is too short (minimum 3 characters)")
            
            return True
            
        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            raise ValueError(f"Invalid input for {self.agent_name}: {e}")
    
    async def invoke(self, agent_input: AgentInput) -> AgentOutput:
        """
        Execute planner agent logic using LLM.
        
        Args:
            agent_input: Input data with user goal
            
        Returns:
            AgentOutput with execution plan
            
        Raises:
            Exception: If planning fails
        """
        try:
            # Extract input data
            user_goal = agent_input.context["user_goal"]
            context = agent_input.context.get("context", "")
            constraints = agent_input.context.get("constraints", {})
            
            # Build prompt
            prompt = self._build_prompt(user_goal, context, constraints)
            
            logger.info(f"Invoking {self.agent_name} for goal: {user_goal[:100]}...")
            
            # Call LLM (retry once if JSON parsing fails)
            llm_response = await self.llm_client.call_llm(
                prompt=prompt,
                system_prompt=self.system_prompt,
                max_tokens=self.config.get("max_tokens", 1000),
                temperature=self.config.get("temperature", 0.2),
                response_format={"type": "json_object"},
            )

            logger.info(f"LLM response received, tokens used: {llm_response.tokens_used}")

            parsed_output = self.parse_output(llm_response.content)
            if parsed_output.metadata.get("fallback"):
                logger.warning(
                    "%s JSON parse failed; retrying once with stricter prompt",
                    self.agent_name,
                )
                retry_prompt = (
                    f"{prompt}\n\n"
                    "Respond with ONLY a single valid JSON object. "
                    "Use double quotes for all keys and string values. "
                    "No markdown, comments, or trailing commas."
                )
                llm_response = await self.llm_client.call_llm(
                    prompt=retry_prompt,
                    system_prompt=self.system_prompt,
                    max_tokens=self.config.get("max_tokens", 1000),
                    temperature=0.1,
                    response_format={"type": "json_object"},
                )
                parsed_output = self.parse_output(llm_response.content)
                parsed_output.metadata["tokens_used"] = (
                    parsed_output.metadata.get("tokens_used", 0) + llm_response.tokens_used
                )
                parsed_output.metadata["model"] = llm_response.model
            else:
                parsed_output.metadata["tokens_used"] = llm_response.tokens_used
                parsed_output.metadata["model"] = llm_response.model

            return parsed_output
            
        except Exception as e:
            logger.error(f"{self.agent_name} invocation failed: {e}")
            raise
    
    def _build_prompt(self, user_goal: str, context: str, constraints: Dict[str, Any]) -> str:
        """
        Build the prompt for the LLM.
        
        Args:
            user_goal: User's research goal
            context: Additional context
            constraints: Constraints on the plan
            
        Returns:
            Formatted prompt string
        """
        prompt_parts = [f"User Goal: {user_goal}"]
        
        if context:
            prompt_parts.append(f"\nAdditional Context: {context}")
        
        if constraints:
            prompt_parts.append(f"\nConstraints: {constraints}")
        
        prompt_parts.append("""
Create an execution plan for this goal. Your response must be valid JSON following the specified format.

Consider:
- What entities need to be researched?
- Which vertical pack(s) are most appropriate?
- What sources should be consulted?
- How should success be measured?
- What jobs need to be executed and in what order?

Remember:
- For company research: Use company vertical with Wikidata, Wikipedia, web search
- For academic topics: Use research vertical with OpenAlex, Crossref, arXiv
- For current events: Use news vertical with GDELT, news sources
- For dataset building: Use rag vertical with quality filtering
""")
        
        return "\n".join(prompt_parts)
    
    def parse_output(self, raw_output: Any) -> AgentOutput:
        """
        Parse LLM output into structured AgentOutput.
        
        Args:
            raw_output: Raw response from LLM
            
        Returns:
            Structured AgentOutput
            
        Raises:
            ValueError: If parsing fails
        """
        try:
            # Parse JSON from LLM response and validate against PlannerOutput schema
            parsed_data = AgentOutputParser.parse_json(raw_output, schema=PlannerOutput)
            
            # Validate we have at least some planning output
            jobs_data = parsed_data.get("jobs", [])
            entities = parsed_data.get("entities", [])
            if not jobs_data and not entities:
                raise ValueError("Plan must contain at least jobs or entities")

            # Construct PlannerOutput schema (already validated)
            planner_output = PlannerOutput(**parsed_data)
            
            # Calculate confidence based on completeness
            confidence = self._calculate_confidence(planner_output)
            
            # Build AgentOutput
            agent_output = AgentOutput(
                decision=planner_output.model_dump(),
                reasoning=planner_output.reasoning,
                confidence_score=confidence,
                metadata={
                    "num_jobs": len(planner_output.jobs),
                    "num_entities": len(planner_output.entities),
                    "verticals": planner_output.recommended_verticals,
                    "fallback": False,
                }
            )
            
            logger.info(
                f"Successfully parsed planner output: "
                f"{len(planner_output.jobs)} jobs, {len(planner_output.entities)} entities, "
                f"confidence={confidence:.2f}"
            )
            
            return agent_output
            
        except Exception as e:
            logger.error(f"Failed to parse planner output: {e}")
            # Return fallback output with low confidence
            return self._create_fallback_output(raw_output, str(e))
    
    def _calculate_confidence(self, planner_output: PlannerOutput) -> float:
        """
        Calculate confidence score based on plan completeness.
        
        Args:
            planner_output: Parsed planner output
            
        Returns:
            Confidence score (0.0-1.0)
        """
        confidence = 0.0
        
        # Base score for having jobs
        if planner_output.jobs:
            confidence += 0.3
        
        # Score for having entities
        if planner_output.entities:
            confidence += 0.2
        
        # Score for vertical recommendations
        if planner_output.recommended_verticals:
            confidence += 0.2
        
        # Score for success metrics
        if planner_output.success_metrics:
            confidence += 0.15
        
        # Score for reasoning quality
        if planner_output.reasoning and len(planner_output.reasoning) > 50:
            confidence += 0.15
        
        return min(1.0, confidence)
    
    def _create_fallback_output(self, raw_output: Any, error_message: str) -> AgentOutput:
        """
        Create fallback output when parsing fails.
        
        Args:
            raw_output: Original LLM output
            error_message: Error description
            
        Returns:
            AgentOutput with low confidence
        """
        logger.warning(f"Creating fallback planner output due to: {error_message}")
        
        return AgentOutput(
            decision={
                "jobs": [],
                "entities": [],
                "recommended_verticals": [],
                "success_metrics": [],
                "reasoning": f"Failed to parse plan: {error_message}",
                "fallback": True
            },
            reasoning=f"Planning failed: {error_message}. Raw output: {str(raw_output)[:200]}",
            confidence_score=0.1,
            metadata={
                "error": error_message,
                "raw_output": str(raw_output)[:500],
                "fallback": True,
            }
        )


# Convenience function for invoking planner agent
async def plan_execution(user_goal: str, job_id: str, context: Optional[str] = None, 
                        constraints: Optional[Dict[str, Any]] = None) -> AgentOutput:
    """
    Convenience function to invoke the planner agent.
    
    Args:
        user_goal: User's research goal
        job_id: Job identifier for tracking
        context: Optional additional context
        constraints: Optional constraints
        
    Returns:
        AgentOutput with execution plan
    """
    planner = PlannerAgent()
    
    agent_input = AgentInput(
        context={
            "user_goal": user_goal,
            "context": context,
            "constraints": constraints or {}
        },
        job_id=job_id,
        user_request=user_goal
    )
    
    decision = await planner.execute(agent_input)
    
    if not decision.success:
        raise Exception(f"Planner agent failed: {decision.error_message}")
    
    return AgentOutput(**decision.output_data)
