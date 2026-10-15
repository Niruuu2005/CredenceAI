"""
Transactional Outbox Dispatcher.
Implements NFR-001, RUN-02, RUN-03, Gate G4.
Reads committed events from PostgreSQL and publishes them to workers/handlers safely.
"""

import json
import logging
from typing import Optional, Callable
from sqlalchemy.orm import Session
from app.models import OutboxEvent, utc_now

logger = logging.getLogger(__name__)


class OutboxDispatcher:
    def __init__(self, handler: Optional[Callable[[OutboxEvent, Session], None]] = None):
        self.handler = handler

    def process_pending_events(self, db: Session, batch_size: int = 50) -> int:
        """
        Poll and process pending outbox events.
        Ensures at-least-once delivery semantics (NFR-002).
        """
        events = (
            db.query(OutboxEvent)
            .filter(OutboxEvent.status == "pending")
            .order_by(OutboxEvent.created_at.asc())
            .limit(batch_size)
            .all()
        )

        processed_count = 0
        for event in events:
            try:
                if self.handler:
                    self.handler(event, db)

                event.status = "dispatched"
                event.processed_at = utc_now()
                processed_count += 1
                logger.info(
                    f"OUTBOX_DISPATCHER  event_id={event.id}  "
                    f"type={event.event_type}  aggregate_id={event.aggregate_id}"
                )
            except Exception as exc:
                event.retry_count += 1
                if event.retry_count >= 5:
                    event.status = "failed"
                logger.error(
                    f"OUTBOX_DISPATCHER_ERROR  event_id={event.id}  "
                    f"retries={event.retry_count}  error={exc}"
                )

        if events:
            db.commit()

        return processed_count
