# Data Model: Todo CRUD API

**Feature**: 001-todo-crud-api
**Date**: 2025-01-08
**Phase**: 1 - Design

## Purpose

Define the data entities, their attributes, relationships, and validation rules for the Todo CRUD API.

---

## Entities

### Task

Represents a unit of work to be completed by a user.

| Attribute | Type | Required | Description | Spec Reference |
|-----------|------|----------|-------------|----------------|
| id | UUID | Yes | Unique task identifier (system-generated) | Assumptions |
| user_id | String | Yes | Owner's user ID (from JWT) | FR-002 |
| title | String(255) | Yes | Task title | FR-001 |
| description | Text | No | Detailed task description | FR-001 |
| completed | Boolean | Yes | Completion status (default: false) | FR-003, FR-009 |
| created_at | DateTime | Yes | Creation timestamp (auto-set) | FR-004 |
| updated_at | DateTime | Yes | Last modification timestamp | FR-008 |

#### Validation Rules

| Field | Rule | Error Response |
|-------|------|----------------|
| title | Required, 1-255 characters | 422: "Title is required" |
| title | Non-empty after trim | 422: "Title cannot be blank" |
| description | Optional, max 10000 characters | 422: "Description too long" |
| completed | Boolean only | 422: "Invalid completion status" |

#### State Transitions

```
[Created] ---(default)---> completed = false
     |
     v
[Incomplete] ---(PATCH /complete)---> [Completed]
     |                                      |
     v                                      v
[Updated] <---(PUT)--- [any state] ---(PUT)---> [Updated]
     |                                      |
     v                                      v
[Deleted] <---(DELETE)--- [any state] ---(DELETE)---> [Deleted]
```

---

### User (Virtual Entity)

Users are not stored in the Todo application database. User identity is derived from JWT tokens issued by Better Auth.

| Attribute | Type | Source | Description |
|-----------|------|--------|-------------|
| user_id | String | JWT `sub` claim | Unique user identifier |
| email | String | JWT `email` claim | User's email (optional use) |

**Note**: The User entity exists only as a JWT payload. No users table is created in the database.

---

## Relationships

```
User (1) -------- (*) Task
        owns/creates
```

- One user can have many tasks
- Each task belongs to exactly one user
- Relationship enforced via `user_id` foreign key (logical, not database FK)

---

## Database Schema (SQLModel)

```python
from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4
from sqlmodel import SQLModel, Field

class Task(SQLModel, table=True):
    """Task entity for Todo CRUD API.

    Spec References: FR-001 through FR-011
    """
    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: str = Field(index=True, nullable=False)
    title: str = Field(max_length=255, nullable=False)
    description: Optional[str] = Field(default=None)
    completed: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

---

## Pydantic Schemas (Request/Response)

### TaskCreate (Request)

```python
class TaskCreate(SQLModel):
    """Request body for creating a task.

    Spec Reference: FR-001
    """
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10000)
```

### TaskUpdate (Request)

```python
class TaskUpdate(SQLModel):
    """Request body for updating a task.

    Spec Reference: FR-007
    """
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=10000)
```

### TaskResponse (Response)

```python
class TaskResponse(SQLModel):
    """Response body for task operations.

    Spec Reference: FR-006
    """
    id: UUID
    title: str
    description: Optional[str]
    completed: bool
    created_at: datetime
    updated_at: datetime
```

### TaskListResponse (Response)

```python
class TaskListResponse(SQLModel):
    """Response body for listing tasks.

    Spec Reference: FR-005, FR-006
    """
    tasks: list[TaskResponse]
```

---

## Indexes

| Index Name | Column(s) | Type | Rationale |
|------------|-----------|------|-----------|
| `pk_tasks` | id | PRIMARY | Unique task identification |
| `idx_tasks_user_id` | user_id | BTREE | All queries filter by user |

---

## Data Integrity Rules

### Create Operation
- `id`: Auto-generated UUID
- `user_id`: Extracted from JWT (not from request body)
- `completed`: Always set to `false`
- `created_at`: Set to current UTC time
- `updated_at`: Set to current UTC time

### Update Operation
- `user_id`: Cannot be changed
- `id`: Cannot be changed
- `updated_at`: Auto-updated to current UTC time
- `created_at`: Cannot be changed

### Delete Operation
- Hard delete (no soft delete per FR-011)
- No cascading (tasks are leaf entities)

---

## Sample Data

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "user_abc123",
  "title": "Buy groceries",
  "description": "Milk, eggs, bread",
  "completed": false,
  "created_at": "2025-01-08T10:00:00Z",
  "updated_at": "2025-01-08T10:00:00Z"
}
```

---

## Security Considerations

### Data Isolation
- Every query MUST include `WHERE user_id = :jwt_user_id`
- Never expose tasks across user boundaries
- User ID in URL must match JWT user ID

### Sensitive Data
- No passwords stored (auth handled by Better Auth)
- No PII beyond what's in JWT
- Task content may contain user-sensitive information (not exposed cross-user)
