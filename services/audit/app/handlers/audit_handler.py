"""
[Task]: T021
[From]: specs/002-advanced-features-dapr/tasks.md §Phase 7 (US5)
[Description]: Audit Service event handler

Processes ALL task lifecycle events from 'task-events' topic.
Creates immutable AuditEntry records with full event_data snapshot.
Includes idempotency check via ProcessedEvent table.
Append-only: no UPDATE or DELETE on audit_entry table.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID, uuid4

from sqlmodel import Session

from app.models.audit_entry import AuditEntry
from app.models.processed_event import ProcessedEvent

logger = logging.getLogger(__name__)

SERVICE_NAME = "audit-service"

VALID_EVENT_TYPES = {"created", "updated", "completed", "deleted"}


async def handle_task_event(event_data: dict, session: Session) -> dict:
    """Process a task event and create an audit entry.

    Args:
        event_data: CloudEvents envelope with task data
        session: Database session

    Returns:
        dict with status for Dapr acknowledgment
    """
    # Extract event ID for idempotency
    event_id = event_data.get("id")
    if not event_id:
        logger.warning("Received event without id, skipping")
        return {"status": "DROP"}

    # Idempotency check
    existing = session.get(ProcessedEvent, UUID(event_id))
    if existing:
        logger.info(f"Event {event_id} already processed, skipping")
        return {"status": "SUCCESS"}

    # Extract data from CloudEvents envelope
    data = event_data.get("data", {})
    event_type = data.get("event_type")
    task_id = data.get("task_id")
    user_id = data.get("user_id")
    timestamp_str = data.get("timestamp")

    if not event_type or not task_id or not user_id:
        logger.warning(f"Event {event_id} missing required fields, dropping")
        return {"status": "DROP"}

    if event_type not in VALID_EVENT_TYPES:
        logger.warning(f"Unknown event_type '{event_type}', dropping")
        return {"status": "DROP"}

    # Parse timestamp
    try:
        if timestamp_str:
            timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
        else:
            timestamp = datetime.now(timezone.utc)
    except (ValueError, AttributeError):
        timestamp = datetime.now(timezone.utc)

    # Create audit entry (append-only)
    audit_entry = AuditEntry(
        id=uuid4(),
        event_type=event_type,
        task_id=UUID(task_id) if isinstance(task_id, str) else task_id,
        user_id=user_id,
        event_data=data,  # Full event payload snapshot
        timestamp=timestamp,
    )

    # Record as processed
    processed = ProcessedEvent(event_id=UUID(event_id), service_name=SERVICE_NAME)

    session.add(audit_entry)
    session.add(processed)
    session.commit()

    logger.info(
        f"Audit entry created: event_type={event_type}, task_id={task_id}, user_id={user_id}"
    )

    return {"status": "SUCCESS"}
