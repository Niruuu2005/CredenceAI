"""
Research orchestration module for CredenceAI 2.0.
Provides research run lifecycle management, transactional outbox dispatch, and durable execution pipeline.
"""

from app.research.service import (
    create_research_run,
    get_research_run,
    cancel_research_run,
    list_workspace_runs,
)
from app.research.outbox_dispatcher import OutboxDispatcher
from app.research.pipeline import execute_research_run

__all__ = [
    "create_research_run",
    "get_research_run",
    "cancel_research_run",
    "list_workspace_runs",
    "OutboxDispatcher",
    "execute_research_run",
]
