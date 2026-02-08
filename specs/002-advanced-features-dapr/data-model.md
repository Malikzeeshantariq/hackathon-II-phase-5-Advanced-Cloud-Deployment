# Data Model: Phase V Part A — Advanced Task Features & Event-Driven Architecture

**Branch**: `002-advanced-features-dapr` | **Date**: 2026-02-08 | **Phase**: 1

## Entity Relationship Overview

```
User (external, Better Auth)
 ├── owns many → Task
 ├── owns many → Reminder
 └── owns many → AuditEntry

Task
 ├── has many → Reminder
 └── generates → TaskEvent (domain event, not persisted as entity)

Reminder
 └── generates → ReminderEvent (domain event, not persisted as entity)
```

---

## 1. Task (Extended)

**Table**: `task`
**Owner**: Chat API + MCP (backend service)

### Current Fields (Phase II — Immutable)

| Field       | Type             | Constraints                    |
|-------------|------------------|--------------------------------|
| id          | UUID             | PK, auto-generated             |
| user_id     | String           | NOT NULL, indexed              |
| title       | String(255)      | NOT NULL                       |
| description | String (text)    | nullable                       |
| completed   | Boolean          | default: false                 |
| created_at  | DateTime (UTC)   | auto-generated                 |
| updated_at  | DateTime (UTC)   | auto-updated                   |

### New Fields (Phase V Part A)

| Field           | Type                     | Constraints                          |
|-----------------|--------------------------|--------------------------------------|
| priority        | String(10)               | nullable, values: low/medium/high/critical |
| tags            | Array of String          | default: empty array, user-scoped    |
| due_at          | DateTime (UTC)           | nullable                             |
| is_recurring    | Boolean                  | default: false                       |
| recurrence_rule | String(20)               | nullable, values: daily/weekly/monthly |

### Validation Rules

- `priority` MUST be one of: `low`, `medium`, `high`, `critical`, or null
- `tags` MUST be an array of non-empty strings; duplicates removed on write
- `due_at` MUST be a valid UTC timestamp or null
- `is_recurring` = true requires `recurrence_rule` to be non-null
- `recurrence_rule` MUST be one of: `daily`, `weekly`, `monthly`, or null
- If `is_recurring` = false, `recurrence_rule` MUST be null

### Indexes

- Existing: `idx_task_user_id` on `user_id`
- New: `idx_task_priority` on `(user_id, priority)` for filtered queries
- New: `idx_task_due_at` on `(user_id, due_at)` for date range queries
- New: `idx_task_tags` GIN index on `tags` for array containment queries

---

## 2. Reminder (New)

**Table**: `reminder`
**Owner**: Chat API + MCP (backend service)

| Field      | Type           | Constraints                              |
|------------|----------------|------------------------------------------|
| id         | UUID           | PK, auto-generated                       |
| task_id    | UUID           | FK → task.id, NOT NULL, ON DELETE CASCADE |
| user_id    | String         | NOT NULL, indexed (denormalized for isolation) |
| remind_at  | DateTime (UTC) | NOT NULL, must be in the future at creation |
| created_at | DateTime (UTC) | auto-generated                           |

### Validation Rules

- `remind_at` MUST be in the future at creation time (FR-013)
- `task_id` MUST reference an existing task owned by the same `user_id`
- Deleting a task cascades to delete all its reminders (FR-012)

### Indexes

- `idx_reminder_task_id` on `task_id`
- `idx_reminder_user_id` on `user_id`
- `idx_reminder_remind_at` on `remind_at` for scheduled job queries

---

## 3. AuditEntry (New)

**Table**: `audit_entry`
**Owner**: Audit Service

| Field      | Type           | Constraints                    |
|------------|----------------|--------------------------------|
| id         | UUID           | PK, auto-generated             |
| event_type | String(20)     | NOT NULL (created/updated/completed/deleted) |
| task_id    | UUID           | NOT NULL (reference, not FK)   |
| user_id    | String         | NOT NULL, indexed              |
| event_data | JSON           | NOT NULL (snapshot of event payload) |
| timestamp  | DateTime (UTC) | NOT NULL                       |

### Validation Rules

- Append-only: no UPDATE or DELETE operations allowed on this table
- `event_type` MUST be one of: `created`, `updated`, `completed`, `deleted`
- `task_id` is NOT a foreign key (task may be deleted; audit entry persists)
- `event_data` stores the full event payload for auditability

### Indexes

- `idx_audit_user_id` on `user_id` for user-scoped queries
- `idx_audit_task_id` on `task_id` for task history queries
- `idx_audit_timestamp` on `timestamp` for chronological queries

---

## 4. ProcessedEvent (New — Idempotency)

**Table**: `processed_event`
**Owner**: Each consuming service maintains its own instance

| Field        | Type           | Constraints         |
|--------------|----------------|---------------------|
| event_id     | UUID           | PK                  |
| service_name | String(50)     | NOT NULL            |
| processed_at | DateTime (UTC) | auto-generated      |

### Purpose

Ensures idempotent event processing (FR-020, SC-008). Before processing any event, consumers check this table. If the `event_id` exists, the event is skipped.

---

## 5. Domain Events (Not Persisted — Wire Format)

### 5.1 TaskEvent

Published to topic: `task-events`

```json
{
  "event_id": "uuid",
  "event_type": "created | updated | completed | deleted",
  "task_id": "uuid",
  "user_id": "string",
  "task_data": {
    "title": "string",
    "description": "string | null",
    "completed": "boolean",
    "priority": "string | null",
    "tags": ["string"],
    "due_at": "iso8601 | null",
    "is_recurring": "boolean",
    "recurrence_rule": "string | null"
  },
  "timestamp": "iso8601"
}
```

### 5.2 ReminderEvent

Published to topic: `reminders`

```json
{
  "event_id": "uuid",
  "task_id": "uuid",
  "title": "string",
  "user_id": "string",
  "due_at": "iso8601 | null",
  "remind_at": "iso8601",
  "timestamp": "iso8601"
}
```

### 5.3 TaskUpdateEvent

Published to topic: `task-updates`

```json
{
  "event_id": "uuid",
  "task_id": "uuid",
  "user_id": "string",
  "change_type": "created | updated | completed | deleted",
  "timestamp": "iso8601"
}
```

Reserved for future real-time/WebSocket sync (Part B/C). Published alongside `task-events` for all lifecycle changes.

---

## 6. State Transitions

### Task Lifecycle

```
[created] → [updated]* → [completed] → [deleted]
                    ↘ [deleted]
```

- Any state can transition to `deleted`
- `completed` can toggle back to incomplete (existing behavior)
- Each transition publishes a TaskEvent

### Recurring Task Flow

```
[recurring task completed]
  → TaskEvent(completed) published
  → Recurring Task Service consumes
  → New Task created with next due_at
  → TaskEvent(created) published for new task
```

### Reminder Flow

```
[reminder created]
  → Dapr Job scheduled at remind_at
  → Job fires → callback endpoint called
  → ReminderEvent published to 'reminders' topic
  → Notification Service consumes and processes
```
