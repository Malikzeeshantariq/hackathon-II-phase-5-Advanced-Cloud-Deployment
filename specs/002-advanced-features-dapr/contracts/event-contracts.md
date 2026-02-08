# Event Contracts: Phase V Part A — Dapr Pub/Sub Event Schemas

**Branch**: `002-advanced-features-dapr` | **Date**: 2026-02-08 | **Phase**: 1

---

## Pub/Sub Component

**Component Name**: `pubsub`
**Type**: `pubsub.kafka`
**Backend**: Redpanda (Kafka-compatible, local) or Kafka (cloud)

---

## Topics

| Topic          | Publisher          | Consumers                          | Purpose                        |
|----------------|--------------------|------------------------------------|--------------------------------|
| `task-events`  | Backend (Chat API) | Recurring Task Service, Audit Service | Task lifecycle notifications   |
| `reminders`    | Backend (Chat API) | Notification Service               | Reminder trigger notifications |
| `task-updates` | Backend (Chat API) | (Reserved for WebSocket/Realtime)  | Client sync notifications      |

---

## 1. TaskEvent Schema (topic: `task-events`)

**Version**: 1.0

```json
{
  "specversion": "1.0",
  "type": "com.todo.task.lifecycle",
  "source": "todo-backend",
  "id": "<event_id: uuid>",
  "time": "<iso8601>",
  "datacontenttype": "application/json",
  "data": {
    "event_type": "created | updated | completed | deleted",
    "task_id": "<uuid>",
    "user_id": "<string>",
    "task_data": {
      "title": "<string>",
      "description": "<string | null>",
      "completed": "<boolean>",
      "priority": "<low | medium | high | critical | null>",
      "tags": ["<string>"],
      "due_at": "<iso8601 | null>",
      "is_recurring": "<boolean>",
      "recurrence_rule": "<daily | weekly | monthly | null>"
    },
    "timestamp": "<iso8601>"
  }
}
```

**Envelope**: CloudEvents 1.0 format (Dapr default)

**Consumer Contract**:
- Recurring Task Service: Filters `event_type == "completed"` AND `task_data.is_recurring == true`
- Audit Service: Processes ALL event types

---

## 2. ReminderEvent Schema (topic: `reminders`)

**Version**: 1.0

```json
{
  "specversion": "1.0",
  "type": "com.todo.reminder.trigger",
  "source": "todo-backend",
  "id": "<event_id: uuid>",
  "time": "<iso8601>",
  "datacontenttype": "application/json",
  "data": {
    "reminder_id": "<uuid>",
    "task_id": "<uuid>",
    "title": "<string>",
    "user_id": "<string>",
    "due_at": "<iso8601 | null>",
    "remind_at": "<iso8601>",
    "timestamp": "<iso8601>"
  }
}
```

**Consumer Contract**:
- Notification Service: Processes all events, logs or delivers notification

---

## 3. TaskUpdateEvent Schema (topic: `task-updates`)

**Version**: 1.0

```json
{
  "specversion": "1.0",
  "type": "com.todo.task.update",
  "source": "todo-backend",
  "id": "<event_id: uuid>",
  "time": "<iso8601>",
  "datacontenttype": "application/json",
  "data": {
    "task_id": "<uuid>",
    "user_id": "<string>",
    "change_type": "created | updated | completed | deleted",
    "timestamp": "<iso8601>"
  }
}
```

**Consumer Contract**:
- Reserved for future WebSocket/Realtime service (Part B/C)
- No consumer in Part A

---

## 4. Idempotency Contract

All events include a unique `id` field (CloudEvents `id`).

**Consumer Responsibility**:
- Before processing, check if `id` has been processed (via `processed_event` table)
- If already processed: ACK the message, skip processing
- If new: process, record `id` in `processed_event` table, ACK

**Delivery Guarantee**: At-least-once (Dapr Pub/Sub default with Kafka)

---

## 5. Schema Versioning

- Event schemas are versioned in this document
- Breaking changes require a new topic or a version field in the payload
- Consumers MUST ignore unknown fields (forward compatibility)
- Consumers MUST NOT require fields that may be absent in older versions
