"""
Agent execution wrapper: budget checks, decision logging, working memory.
"""

import logging
from typing import Optional

from sqlalchemy.orm import Session

from app.agents.base import BaseAgent, AgentInput, AgentDecision
from app.services.agent_budget_controller import AgentBudgetController, BudgetExceededError
from app.services.agent_decision_logger import AgentDecisionLogger
from app.services.agent_working_memory import AgentWorkingMemory

logger = logging.getLogger(__name__)

# Map agent_name to budget controller keys
_BUDGET_NAME_MAP = {
    "planner_agent": "PlannerAgent",
    "source_selection_agent": "SourceSelectionAgent",
    "quality_critic_agent": "QualityCriticAgent",
    "entity_resolution_agent": "EntityResolutionAgent",
    "extraction_validation_agent": "ExtractionValidationAgent",
    "crawl_strategy_agent": "CrawlStrategyAgent",
    "experiment_agent": "ExperimentAgent",
    "ops_recovery_agent": "OpsRecoveryAgent",
}


async def run_agent(
    db: Session,
    agent: BaseAgent,
    agent_input: AgentInput,
    estimated_tokens: int = 500,
    tokens_used: int = 0,
) -> AgentDecision:
    """Execute an agent with budget enforcement, logging, and memory."""
    budget_name = _BUDGET_NAME_MAP.get(agent.agent_name, agent.agent_name)
    budget = AgentBudgetController(db)

    try:
        budget.check_budget(agent_input.job_id, budget_name, estimated_tokens)
    except BudgetExceededError as exc:
        logger.warning("Agent budget exceeded: %s", exc)
        return AgentDecision(
            agent_name=agent.agent_name,
            job_id=agent_input.job_id,
            input_data=agent_input.model_dump(),
            reasoning=str(exc),
            confidence_score=0.0,
            success=False,
            error_message=str(exc),
        )

    decision = await agent.execute(agent_input)

    if decision.success:
        budget.update_usage(
            agent_input.job_id,
            budget_name,
            tokens_used or estimated_tokens,
            api_calls=1,
        )
        AgentDecisionLogger(db).log_decision(decision)
        memory = AgentWorkingMemory(db)
        memory.record_step(
            job_id=agent_input.job_id,
            agent_name=agent.agent_name,
            decision=decision.output_data,
            reasoning=decision.reasoning,
        )

    return decision
