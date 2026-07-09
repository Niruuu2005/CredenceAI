"""
Per-job working memory for multi-step agent orchestration.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.models import AgentMemoryRecord

logger = logging.getLogger(__name__)


class AgentWorkingMemory:
    """Persist and retrieve per-job agent context across iterations."""

    def __init__(self, db: Session):
        self.db = db

    def record_step(
        self,
        job_id: str,
        agent_name: str,
        decision: Optional[Dict[str, Any]],
        reasoning: str = "",
    ) -> None:
        step_index = self._next_step_index(job_id)
        record = AgentMemoryRecord(
            job_id=job_id,
            agent_name=agent_name,
            step_index=step_index,
            decision_json=json.dumps(decision) if decision else None,
            reasoning=reasoning,
        )
        self.db.add(record)
        self.db.commit()

    def get_context(self, job_id: str) -> Dict[str, Any]:
        records = (
            self.db.query(AgentMemoryRecord)
            .filter(AgentMemoryRecord.job_id == job_id)
            .order_by(AgentMemoryRecord.step_index)
            .all()
        )
        steps: List[Dict[str, Any]] = []
        for rec in records:
            step: Dict[str, Any] = {
                "agent": rec.agent_name,
                "step": rec.step_index,
                "reasoning": rec.reasoning,
            }
            if rec.decision_json:
                try:
                    step["decision"] = json.loads(rec.decision_json)
                except json.JSONDecodeError:
                    step["decision"] = rec.decision_json
            steps.append(step)
        return {"job_id": job_id, "steps": steps, "iteration_count": len(steps)}

    def clear(self, job_id: str) -> None:
        self.db.query(AgentMemoryRecord).filter(
            AgentMemoryRecord.job_id == job_id
        ).delete()
        self.db.commit()

    def _next_step_index(self, job_id: str) -> int:
        last = (
            self.db.query(AgentMemoryRecord)
            .filter(AgentMemoryRecord.job_id == job_id)
            .order_by(AgentMemoryRecord.step_index.desc())
            .first()
        )
        return (last.step_index + 1) if last else 0
