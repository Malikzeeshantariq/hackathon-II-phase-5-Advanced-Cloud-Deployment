"""Event payload schemas for Dapr Pub/Sub (CloudEvents 1.0).

Spec Reference: event-contracts.md Sections 1-3
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel


class TaskData(BaseModel):
    """Snapshot of task data in event payload."""
    title: str
    description: Optional[str] = None
    completed: bool
    priority: Optional[str] = None
    tags: List[str] = []
    due_at: Optional[datetime] = None
    is_recurring: bool = False
    recurrence_rule: Optional[str] = None


class TaskEventPayload(BaseModel):
    """Data field of a TaskEvent (topic: task-events)."""
    event_type: str  # created | updated | completed | deleted
    task_id: UUID
    user_id: str
    task_data: TaskData
    timestamp: datetime


class ReminderEventPayload(BaseModel):
    """Data field of a ReminderEvent (topic: reminders)."""
    reminder_id: UUID
    task_id: UUID
    title: str
    user_id: str
    due_at: Optional[datetime] = None
    remind_at: datetime
    timestamp: datetime


class TaskUpdateEventPayload(BaseModel):
    """Data field of a TaskUpdateEvent (topic: task-updates)."""
    task_id: UUID
    user_id: str
    change_type: str  # created | updated | completed | deleted
    timestamp: datetime
