"""Task SQLModel definition.

Spec Reference: data-model.md - Task Entity
Phase II fields (immutable) + Phase V Part A extensions.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID, uuid4

from sqlalchemy import Column, Index
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.types import String
from sqlmodel import SQLModel, Field


class Task(SQLModel, table=True):
    """Task entity for Todo CRUD API.

    Phase II fields (immutable):
        id, user_id, title, description, completed, created_at, updated_at

    Phase V Part A extensions:
        priority, tags, due_at, is_recurring, recurrence_rule
    """

    __tablename__ = "tasks"

    __table_args__ = (
        Index("idx_task_priority", "user_id", "priority"),
        Index("idx_task_due_at", "user_id", "due_at"),
    )

    # --- Phase II fields (immutable) ---
    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique task identifier"
    )
    user_id: str = Field(
        index=True,
        nullable=False,
        description="Owner's user ID from JWT"
    )
    title: str = Field(
        max_length=255,
        nullable=False,
        description="Task title"
    )
    description: Optional[str] = Field(
        default=None,
        description="Detailed task description"
    )
    completed: bool = Field(
        default=False,
        description="Completion status"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Last modification timestamp"
    )

    # --- Phase V Part A extensions ---
    priority: Optional[str] = Field(
        default=None,
        max_length=10,
        description="Task priority: low, medium, high, critical"
    )
    tags: List[str] = Field(
        default_factory=list,
        sa_column=Column(ARRAY(String), nullable=False, server_default="{}"),
        description="User-scoped tags"
    )
    due_at: Optional[datetime] = Field(
        default=None,
        description="Due date (UTC)"
    )
    is_recurring: bool = Field(
        default=False,
        description="Whether this task recurs"
    )
    recurrence_rule: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Recurrence rule: daily, weekly, monthly"
    )
