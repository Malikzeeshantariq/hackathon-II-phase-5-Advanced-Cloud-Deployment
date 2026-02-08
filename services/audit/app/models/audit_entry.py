"""AuditEntry SQLModel definition.

Spec Reference: data-model.md Section 3 - AuditEntry Entity
Functional Requirements: FR-022
"""

from datetime import datetime
from typing import Any, Dict
from uuid import UUID, uuid4

from sqlalchemy import Column, Index
from sqlalchemy.types import JSON
from sqlmodel import SQLModel, Field


class AuditEntry(SQLModel, table=True):
    """Immutable audit log entry for task lifecycle events.

    Append-only: no UPDATE or DELETE operations.
    task_id is NOT a foreign key (task may be deleted; audit persists).
    """

    __tablename__ = "audit_entry"

    __table_args__ = (
        Index("idx_audit_user_id", "user_id"),
        Index("idx_audit_task_id", "task_id"),
        Index("idx_audit_timestamp", "timestamp"),
    )

    id: UUID = Field(
        default_factory=uuid4,
        primary_key=True,
        description="Unique audit entry identifier"
    )
    event_type: str = Field(
        max_length=20,
        nullable=False,
        description="Event type: created, updated, completed, deleted"
    )
    task_id: UUID = Field(
        nullable=False,
        description="Referenced task ID (not FK)"
    )
    user_id: str = Field(
        nullable=False,
        description="User who performed the action"
    )
    event_data: Dict[str, Any] = Field(
        sa_column=Column(JSON, nullable=False),
        description="Full event payload snapshot"
    )
    timestamp: datetime = Field(
        nullable=False,
        description="Event timestamp"
    )
