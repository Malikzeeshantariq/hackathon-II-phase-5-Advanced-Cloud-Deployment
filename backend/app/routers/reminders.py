"""
[Task]: T015, T016
[From]: specs/002-advanced-features-dapr/tasks.md §Phase 5 (US3)
[Description]: Reminder CRUD routes with Dapr Job scheduling

T015: Create reminder CRUD routes
T016: Implement Dapr Jobs scheduling for reminders
"""

import logging
from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.database import get_session
from app.middleware.auth import TokenPayload, get_current_user, verify_user_access
from app.models.task import Task
from app.models.reminder import Reminder
from app.schemas.reminder import ReminderCreate, ReminderResponse
from app.services.event_publisher import get_event_publisher

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/{user_id}/tasks/{task_id}/reminders",
    tags=["Reminders"],
)


@router.post(
    "",
    response_model=ReminderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a reminder for a task",
)
async def create_reminder(
    user_id: str,
    task_id: UUID,
    reminder_data: ReminderCreate,
    session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> Reminder:
    """T015, T016: Create a reminder and schedule a Dapr Job.

    Validates remind_at is in the future, task exists and is owned by user.
    Schedules a Dapr Job at remind_at time.
    """
    verify_user_access(current_user.user_id, user_id)

    # Validate remind_at is in the future
    now = datetime.now(timezone.utc)
    remind_at = reminder_data.remind_at
    if remind_at.tzinfo is None:
        remind_at = remind_at.replace(tzinfo=timezone.utc)
    if remind_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="remind_at must be in the future",
        )

    # Validate task exists and is owned by user
    task_stmt = select(Task).where(Task.id == task_id, Task.user_id == current_user.user_id)
    task = session.exec(task_stmt).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    # Create reminder
    reminder = Reminder(
        task_id=task_id,
        user_id=current_user.user_id,
        remind_at=reminder_data.remind_at,
    )
    session.add(reminder)
    session.commit()
    session.refresh(reminder)

    # T016: Schedule Dapr Job
    event_publisher = await get_event_publisher()
    job_name = f"reminder-{reminder.id}"
    job_data = {
        "reminder_id": str(reminder.id),
        "task_id": str(task_id),
        "user_id": current_user.user_id,
    }
    success = await event_publisher.schedule_reminder_job(job_name, reminder_data.remind_at, job_data)
    if not success:
        logger.warning(f"Failed to schedule Dapr job for reminder {reminder.id}")

    return reminder


@router.get(
    "",
    response_model=List[ReminderResponse],
    summary="List reminders for a task",
)
async def list_reminders(
    user_id: str,
    task_id: UUID,
    session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> List[Reminder]:
    """T015: List all reminders for a task owned by user."""
    verify_user_access(current_user.user_id, user_id)

    # Validate task exists and is owned by user
    task_stmt = select(Task).where(Task.id == task_id, Task.user_id == current_user.user_id)
    task = session.exec(task_stmt).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )

    stmt = select(Reminder).where(
        Reminder.task_id == task_id,
        Reminder.user_id == current_user.user_id,
    ).order_by(Reminder.remind_at)
    reminders = session.exec(stmt).all()
    return list(reminders)


@router.delete(
    "/{reminder_id}",
    summary="Delete a reminder",
)
async def delete_reminder(
    user_id: str,
    task_id: UUID,
    reminder_id: UUID,
    session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> dict:
    """T015, T016: Delete a reminder and cancel its Dapr Job."""
    verify_user_access(current_user.user_id, user_id)

    stmt = select(Reminder).where(
        Reminder.id == reminder_id,
        Reminder.task_id == task_id,
        Reminder.user_id == current_user.user_id,
    )
    reminder = session.exec(stmt).first()
    if not reminder:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reminder not found",
        )

    # T016: Cancel Dapr Job
    event_publisher = await get_event_publisher()
    job_name = f"reminder-{reminder.id}"
    await event_publisher.cancel_reminder_job(job_name)

    session.delete(reminder)
    session.commit()

    return {"message": "Reminder deleted successfully"}
