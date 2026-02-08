"""Pydantic schemas for Task request/response validation.

Spec Reference: api-contracts.md Sections 1.1-1.5
Phase II schemas (immutable) + Phase V Part A extensions.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator


VALID_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_RECURRENCE_RULES = {"daily", "weekly", "monthly"}
VALID_SORT_FIELDS = {"created_at", "due_at", "priority", "title"}
VALID_SORT_ORDERS = {"asc", "desc"}


class TaskCreate(BaseModel):
    """Request body for creating a task."""
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    priority: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    due_at: Optional[datetime] = Field(default=None)
    is_recurring: bool = Field(default=False)
    recurrence_rule: Optional[str] = Field(default=None)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(VALID_PRIORITIES)}")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        if v is not None:
            # Remove empty strings and duplicates
            return list(dict.fromkeys(tag for tag in v if tag.strip()))
        return v

    @field_validator("recurrence_rule")
    @classmethod
    def validate_recurrence_rule(cls, v):
        if v is not None and v not in VALID_RECURRENCE_RULES:
            raise ValueError(f"recurrence_rule must be one of: {', '.join(VALID_RECURRENCE_RULES)}")
        return v

    @model_validator(mode="after")
    def validate_recurring_consistency(self):
        if self.is_recurring and self.recurrence_rule is None:
            raise ValueError("recurrence_rule is required when is_recurring is true")
        if not self.is_recurring and self.recurrence_rule is not None:
            raise ValueError("recurrence_rule must be null when is_recurring is false")
        return self


class TaskUpdate(BaseModel):
    """Request body for updating a task. All fields optional."""
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)
    priority: Optional[str] = Field(default=None)
    tags: Optional[List[str]] = Field(default=None)
    due_at: Optional[datetime] = Field(default=None)
    is_recurring: Optional[bool] = Field(default=None)
    recurrence_rule: Optional[str] = Field(default=None)

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in VALID_PRIORITIES:
            raise ValueError(f"priority must be one of: {', '.join(VALID_PRIORITIES)}")
        return v

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, v):
        if v is not None:
            return list(dict.fromkeys(tag for tag in v if tag.strip()))
        return v

    @field_validator("recurrence_rule")
    @classmethod
    def validate_recurrence_rule(cls, v):
        if v is not None and v not in VALID_RECURRENCE_RULES:
            raise ValueError(f"recurrence_rule must be one of: {', '.join(VALID_RECURRENCE_RULES)}")
        return v


class TaskResponse(BaseModel):
    """Response body for task operations — includes Phase V fields."""
    id: UUID
    user_id: str
    title: str
    description: Optional[str]
    completed: bool
    priority: Optional[str]
    tags: List[str]
    due_at: Optional[datetime]
    is_recurring: bool
    recurrence_rule: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    """Response body for listing tasks."""
    tasks: list[TaskResponse]
