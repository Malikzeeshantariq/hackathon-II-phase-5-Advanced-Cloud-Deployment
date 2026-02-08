"""ToolCall model for the Todo AI Chatbot."""

from datetime import datetime
from typing import Any, Dict, Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship
from sqlalchemy.dialects.postgresql import JSONB
from pydantic import BaseModel


class ToolCallBase(SQLModel):
    """Base tool call fields for validation."""
    tool_name: str = Field(min_length=1, max_length=100)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    result: Dict[str, Any] = Field(default_factory=dict)


class ToolCall(ToolCallBase, table=True):
    """Database model for tool calls."""
    __tablename__ = "tool_calls"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    message_id: UUID = Field(
        foreign_key="messages.id",
        index=True,
        nullable=False
    )
    tool_name: str = Field(nullable=False, max_length=100)
    parameters: Dict = Field(default_factory=dict, sa_type=JSONB)
    result: Dict = Field(default_factory=dict, sa_type=JSONB)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    message: Optional["Message"] = Relationship(back_populates="tool_calls")


class ToolCallCreate(ToolCallBase):
    """Schema for creating a tool call."""
    message_id: UUID


class ToolCallRead(ToolCallBase):
    """Schema for reading a tool call."""
    id: UUID
    message_id: UUID
    created_at: datetime