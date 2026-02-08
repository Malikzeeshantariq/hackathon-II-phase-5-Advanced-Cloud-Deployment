# API Contracts: Phase V Part A — Advanced Task Features & Event-Driven Architecture

**Branch**: `002-advanced-features-dapr` | **Date**: 2026-02-08 | **Phase**: 1

All endpoints require JWT in `Authorization: Bearer <token>` header.
All endpoints enforce `user_id` from token matches URL `{user_id}`.

---

## 1. Task Endpoints (Extended)

### 1.1 Create Task (Extended)

```
POST /api/{user_id}/tasks
```

**Request Body** (extended):
```json
{
  "title": "string (required, 1-255 chars)",
  "description": "string | null",
  "priority": "low | medium | high | critical | null",
  "tags": ["string"] | null,
  "due_at": "iso8601 datetime | null",
  "is_recurring": false,
  "recurrence_rule": "daily | weekly | monthly | null"
}
```

**Response** `201 Created`:
```json
{
  "id": "uuid",
  "user_id": "string",
  "title": "string",
  "description": "string | null",
  "completed": false,
  "priority": "string | null",
  "tags": ["string"],
  "due_at": "iso8601 | null",
  "is_recurring": false,
  "recurrence_rule": "string | null",
  "created_at": "iso8601",
  "updated_at": "iso8601"
}
```

**Side Effects**:
- Publishes `TaskEvent(created)` to `task-events` topic
- Publishes `TaskUpdateEvent(created)` to `task-updates` topic

**Errors**:
- `400`: Invalid priority value, invalid recurrence_rule, is_recurring=true without recurrence_rule
- `401`: Missing or invalid JWT
- `403`: Token user_id mismatch

---

### 1.2 List Tasks (Extended)

```
GET /api/{user_id}/tasks?priority={value}&tags={tag1,tag2}&status={completed|pending|all}&due_before={iso8601}&due_after={iso8601}&search={query}&sort_by={field}&sort_order={asc|desc}
```

**Query Parameters** (all optional):
| Parameter   | Type   | Description                              |
|-------------|--------|------------------------------------------|
| priority    | string | Filter by priority (low/medium/high/critical) |
| tags        | string | Comma-separated tags (AND filter)        |
| status      | string | `completed`, `pending`, or `all` (default: all) |
| due_before  | string | ISO8601 datetime upper bound             |
| due_after   | string | ISO8601 datetime lower bound             |
| search      | string | Case-insensitive substring match on title, description, tags |
| sort_by     | string | `created_at`, `due_at`, `priority`, `title` (default: created_at) |
| sort_order  | string | `asc` or `desc` (default: desc)          |

**Response** `200 OK`:
```json
[
  {
    "id": "uuid",
    "user_id": "string",
    "title": "string",
    "description": "string | null",
    "completed": false,
    "priority": "string | null",
    "tags": ["string"],
    "due_at": "iso8601 | null",
    "is_recurring": false,
    "recurrence_rule": "string | null",
    "created_at": "iso8601",
    "updated_at": "iso8601"
  }
]
```

**Sort Behavior**:
- `due_at`: Tasks without due dates sort to the end
- `priority`: Order is critical > high > medium > low > null

---

### 1.3 Update Task (Extended)

```
PUT /api/{user_id}/tasks/{task_id}
```

**Request Body** (all optional):
```json
{
  "title": "string",
  "description": "string | null",
  "priority": "low | medium | high | critical | null",
  "tags": ["string"] | null,
  "due_at": "iso8601 datetime | null",
  "is_recurring": false,
  "recurrence_rule": "daily | weekly | monthly | null"
}
```

**Response** `200 OK`: Full task object (same as create response)

**Side Effects**:
- Publishes `TaskEvent(updated)` to `task-events` topic
- Publishes `TaskUpdateEvent(updated)` to `task-updates` topic
- If `is_recurring` changed to false: existing recurrence stops on next completion

**Errors**:
- `400`: Invalid values
- `401`/`403`/`404`: Auth and ownership errors

---

### 1.4 Complete Task (Existing + Events)

```
PATCH /api/{user_id}/tasks/{task_id}/complete
```

**Response** `200 OK`: Full task object with `completed` toggled

**Side Effects**:
- Publishes `TaskEvent(completed)` to `task-events` topic
- Publishes `TaskUpdateEvent(completed)` to `task-updates` topic
- If task `is_recurring` and completed=true: Recurring Task Service will create next occurrence

---

### 1.5 Delete Task (Existing + Events)

```
DELETE /api/{user_id}/tasks/{task_id}
```

**Response** `200 OK`: `{"message": "Task deleted successfully"}`

**Side Effects**:
- Publishes `TaskEvent(deleted)` to `task-events` topic
- Publishes `TaskUpdateEvent(deleted)` to `task-updates` topic
- Cascades: all reminders for this task are deleted
- Cascades: all scheduled Dapr Jobs for this task's reminders are cancelled

---

## 2. Reminder Endpoints (New)

### 2.1 Create Reminder

```
POST /api/{user_id}/tasks/{task_id}/reminders
```

**Request Body**:
```json
{
  "remind_at": "iso8601 datetime (required, must be in future)"
}
```

**Response** `201 Created`:
```json
{
  "id": "uuid",
  "task_id": "uuid",
  "user_id": "string",
  "remind_at": "iso8601",
  "created_at": "iso8601"
}
```

**Side Effects**:
- Schedules Dapr Job at `remind_at` timestamp

**Errors**:
- `400`: `remind_at` is in the past
- `401`/`403`/`404`: Auth, ownership, or task not found

---

### 2.2 List Reminders for a Task

```
GET /api/{user_id}/tasks/{task_id}/reminders
```

**Response** `200 OK`:
```json
[
  {
    "id": "uuid",
    "task_id": "uuid",
    "user_id": "string",
    "remind_at": "iso8601",
    "created_at": "iso8601"
  }
]
```

---

### 2.3 Delete Reminder

```
DELETE /api/{user_id}/tasks/{task_id}/reminders/{reminder_id}
```

**Response** `200 OK`: `{"message": "Reminder deleted successfully"}`

**Side Effects**:
- Cancels the associated Dapr Job

---

## 3. Audit Endpoints (New)

### 3.1 List Audit Entries for User

```
GET /api/{user_id}/audit?task_id={uuid}&event_type={type}&limit={n}&offset={n}
```

**Query Parameters** (all optional):
| Parameter  | Type   | Description                                 |
|------------|--------|---------------------------------------------|
| task_id    | uuid   | Filter by specific task                     |
| event_type | string | Filter by type (created/updated/completed/deleted) |
| limit      | int    | Max entries (default: 50, max: 200)         |
| offset     | int    | Pagination offset (default: 0)              |

**Response** `200 OK`:
```json
[
  {
    "id": "uuid",
    "event_type": "string",
    "task_id": "uuid",
    "user_id": "string",
    "event_data": {},
    "timestamp": "iso8601"
  }
]
```

**Note**: This endpoint is served by the Audit Service via Dapr Service Invocation or direct route.

---

## 4. Internal Endpoints (Dapr Callbacks — Not User-Facing)

### 4.1 Dapr Job Callback (Reminder Trigger)

```
POST /internal/jobs/reminder-trigger
```

Called by Dapr Jobs API when a scheduled reminder fires.

**Request Body** (from Dapr Job data):
```json
{
  "reminder_id": "uuid",
  "task_id": "uuid",
  "user_id": "string"
}
```

**Action**: Looks up reminder and task, publishes ReminderEvent to `reminders` topic.

---

### 4.2 Dapr Pub/Sub Subscription Endpoints

**Backend** (Chat API):
- `POST /dapr/subscribe` — Returns subscription list

**Notification Service**:
- `POST /events/reminders` — Handles reminder events from `reminders` topic

**Recurring Task Service**:
- `POST /events/task-events` — Handles task lifecycle events from `task-events` topic

**Audit Service**:
- `POST /events/task-events` — Handles task lifecycle events from `task-events` topic

---

## 5. Dapr Service Invocation Contracts

### 5.1 Recurring Task Service → Backend (Create Next Task)

```
POST /api/{user_id}/tasks  (via Dapr Service Invocation to app-id: "todo-backend")
```

Uses standard task creation endpoint. The Recurring Task Service authenticates via a service-to-service mechanism (internal Dapr call, no external JWT required for internal invocation).

---

## 6. Error Response Format (All Endpoints)

```json
{
  "detail": "Human-readable error message"
}
```

**HTTP Status Codes**:
| Code | Meaning                      |
|------|------------------------------|
| 200  | Success                      |
| 201  | Created                      |
| 400  | Validation error             |
| 401  | Missing or invalid JWT       |
| 403  | User ID mismatch             |
| 404  | Resource not found           |
| 500  | Internal server error        |
