"""
Agent Error Handler for CredenceAI Iteration 0.4

Provides centralized error handling and graceful degradation for agent operations.
Ensures agents fail safely without breaking the pipeline.
"""

import logging
from typing import Any, Dict, Optional, Callable
from functools import wraps
from datetime import datetime, timezone

from app.agents.base import AgentDecision, AgentOutput

logger = logging.getLogger(__name__)


class AgentErrorHandler:
    """
    Centralized error handling for agent operations.
    
    Features:
    - Graceful degradation when agents fail
    - Fallback to deterministic processing
    - Error logging and classification
    - Retry coordination
    """
    
    @staticmethod
    def handle_agent_failure(
        agent_name: str,
        job_id: str,
        error: Exception,
        fallback_decision: Optional[Any] = None
    ) -> AgentDecision:
        """
        Handle agent failure and provide fallback decision.
        
        Args:
            agent_name: Name of the failed agent
            job_id: Job identifier
            error: Exception that occurred
            fallback_decision: Optional fallback decision value
            
        Returns:
            AgentDecision marked as failed with error details
        """
        error_type = type(error).__name__
        error_message = str(error)
        
        logger.error(
            f"Agent {agent_name} failed for job {job_id}: "
            f"{error_type} - {error_message}"
        )
        
        # Create failure decision
        decision = AgentDecision(
            agent_name=agent_name,
            job_id=job_id,
            input_data={},
            output_data={"fallback_decision": fallback_decision} if fallback_decision else None,
            reasoning=f"Agent execution failed: {error_type} - {error_message}",
            confidence_score=0.0,
            timestamp=datetime.now(timezone.utc),
            success=False,
            error_message=error_message,
            execution_time_ms=0
        )
        
        return decision
    
    @staticmethod
    def get_fallback_decision(agent_name: str, context: Dict[str, Any]) -> Any:
        """
        Get deterministic fallback decision when agent fails.
        
        Args:
            agent_name: Name of the agent
            context: Context for fallback decision
            
        Returns:
            Fallback decision appropriate for the agent type
        """
        # Fallback strategies per agent type
        if agent_name == "PlannerAgent":
            return {
                "jobs": [{"job_type": "search_query", "input": context.get("query", "")}],
                "fallback": True
            }
        
        elif agent_name == "SourceSelectionAgent":
            return {
                "recommended_sources": [{"name": "SearXNG", "priority": 1, "confidence": 0.5}],
                "fallback": True
            }
        
        elif agent_name == "QualityCriticAgent":
            # Default to existing quality score
            return {
                "decision": "review",  # Conservative: send to manual review
                "reasoning": "Agent unavailable, defaulting to manual review",
                "confidence": 0.3,
                "fallback": True
            }
        
        elif agent_name == "EntityResolutionAgent":
            # Use best matching candidate from context
            candidates = context.get("candidates", [])
            if candidates:
                return {
                    "canonical_entity": candidates[0].get("name", "Unknown"),
                    "confidence": 0.4,
                    "fallback": True
                }
            return {
                "canonical_entity": context.get("mention", "Unknown"),
                "confidence": 0.3,
                "fallback": True
            }
        
        elif agent_name == "ExtractionValidationAgent":
            # Default to valid if agent unavailable
            return {
                "status": "VALID",
                "reasoning": "Agent unavailable, assuming valid extraction",
                "confidence": 0.3,
                "fallback": True
            }
        
        else:
            return {"fallback": True, "error": "Unknown agent type"}
    
    @staticmethod
    def should_retry(error: Exception, attempt: int, max_retries: int = 3) -> bool:
        """
        Determine if operation should be retried based on error type.
        
        Args:
            error: Exception that occurred
            attempt: Current attempt number
            max_retries: Maximum retry attempts
            
        Returns:
            True if should retry, False otherwise
        """
        if attempt >= max_retries:
            return False
        
        error_type = type(error).__name__
        
        # Retry on transient errors
        retriable_errors = [
            "LLMTimeoutError",
            "LLMRateLimitError",
            "TimeoutError",
            "ConnectionError",
            "HTTPError"
        ]
        
        return error_type in retriable_errors
    
    @staticmethod
    def classify_error(error: Exception) -> str:
        """
        Classify error type for logging and monitoring.
        
        Args:
            error: Exception that occurred
            
        Returns:
            Error classification string
        """
        error_type = type(error).__name__
        
        if "Timeout" in error_type:
            return "timeout"
        elif "RateLimit" in error_type:
            return "rate_limit"
        elif "Budget" in error_type:
            return "budget_exceeded"
        elif "Parsing" in error_type or "Validation" in error_type:
            return "parsing_error"
        elif "Connection" in error_type or "HTTP" in error_type:
            return "network_error"
        else:
            return "unknown_error"


def with_fallback(fallback_fn: Optional[Callable] = None):
    """
    Decorator to add graceful fallback to agent methods.
    
    Args:
        fallback_fn: Optional custom fallback function
        
    Returns:
        Decorated function with error handling
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            try:
                return await func(self, *args, **kwargs)
            except Exception as e:
                logger.warning(
                    f"Agent {self.agent_name} failed, using fallback: {e}"
                )
                
                if fallback_fn:
                    return fallback_fn(self, *args, **kwargs)
                
                # Default fallback: return low-confidence neutral decision
                return AgentOutput(
                    decision="review",
                    reasoning=f"Agent execution failed: {str(e)}. Using fallback.",
                    confidence_score=0.3,
                    metadata={"fallback": True, "error": str(e)}
                )
        
        return wrapper
    return decorator


def log_agent_error(
    agent_name: str,
    job_id: str,
    error: Exception,
    context: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log agent error with structured context.
    
    Args:
        agent_name: Name of the agent
        job_id: Job identifier
        error: Exception that occurred
        context: Optional additional context
    """
    error_class = AgentErrorHandler.classify_error(error)
    
    log_data = {
        "agent_name": agent_name,
        "job_id": job_id,
        "error_type": type(error).__name__,
        "error_class": error_class,
        "error_message": str(error),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    
    if context:
        log_data["context"] = context
    
    logger.error(f"Agent error: {log_data}")
