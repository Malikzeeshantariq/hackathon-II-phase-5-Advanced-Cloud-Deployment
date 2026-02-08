"""Message model for the Todo AI Chatbot."""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship
from pydantic import BaseModel


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"


class MessageBase(SQLModel):
    """Base message fields for validation."""
    content: str = Field(min_length=1, max_length=10000)
    role: MessageRole


class Message(MessageBase, table=True):
    """Database model for messages."""
    __tablename__ = "messages"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    conversation_id: UUID = Field(
        foreign_key="conversations.id",
        index=True,
        nullable=False
    )
    role: MessageRole = Field(nullable=False)
    content: str = Field(nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    conversation: Optional["Conversation"] = Relationship(back_populates="messages")
    tool_calls: List["ToolCall"] = Relationship(back_populates="message")


class MessageCreate(MessageBase):
    """Schema for creating a message."""
    conversation_id: UUID


class MessageRead(MessageBase):
    """Schema for reading a message."""
    id: UUID
    conversation_id: UUID
    created_at: datetime
    tool_calls: List["ToolCallRead"] = []