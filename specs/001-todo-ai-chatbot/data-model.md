# Data Model: Todo AI Chatbot (Phase 3)

**Branch**: `001-todo-ai-chatbot` | **Date**: 2026-01-19 | **Spec**: [spec.md](./spec.md)

## Overview

This document defines the database schema additions for Phase 3 conversational AI features. All models use SQLModel for ORM mapping and Pydantic validation.

---

## Entity Relationship Diagram

```
┌─────────────┐       ┌──────────────────┐       ┌─────────────┐
│    User     │       │   Conversation   │       │   Message   │
│  (Phase 2)  │       │                  │       │             │
├─────────────┤       ├──────────────────┤       ├─────────────┤
│ id (PK)     │──────<│ id (PK)          │──────<│ id (PK)     │
│ email       │       │ user_id (FK)     │       │ conv_id(FK) │
│ ...         │       │ created_at       │       │ role        │
└─────────────┘       │ updated_at       │       │ content     │
                      └──────────────────┘       │ created_at  │
                                                 └─────────────┘
                                                       │
                                                       │
                                                       ▼
                                                 ┌─────────────┐
                                                 │  ToolCall   │
                                                 ├─────────────┤
                                                 │ id (PK)     │
                                                 │ message_id  │
                                                 │ tool_name   │
                                                 │ parameters  │
                                                 │ result      │
                                                 │ created_at  │
                                                 └─────────────┘
```

---

## Models

### Conversation

Represents a chat session between a user and the AI assistant.

```python
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field, Relationship


class ConversationBase(SQLModel):
    """Base conversation fields for validation."""
    pass


class Conversation(ConversationBase, table=True):
    """Database model for conversations."""
    __tablename__ = "conversations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    messages: list["Message"] = Relationship(back_populates="conversation")


class ConversationCreate(ConversationBase):
    """Schema for creating a conversation."""
    user_id: UUID


class ConversationRead(ConversationBase):
    """Schema for reading a conversation."""
    id: UUID
    user_id: UUID
    created_at: datetime
    updated_at: datetime
```

**Constraints**:
- One active conversation per user (Phase 3 scope)
- `user_id` must reference existing user
- Soft delete not implemented (hard delete for now)

**Indexes**:
- `idx_conversations_user_id` on `user_id` (for user lookup)

---

### Message

Represents a single message in a conversation.

```python
from enum import Enum


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
    conversation: Optional[Conversation] = Relationship(back_populates="messages")
    tool_calls: list["ToolCall"] = Relationship(back_populates="message")


class MessageCreate(MessageBase):
    """Schema for creating a message."""
    conversation_id: UUID


class MessageRead(MessageBase):
    """Schema for reading a message."""
    id: UUID
    conversation_id: UUID
    created_at: datetime
    tool_calls: list["ToolCallRead"] = []
```

**Constraints**:
- `content` required, max 10,000 characters
- `role` must be 'user' or 'assistant'
- Messages ordered by `created_at` for history reconstruction

**Indexes**:
- `idx_messages_conversation_id` on `conversation_id` (for history lookup)
- `idx_messages_created_at` on `created_at` (for ordering)

---

### ToolCall

Records each tool invocation by the AI agent for auditability.

```python
from typing import Any


class ToolCallBase(SQLModel):
    """Base tool call fields for validation."""
    tool_name: str = Field(min_length=1, max_length=100)
    parameters: dict[str, Any] = Field(default_factory=dict)
    result: dict[str, Any] = Field(default_factory=dict)


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
    parameters: dict = Field(default_factory=dict, sa_type=JSONB)
    result: dict = Field(default_factory=dict, sa_type=JSONB)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationships
    message: Optional[Message] = Relationship(back_populates="tool_calls")


class ToolCallCreate(ToolCallBase):
    """Schema for creating a tool call."""
    message_id: UUID


class ToolCallRead(ToolCallBase):
    """Schema for reading a tool call."""
    id: UUID
    message_id: UUID
    created_at: datetime
```

**Constraints**:
- `tool_name` must match defined MCP tools
- `parameters` stores input to tool
- `result` stores tool output (success or error)
- Tool calls always belong to assistant messages

**Indexes**:
- `idx_tool_calls_message_id` on `message_id`
- `idx_tool_calls_tool_name` on `tool_name` (for analytics)

---

## Migration SQL

```sql
-- Phase 3: AI Chatbot Tables

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);

-- Messages table
CREATE TYPE message_role AS ENUM ('user', 'assistant');

CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role message_role NOT NULL,
    content TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- Tool calls table
CREATE TABLE IF NOT EXISTS tool_calls (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID NOT NULL REFERENCES messages(id) ON DELETE CASCADE,
    tool_name VARCHAR(100) NOT NULL,
    parameters JSONB NOT NULL DEFAULT '{}',
    result JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_tool_calls_message_id ON tool_calls(message_id);
CREATE INDEX idx_tool_calls_tool_name ON tool_calls(tool_name);

-- Updated_at trigger for conversations
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
```

---

## Data Isolation

### User Scoping Rules

| Entity | Scope Rule |
|--------|------------|
| Conversation | `WHERE user_id = :current_user_id` |
| Message | Via conversation join |
| ToolCall | Via message → conversation join |
| Task | `WHERE user_id = :current_user_id` (existing) |

### Enforcement Points

1. **Chat Endpoint**: Conversation created/loaded with verified `user_id`
2. **MCP Tools**: All tools receive `user_id` from context, not user input
3. **Query Layer**: Repository methods enforce user_id filter

---

## Existing Models (Phase 2)

### Task (unchanged)

```python
class Task(SQLModel, table=True):
    __tablename__ = "tasks"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(foreign_key="users.id", index=True, nullable=False)
    title: str = Field(nullable=False, max_length=255)
    description: Optional[str] = Field(default=None)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### User (unchanged)

```python
class User(SQLModel, table=True):
    __tablename__ = "users"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    email: str = Field(unique=True, index=True, nullable=False)
    # ... other fields managed by Better Auth
```

---

## Query Patterns

### Load Conversation with History

```python
async def get_conversation_with_messages(
    session: AsyncSession,
    user_id: UUID,
    conversation_id: UUID
) -> Conversation | None:
    statement = (
        select(Conversation)
        .where(Conversation.id == conversation_id)
        .where(Conversation.user_id == user_id)
        .options(
            selectinload(Conversation.messages)
            .selectinload(Message.tool_calls)
        )
    )
    result = await session.exec(statement)
    return result.first()
```

### Get or Create Conversation

```python
async def get_or_create_conversation(
    session: AsyncSession,
    user_id: UUID
) -> Conversation:
    # Find existing
    statement = (
        select(Conversation)
        .where(Conversation.user_id == user_id)
        .order_by(Conversation.updated_at.desc())
        .limit(1)
    )
    result = await session.exec(statement)
    conversation = result.first()

    if conversation:
        return conversation

    # Create new
    conversation = Conversation(user_id=user_id)
    session.add(conversation)
    await session.commit()
    await session.refresh(conversation)
    return conversation
```

---

## Document Status

**Status**: Complete
**Next Steps**: Generate API contracts in `contracts/`
