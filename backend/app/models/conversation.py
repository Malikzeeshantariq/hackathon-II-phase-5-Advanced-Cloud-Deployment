"""Conversation model for the Todo AI Chatbot."""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from app.models.message import Message


class ConversationBase(SQLModel):
    """Base conversation fields for validation."""
    pass


class Conversation(ConversationBase, table=True):
    """Database model for conversations."""
    __tablename__ = "conversations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True, nullable=False)  # String to match Better Auth user IDs
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    messages: List["Message"] = Relationship(back_populates="conversation")


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    user_id: str


class ConversationRead(ConversationBase):
    """Schema for reading a conversation."""
    id: UUID
    user_id: str
    created_at: datetime
    updated_at: datetime
