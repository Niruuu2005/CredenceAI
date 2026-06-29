"""
Agent Decision Logger for CredenceAI Iteration 0.4

This module provides logging and auditing for all AI agent decisions.
Every agent invocation must be logged with full context for:
- Transparency and explainability
- Debugging and troubleshooting
- Compliance and audit trails
- Performance analysis

All logged decisions are persisted to database and can be queried for analysis.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Boolean, JSON, desc
from datetime import datetime, timedelta, timezone
import logging

from app.models import Base
from app.agents.base import AgentDecision

logger = logging.getLogger(__name__)


class AgentDecisionRecord(Base):
    """
    Database model for agent decision audit log.
    
    Attributes:
        id: Primary key
        job_id: Job identifier
        agent_name: Name of the agent
        input_data: Input provided to agent (JSON)
        output_data: Output produced by agent (JSON)
        reasoning: Explanation of decision
        confidence_score: Confidence level (0.0-1.0)
        timestamp: When decision was made
        execution_time_ms: Time taken in milliseconds
        success: Whether execution succeeded
        error_message: Error details if failed
    """
    __tablename__ = "agent_decisions"
    
    id = Column(Integer, primary_key=True, index=True)
    job_id = Column(String, index=True, nullable=False)
    agent_name = Column(String, index=True, nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    reasoning = Column(Text, nullable=True)
    confidence_score = Column(Float, nullable=False)
    timestamp = Column(DateTime, index=True, nullable=False)
    execution_time_ms = Column(Integer, nullable=True)
    success = Column(Boolean, default=True)
    error_message = Column(Text, nullable=True)


class AgentDecisionLogger:
    """
    Service for logging and querying agent decisions.
    
    This logger:
    - Persists all agent decisions to database
    - Provides query methods for decision analysis
    - Supports filtering by job, agent, success status
    - Tracks decision trends and patterns
    """
    
    def __init__(self, db_session: Session):
        """
        Initialize decision logger.
        
        Args:
            db_session: Database session for persistence
        """
        self.db = db_session
    
    def log_decision(self, decision: AgentDecision) -> int:
        """
        Log an agent decision to the database.
        
        Args:
            decision: AgentDecision object to log
            
        Returns:
            ID of the created log record
        """
        record = AgentDecisionRecord(
            job_id=decision.job_id,
            agent_name=decision.agent_name,
            input_data=decision.input_data,
            output_data=decision.output_data,
            reasoning=decision.reasoning,
            confidence_score=decision.confidence_score,
            timestamp=decision.timestamp,
            execution_time_ms=decision.execution_time_ms,
            success=decision.success,
            error_message=decision.error_message,
        )
        
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        
        logger.info(
            f"Logged decision: agent={decision.agent_name}, "
            f"job={decision.job_id}, success={decision.success}, "
            f"confidence={decision.confidence_score:.2f}"
        )
        
        return record.id
    
    def get_decisions_by_job(
        self,
        job_id: str,
        limit: int = 100
    ) -> List[AgentDecisionRecord]:
        """
        Get all agent decisions for a specific job.
        
        Args:
            job_id: Job identifier
            limit: Maximum number of records to return
            
        Returns:
            List of decision records ordered by timestamp
        """
        records = self.db.query(AgentDecisionRecord).filter(
            AgentDecisionRecord.job_id == job_id
        ).order_by(desc(AgentDecisionRecord.timestamp)).limit(limit).all()
        
        logger.debug(f"Retrieved {len(records)} decisions for job {job_id}")
        return records
    
    def get_decisions_by_agent(
        self,
        agent_name: str,
        limit: int = 100,
        success_only: bool = False
    ) -> List[AgentDecisionRecord]:
        """
        Get all decisions made by a specific agent.
        
        Args:
            agent_name: Name of the agent
            limit: Maximum number of records to return
            success_only: If True, only return successful decisions
            
        Returns:
            List of decision records ordered by timestamp
        """
        query = self.db.query(AgentDecisionRecord).filter(
            AgentDecisionRecord.agent_name == agent_name
        )
        
        if success_only:
            query = query.filter(AgentDecisionRecord.success == True)
        
        records = query.order_by(desc(AgentDecisionRecord.timestamp)).limit(limit).all()
        
        logger.debug(
            f"Retrieved {len(records)} decisions for agent {agent_name} "
            f"(success_only={success_only})"
        )
        return records
    
    def get_recent_decisions(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[AgentDecisionRecord]:
        """
        Get recent agent decisions within a time window.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of records to return
            
        Returns:
            List of decision records ordered by timestamp
        """
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        records = self.db.query(AgentDecisionRecord).filter(
            AgentDecisionRecord.timestamp >= cutoff_time
        ).order_by(desc(AgentDecisionRecord.timestamp)).limit(limit).all()
        
        logger.debug(f"Retrieved {len(records)} decisions from last {hours} hours")
        return records
    
    def get_failed_decisions(
        self,
        agent_name: Optional[str] = None,
        limit: int = 100
    ) -> List[AgentDecisionRecord]:
        """
        Get failed agent decisions for debugging.
        
        Args:
            agent_name: Optional filter by agent name
            limit: Maximum number of records to return
            
        Returns:
            List of failed decision records
        """
        query = self.db.query(AgentDecisionRecord).filter(
            AgentDecisionRecord.success == False
        )
        
        if agent_name:
            query = query.filter(AgentDecisionRecord.agent_name == agent_name)
        
        records = query.order_by(desc(AgentDecisionRecord.timestamp)).limit(limit).all()
        
        logger.debug(
            f"Retrieved {len(records)} failed decisions" +
            (f" for agent {agent_name}" if agent_name else "")
        )
        return records
    
    def get_decision_stats(self, job_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get statistics about agent decisions.
        
        Args:
            job_id: Optional filter by job ID
            
        Returns:
            Dictionary with decision statistics
        """
        query = self.db.query(AgentDecisionRecord)
        
        if job_id:
            query = query.filter(AgentDecisionRecord.job_id == job_id)
        
        all_decisions = query.all()
        
        if not all_decisions:
            return {
                "total_decisions": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "avg_confidence": 0.0,
                "avg_execution_time_ms": 0.0,
                "agents_used": [],
            }
        
        successful = [d for d in all_decisions if d.success]
        failed = [d for d in all_decisions if not d.success]
        
        agents_used = list(set(d.agent_name for d in all_decisions))
        
        avg_confidence = sum(d.confidence_score for d in successful) / len(successful) if successful else 0.0
        
        execution_times = [d.execution_time_ms for d in all_decisions if d.execution_time_ms is not None]
        avg_execution_time = sum(execution_times) / len(execution_times) if execution_times else 0.0
        
        stats = {
            "total_decisions": len(all_decisions),
            "successful": len(successful),
            "failed": len(failed),
            "success_rate": len(successful) / len(all_decisions) if all_decisions else 0.0,
            "avg_confidence": avg_confidence,
            "avg_execution_time_ms": avg_execution_time,
            "agents_used": agents_used,
        }
        
        logger.info(
            f"Decision stats: {stats['total_decisions']} total, "
            f"{stats['success_rate']:.1%} success rate, "
            f"{stats['avg_confidence']:.2f} avg confidence"
        )
        
        return stats
    
    def delete_old_decisions(self, days: int = 90) -> int:
        """
        Delete old decision records (for database maintenance).
        
        Args:
            days: Delete records older than this many days
            
        Returns:
            Number of records deleted
        """
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        deleted_count = self.db.query(AgentDecisionRecord).filter(
            AgentDecisionRecord.timestamp < cutoff_date
        ).delete()
        
        self.db.commit()
        
        logger.info(f"Deleted {deleted_count} decision records older than {days} days")
        return deleted_count
