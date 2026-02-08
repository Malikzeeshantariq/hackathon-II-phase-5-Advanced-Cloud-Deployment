"""
[Task]: T017
[From]: specs/002-advanced-features-dapr/tasks.md §Phase 5 (US3)
[Description]: Dapr Job callback endpoint for reminder triggers

POST /internal/jobs/reminder-trigger — called by Dapr when a scheduled job fires.
No JWT auth required (internal Dapr callback).
"""

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select

from app.database import get_session
from app.models.task import Task
from app.models.reminder import Reminder
from app.services.event_publisher import get_event_publisher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal", tags=["Internal"])


class ReminderTriggerRequest(BaseModel):
    """Request body from Dapr Jobs API when a reminder fires."""

    reminder_id: UUID
    task_id: UUID
    user_id: str


@router.post(
    "/jobs/reminder-trigger",
    summary="Reminder trigger callback (Dapr Jobs)",
)
async def trigger_reminder(
    request: ReminderTriggerRequest,
    session: Session = Depends(get_session),
) -> dict:
    """T017: Handle Dapr Job callback when a reminder fires.

    Looks up reminder + task, publishes ReminderEvent to 'reminders' topic.
    """
    logger.info(f"Reminder trigger: reminder_id={request.reminder_id}, task_id={request.task_id}")

    # Look up reminder
    reminder = session.get(Reminder, request.reminder_id)
    if not reminder:
        logger.warning(f"Reminder not found: {request.reminder_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Reminder {request.reminder_id} not found",
        )

    # Look up task (with user isolation)
    stmt = select(Task).where(Task.id == request.task_id, Task.user_id == request.user_id)
    task = session.exec(stmt).first()
    if not task:
        logger.warning(f"Task not found: task_id={request.task_id}, user_id={request.user_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {request.task_id} not found",
        )

    # Publish ReminderEvent
    event_publisher = await get_event_publisher()
    success = await event_publisher.publish_reminder_event(
        reminder_id=request.reminder_id,
        task=task,
        user_id=request.user_id,
        remind_at=reminder.remind_at,
    )

    if not success:
        logger.error(f"Failed to publish ReminderEvent for reminder {request.reminder_id}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to publish reminder event",
        )

    return {"status": "ok"}
