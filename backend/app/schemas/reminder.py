"""Pydantic schemas for Reminder request/response validation.

Spec Reference: api-contracts.md Section 2
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ReminderCreate(BaseModel):
    """Request body for creating a reminder."""
    remind_at: datetime = Field(description="Reminder time (must be in the future)")


class ReminderResponse(BaseModel):
    """Response body for reminder operations."""
    id: UUID
    task_id: UUID
    user_id: str
    remind_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True
