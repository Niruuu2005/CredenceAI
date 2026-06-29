"""
Agent Budget Controller for CredenceAI Iteration 0.4

This module manages budget constraints for AI agent operations to control costs
and prevent excessive LLM API usage. Budgets are tracked per job and per agent type.

Budget Limits:
- Tokens per job (default: 10,000 tokens)
- API calls per job (default: 20 calls)
- Tokens per agent type (can be configured)
- Daily/monthly budget caps (optional)

Budget state is persisted in database for tracking across service restarts.
"""

from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime, timezone
import logging

from app.models import Base

logger = logging.getLogger(__name__)


class AgentBudgetRecord(Base):
    """
    Database model for tracking agent budget usage per job.
    
    Attributes:
        id: Primary key
        job_id: Job identifier
        agent_name: Name of the agent
        tokens_used: Total tokens consumed
        api_calls_made: Total API calls made
        tokens_limit: Maximum tokens allowed
        api_calls_limit: Maximum API calls allowed
        created_at: When budget tracking started
        updated_at: Last update timestamp
    """
    __tablename__ = "agent_budget_records"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, index=True, nullable=False)
    agent_name = Column(String, index=True, nullable=False)
    tokens_used = Column(Integer, default=0)
    api_calls_made = Column(Integer, default=0)
    tokens_limit = Column(Integer, default=10000)
    api_calls_limit = Column(Integer, default=20)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class BudgetExceededError(Exception):
    """Raised when an agent operation would exceed budget limits."""
    pass


class AgentBudgetController:
    """
    Controls and tracks budget for AI agent operations.
    
    This controller:
    - Checks if budget is available before agent execution
    - Updates budget usage after agent execution
    - Enforces per-job and per-agent budget limits
    - Persists budget state to database
    """
    
    # Default budget limits (can be overridden via config)
    DEFAULT_TOKENS_PER_JOB = 10000
    DEFAULT_API_CALLS_PER_JOB = 20
    
    # Per-agent type limits (can be configured)
    AGENT_TOKEN_LIMITS = {
        "PlannerAgent": 2000,
        "SourceSelectionAgent": 1000,
        "QualityCriticAgent": 1500,
        "EntityResolutionAgent": 1500,
        "ExtractionValidationAgent": 1000,
    }
    
    def __init__(self, db_session: Session, config: Optional[Dict] = None):
        """
        Initialize budget controller.
        
        Args:
            db_session: Database session for persistence
            config: Optional configuration overrides
        """
        self.db = db_session
        self.config = config or {}
        self.tokens_per_job = self.config.get("tokens_per_job", self.DEFAULT_TOKENS_PER_JOB)
        self.api_calls_per_job = self.config.get("api_calls_per_job", self.DEFAULT_API_CALLS_PER_JOB)
    
    def check_budget(self, job_id: str, agent_name: str, estimated_tokens: int = 0) -> bool:
        """
        Check if budget is available for an agent operation.
        
        Args:
            job_id: Job identifier
            agent_name: Name of the agent requesting budget
            estimated_tokens: Estimated tokens this operation will consume
            
        Returns:
            True if budget is available, False otherwise
            
        Raises:
            BudgetExceededError: If budget would be exceeded
        """
        # Get or create budget record
        record = self._get_or_create_record(job_id, agent_name)
        
        # Check job-level token budget
        total_tokens_used = self._get_job_total_tokens(job_id)
        if total_tokens_used + estimated_tokens > self.tokens_per_job:
            raise BudgetExceededError(
                f"Job {job_id} would exceed token budget: "
                f"{total_tokens_used + estimated_tokens} > {self.tokens_per_job}"
            )
        
        # Check job-level API call budget
        total_api_calls = self._get_job_total_api_calls(job_id)
        if total_api_calls + 1 > self.api_calls_per_job:
            raise BudgetExceededError(
                f"Job {job_id} would exceed API call budget: "
                f"{total_api_calls + 1} > {self.api_calls_per_job}"
            )
        
        # Check agent-specific token budget
        agent_token_limit = self.AGENT_TOKEN_LIMITS.get(agent_name, 2000)
        if record.tokens_used + estimated_tokens > agent_token_limit:
            raise BudgetExceededError(
                f"Agent {agent_name} in job {job_id} would exceed token budget: "
                f"{record.tokens_used + estimated_tokens} > {agent_token_limit}"
            )
        
        logger.info(
            f"Budget check passed for {agent_name} in job {job_id}: "
            f"tokens={total_tokens_used}/{self.tokens_per_job}, "
            f"calls={total_api_calls}/{self.api_calls_per_job}"
        )
        
        return True
    
    def update_usage(
        self,
        job_id: str,
        agent_name: str,
        tokens_used: int,
        api_calls: int = 1
    ) -> None:
        """
        Update budget usage after an agent operation.
        
        Args:
            job_id: Job identifier
            agent_name: Name of the agent
            tokens_used: Number of tokens consumed
            api_calls: Number of API calls made (default: 1)
        """
        record = self._get_or_create_record(job_id, agent_name)
        
        # Update usage
        record.tokens_used += tokens_used
        record.api_calls_made += api_calls
        record.updated_at = datetime.now(timezone.utc)
        
        self.db.commit()
        
        logger.info(
            f"Updated budget for {agent_name} in job {job_id}: "
            f"+{tokens_used} tokens, +{api_calls} calls "
            f"(total: {record.tokens_used} tokens, {record.api_calls_made} calls)"
        )
    
    def get_remaining_budget(self, job_id: str) -> Dict[str, int]:
        """
        Get remaining budget for a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Dictionary with remaining tokens and API calls
        """
        total_tokens = self._get_job_total_tokens(job_id)
        total_api_calls = self._get_job_total_api_calls(job_id)
        
        return {
            "remaining_tokens": max(0, self.tokens_per_job - total_tokens),
            "remaining_api_calls": max(0, self.api_calls_per_job - total_api_calls),
            "tokens_used": total_tokens,
            "api_calls_used": total_api_calls,
            "tokens_limit": self.tokens_per_job,
            "api_calls_limit": self.api_calls_per_job,
        }
    
    def get_agent_usage(self, job_id: str, agent_name: str) -> Dict[str, int]:
        """
        Get budget usage for a specific agent in a job.
        
        Args:
            job_id: Job identifier
            agent_name: Name of the agent
            
        Returns:
            Dictionary with tokens and API calls used by this agent
        """
        record = self._get_or_create_record(job_id, agent_name)
        
        return {
            "agent_name": agent_name,
            "tokens_used": record.tokens_used,
            "api_calls_made": record.api_calls_made,
            "tokens_limit": self.AGENT_TOKEN_LIMITS.get(agent_name, 2000),
        }
    
    def reset_job_budget(self, job_id: str) -> None:
        """
        Reset budget for a job (useful for retries or testing).
        
        Args:
            job_id: Job identifier
        """
        records = self.db.query(AgentBudgetRecord).filter(
            AgentBudgetRecord.job_id == job_id
        ).all()
        
        for record in records:
            self.db.delete(record)
        
        self.db.commit()
        logger.info(f"Reset budget for job {job_id}")
    
    def _get_or_create_record(self, job_id: str, agent_name: str) -> AgentBudgetRecord:
        """Get existing budget record or create a new one."""
        record = self.db.query(AgentBudgetRecord).filter(
            AgentBudgetRecord.job_id == job_id,
            AgentBudgetRecord.agent_name == agent_name
        ).first()
        
        if not record:
            record = AgentBudgetRecord(
                job_id=job_id,
                agent_name=agent_name,
                tokens_limit=self.AGENT_TOKEN_LIMITS.get(agent_name, 2000)
            )
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
        
        return record
    
    def _get_job_total_tokens(self, job_id: str) -> int:
        """Get total tokens used across all agents for a job."""
        result = self.db.query(AgentBudgetRecord).filter(
            AgentBudgetRecord.job_id == job_id
        ).all()
        
        return sum(record.tokens_used for record in result)
    
    def _get_job_total_api_calls(self, job_id: str) -> int:
        """Get total API calls made across all agents for a job."""
        result = self.db.query(AgentBudgetRecord).filter(
            AgentBudgetRecord.job_id == job_id
        ).all()
        
        return sum(record.api_calls_made for record in result)
