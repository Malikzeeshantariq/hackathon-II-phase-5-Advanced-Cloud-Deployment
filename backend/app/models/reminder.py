"""Reminder SQLModel definition.

Spec Reference: data-model.md Section 2 - Reminder Entity
Functional Requirements: FR-005, FR-012, FR-013
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID, uuid4

from sqlmodel import SQLModel, Field


class Reminder(SQLModel, table=True):
    """Reminder entity — a scheduled notification for a task.

    Attributes:
        id: Unique reminder identifier
        task_id: FK to task (CASCADE delete)
        user_id: Denormalized for user isolation queries
        remind_at: When the reminder should fire (must be future)
        created_at: Creation timestamp
    """

    __tablename__ = "reminders"

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique reminder identifier"
    )
    task_id: UUID = Field(
        foreign_key="tasks.id",
        index=True,
        nullable=False,
        description="Associated task ID (CASCADE delete)"
    )
    user_id: str = Field(
        index=True,
        nullable=False,
        description="Owner's user ID (denormalized for isolation)"
    )
    remind_at: datetime = Field(
        nullable=False,
        description="Scheduled reminder time (UTC, must be in future)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
