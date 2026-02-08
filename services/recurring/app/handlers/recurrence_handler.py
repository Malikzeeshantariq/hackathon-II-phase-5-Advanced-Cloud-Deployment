"""
[Task]: T019, T020
[From]: specs/002-advanced-features-dapr/tasks.md §Phase 6 (US4)
[Description]: Recurring Task Service event handler

Processes TaskEvents from 'task-events' topic.
Filters for event_type=="completed" AND task_data.is_recurring==true.
Computes next due date using dateutil.relativedelta.
Creates new task via Dapr Service Invocation to todo-backend.
"""

import logging
from datetime import datetime, timezone
from uuid import UUID

import httpx
from dateutil.relativedelta import relativedelta
from sqlmodel import Session

from app.config import get_settings
from app.models.processed_event import ProcessedEvent

logger = logging.getLogger(__name__)

SERVICE_NAME = "recurring-service"


def compute_next_due_date(current_due_at: str | None, recurrence_rule: str) -> str:
    """T020: Compute next due date based on recurrence rule.

    Handles:
    - daily: +1 day
    - weekly: +7 days
    - monthly: +1 month (with month-end clamping: Jan 31 -> Feb 28/29)
    - Missing due_at: use current date as base

    Args:
        current_due_at: ISO8601 datetime string or None
        recurrence_rule: daily, weekly, or monthly

    Returns:
        ISO8601 datetime string for next due date
    """
    if current_due_at:
        try:
            base = datetime.fromisoformat(current_due_at.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            base = datetime.now(timezone.utc)
    else:
        base = datetime.now(timezone.utc)

    if recurrence_rule == "daily":
        next_date = base + relativedelta(days=1)
    elif recurrence_rule == "weekly":
        next_date = base + relativedelta(weeks=1)
    elif recurrence_rule == "monthly":
        # relativedelta handles month-end clamping (Jan 31 -> Feb 28/29)
        next_date = base + relativedelta(months=1)
    else:
        logger.warning(f"Unknown recurrence_rule '{recurrence_rule}', defaulting to daily")
        next_date = base + relativedelta(days=1)

    return next_date.isoformat()


async def handle_task_event(event_data: dict, session: Session) -> dict:
    """Process a task event from Dapr Pub/Sub.

    Filters for completed recurring tasks, creates next occurrence
    via Dapr Service Invocation to todo-backend.

    Args:
        event_data: CloudEvents envelope with task data
        session: Database session

    Returns:
        dict with status for Dapr acknowledgment
    """
    settings = get_settings()

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
    task_data = data.get("task_data", {})
    task_id = data.get("task_id")
    user_id = data.get("user_id")

    # Filter: only process completed recurring tasks
    is_recurring = task_data.get("is_recurring", False)
    if event_type != "completed" or not is_recurring:
        # Record as processed to avoid re-processing
        processed = ProcessedEvent(event_id=UUID(event_id), service_name=SERVICE_NAME)
        session.add(processed)
        session.commit()
        return {"status": "SUCCESS"}

    recurrence_rule = task_data.get("recurrence_rule")
    if not recurrence_rule:
        logger.warning(f"Recurring task {task_id} has no recurrence_rule, skipping")
        processed = ProcessedEvent(event_id=UUID(event_id), service_name=SERVICE_NAME)
        session.add(processed)
        session.commit()
        return {"status": "SUCCESS"}

    # T020: Compute next due date
    current_due_at = task_data.get("due_at")
    next_due_at = compute_next_due_date(current_due_at, recurrence_rule)

    # Create new task via Dapr Service Invocation
    new_task_payload = {
        "title": task_data.get("title", ""),
        "description": task_data.get("description"),
        "priority": task_data.get("priority"),
        "tags": task_data.get("tags", []),
        "due_at": next_due_at,
        "is_recurring": True,
        "recurrence_rule": recurrence_rule,
    }

    # Dapr Service Invocation to todo-backend
    dapr_url = f"http://localhost:{settings.DAPR_HTTP_PORT}/v1.0/invoke/{settings.BACKEND_APP_ID}/method/api/{user_id}/tasks"

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                dapr_url,
                json=new_task_payload,
                headers={"Content-Type": "application/json"},
            )

        if response.status_code in [200, 201]:
            logger.info(
                f"Created next recurring task for user={user_id}, "
                f"original_task={task_id}, next_due_at={next_due_at}"
            )
        else:
            logger.error(
                f"Failed to create recurring task: {response.status_code} - {response.text}"
            )
            # Return RETRY so Dapr will redeliver
            return {"status": "RETRY"}

    except Exception as e:
        logger.error(f"Error creating recurring task: {str(e)}")
        return {"status": "RETRY"}

    # Record as processed
    processed = ProcessedEvent(event_id=UUID(event_id), service_name=SERVICE_NAME)
    session.add(processed)
    session.commit()

    return {"status": "SUCCESS"}
