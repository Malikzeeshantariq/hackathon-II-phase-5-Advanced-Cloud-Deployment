"""
[Task]: T018
[From]: specs/002-advanced-features-dapr/tasks.md §Phase 5 (US3)
[Description]: Notification Service reminder event handler

Processes ReminderEvents from the 'reminders' topic.
Checks idempotency via ProcessedEvent table.
Logs notification details (delivery channel integration deferred per Assumption 1).
"""

import logging
from uuid import UUID

from sqlmodel import Session

from app.models.processed_event import ProcessedEvent

logger = logging.getLogger(__name__)

SERVICE_NAME = "notification-service"


async def handle_reminder_event(event_data: dict, session: Session) -> dict:
    """Process a reminder event from Dapr Pub/Sub.

    Args:
        event_data: CloudEvents envelope with reminder data
        session: Database session

    Returns:
        dict with status for Dapr acknowledgment
    """
    # Extract the event ID from CloudEvents envelope
    event_id = event_data.get("id")
    if not event_id:
        logger.warning("Received event without id, skipping")
        return {"status": "DROP"}

    # Idempotency check
    existing = session.get(ProcessedEvent, UUID(event_id))
    if existing:
        logger.info(f"Event {event_id} already processed, skipping")
        return {"status": "SUCCESS"}

    # Extract reminder data from CloudEvents data field
    data = event_data.get("data", {})
    reminder_id = data.get("reminder_id")
    task_id = data.get("task_id")
    title = data.get("title")
    user_id = data.get("user_id")
    due_at = data.get("due_at")
    remind_at = data.get("remind_at")

    # Log the notification (delivery channel deferred per Assumption 1)
    logger.info(
        f"NOTIFICATION: Reminder triggered for user={user_id}, "
        f"task={task_id}, title='{title}', due_at={due_at}, "
        f"remind_at={remind_at}, reminder_id={reminder_id}"
    )

    # Record as processed for idempotency
    processed = ProcessedEvent(
        event_id=UUID(event_id),
        service_name=SERVICE_NAME,
    )
    session.add(processed)
    session.commit()

    return {"status": "SUCCESS"}
