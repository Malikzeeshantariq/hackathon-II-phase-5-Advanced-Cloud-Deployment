# Feature Specification: Phase V Part A — Advanced Task Features & Event-Driven Architecture

**Feature Branch**: `002-advanced-features-dapr`
**Created**: 2026-02-08
**Status**: Draft
**Input**: Phase V Part A specification — advanced task features (due dates, reminders, recurring tasks, priorities, tags, search, filter, sort) with event-driven architecture via Dapr and Kafka-compatible backends
**Constitution**: sp.constitution v4.0.0
**Scope**: Phase V — Part A only

## Governing Documents

This specification MUST comply with:

- sp.constitution v4.0.0
- Phase II, III, IV artifacts (immutable contracts)
- Spec → Plan → Tasks → Code hierarchy

## Scope Boundary

**In Scope (Part A):**

- Advanced task features: due dates, reminders, recurring tasks
- Intermediate task features: priorities, tags, search, filter, sort
- Event-driven architecture using Kafka-compatible backends via Dapr Pub/Sub
- Distributed runtime: Dapr Pub/Sub, State, Jobs, Service Invocation, Secrets
- Multi-service topology: Chat API + MCP, Notification, Recurring Task, Audit
- Local deployment (Minikube + Helm + Dapr)

**Explicitly Out of Scope (Part B & C):**

- Cloud provider deployment (Oracle OKE)
- CI/CD pipelines (GitHub Actions)
- Production observability stack
- High availability / multi-region
- Cloud-only deployment constraints

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Organize Tasks with Priorities, Tags, and Sorting (Priority: P1)

A user wants to organize their task list by assigning priorities and tags to tasks, then filter and sort to focus on what matters most. The user creates several tasks, assigns priority levels (low, medium, high, critical) and tags (e.g., "work", "personal", "urgent"), then uses filter and sort to view only high-priority work tasks sorted by due date.

**Why this priority**: This is the foundational enhancement to the task model. Every other advanced feature (due dates, reminders, recurring) builds on these core attributes. Without priorities, tags, and query capabilities, the remaining stories have no organizational context.

**Independent Test**: Can be fully tested by creating tasks with priorities and tags, then using search/filter/sort operations. Delivers immediate organizational value even without due dates or events.

**Acceptance Scenarios**:

1. **Given** a user with existing tasks, **When** the user assigns a priority (low/medium/high/critical) to a task, **Then** the priority is persisted and visible when retrieving the task.
2. **Given** a user with existing tasks, **When** the user adds one or more tags to a task, **Then** the tags are persisted, user-scoped, and visible when retrieving the task.
3. **Given** a user with tagged and prioritized tasks, **When** the user filters by priority "high" and tag "work", **Then** only tasks matching both criteria are returned.
4. **Given** a user with multiple tasks, **When** the user sorts by priority (descending), **Then** critical tasks appear first, followed by high, medium, then low.
5. **Given** a user with tasks, **When** the user searches for "meeting" in title or description, **Then** only matching tasks scoped to that user are returned.
6. **Given** a user with tasks, **When** the user sorts by created date, due date, priority, or title, **Then** the results are correctly ordered by the chosen field.

---

### User Story 2 — Set Due Dates on Tasks (Priority: P2)

A user wants to assign deadlines to tasks so they can track what needs to be done and by when. The user creates a task with a due date, later updates the due date, and can also remove it. The user filters their task list to see tasks due within the next 7 days.

**Why this priority**: Due dates are a prerequisite for reminders and recurring tasks. They add time-awareness to the task system and enable time-based filtering and sorting.

**Independent Test**: Can be fully tested by creating tasks with due dates, updating them, removing them, and filtering/sorting by due date range. Delivers scheduling value independently of events.

**Acceptance Scenarios**:

1. **Given** the task creation flow, **When** the user provides a due date timestamp, **Then** the task is created with the due date persisted.
2. **Given** a task with a due date, **When** the user updates the due date, **Then** the new due date replaces the old one and is persisted.
3. **Given** a task with a due date, **When** the user removes the due date, **Then** the task no longer has a due date.
4. **Given** a task without a due date, **When** the user queries tasks, **Then** the task appears with no due date value (not a default or zero date).
5. **Given** multiple tasks with various due dates, **When** the user filters by a date range (e.g., next 7 days), **Then** only tasks with due dates within that range are returned.
6. **Given** multiple tasks, **When** the user sorts by due date, **Then** tasks without due dates appear at the end, and tasks with due dates are ordered chronologically.

---

### User Story 3 — Receive Reminders for Upcoming Tasks (Priority: P3)

A user wants to set reminders on tasks so they are notified before a deadline. The user sets a reminder for a task due tomorrow, and the system automatically triggers a notification at the specified time without polling.

**Why this priority**: Reminders introduce the event-driven architecture — scheduled jobs, event publishing, and cross-service communication. This is the first story that requires Dapr Jobs and Pub/Sub.

**Independent Test**: Can be fully tested by scheduling a reminder, verifying the job is created, letting the job trigger, verifying the event is published, and confirming the notification service receives and processes it.

**Acceptance Scenarios**:

1. **Given** a task with a due date, **When** the user sets a reminder at a specific time, **Then** a reminder record is created and a scheduled job is registered (no polling).
2. **Given** a scheduled reminder, **When** the reminder time arrives, **Then** a reminder event is published to the event bus automatically.
3. **Given** a published reminder event, **When** the notification service receives it, **Then** the notification is processed and the user is informed.
4. **Given** a task with a reminder, **When** the user deletes the task, **Then** the associated reminder and scheduled job are cancelled.
5. **Given** a task, **When** the user sets multiple reminders at different times, **Then** each reminder triggers independently at its scheduled time.
6. **Given** a reminder event, **When** the notification service is temporarily unavailable, **Then** the event is retained and processed when the service recovers (at-least-once delivery).

---

### User Story 4 — Automatically Recreate Recurring Tasks (Priority: P4)

A user wants to set tasks as recurring (daily, weekly, monthly) so that when a recurring task is completed, the next occurrence is automatically created. The user marks a weekly task as complete, and a new task for the next week appears without manual intervention.

**Why this priority**: Recurring tasks are the most complex event-driven workflow — they require event publishing on task completion, cross-service consumption, and automatic task creation. This builds on all previous stories.

**Independent Test**: Can be fully tested by creating a recurring task, completing it, verifying the completion event is published, and confirming the recurring task service creates the next occurrence with the correct next due date.

**Acceptance Scenarios**:

1. **Given** the task creation flow, **When** the user marks a task as recurring with a recurrence rule (daily/weekly/monthly), **Then** the recurrence configuration is persisted.
2. **Given** a recurring task, **When** the user completes it, **Then** a task-completed event is published to the event bus.
3. **Given** a task-completed event for a recurring task, **When** the recurring task service processes it, **Then** a new task is created with the next occurrence date based on the recurrence rule.
4. **Given** a daily recurring task completed on Monday, **When** the next occurrence is created, **Then** the new task has a due date of Tuesday.
5. **Given** a weekly recurring task completed on Wednesday, **When** the next occurrence is created, **Then** the new task has a due date of next Wednesday.
6. **Given** a monthly recurring task completed on January 31, **When** the next occurrence is created, **Then** the new task has a due date of February 28 (or 29 in leap year), handling month-end edge cases.
7. **Given** a recurring task, **When** the user removes the recurrence rule, **Then** completing the task does NOT create a new occurrence.

---

### User Story 5 — Track Task Activity via Audit Log (Priority: P5)

A user (or system administrator) wants an immutable audit trail of all task lifecycle events — creation, updates, completion, deletion — so that activity can be reviewed for accountability and debugging.

**Why this priority**: The audit service is optional and additive. It subscribes to existing events without affecting core functionality. It demonstrates the extensibility of the event-driven architecture.

**Independent Test**: Can be tested by performing task CRUD operations and verifying that corresponding audit entries are recorded in the audit log, independent of other features.

**Acceptance Scenarios**:

1. **Given** a task is created, **When** the task-created event is published, **Then** the audit service records an immutable entry with task details, user, and timestamp.
2. **Given** a task is updated (priority, tags, due date, title), **When** the task-updated event is published, **Then** the audit service records what changed.
3. **Given** a task is completed, **When** the task-completed event is published, **Then** the audit service records the completion.
4. **Given** a task is deleted, **When** the task-deleted event is published, **Then** the audit service records the deletion.
5. **Given** audit entries exist, **When** querying the audit log for a user, **Then** only that user's activity is returned (user-scoped).

---

### Edge Cases

- What happens when a reminder is set for a time in the past? The system MUST reject it with a clear error.
- What happens when a recurring task's recurrence rule is invalid (e.g., empty string)? The system MUST validate and reject invalid rules.
- What happens when a user assigns a priority value outside the allowed set? The system MUST reject it with a validation error.
- What happens when a user searches with an empty query? The system MUST return all tasks (unfiltered) for that user.
- What happens when a user filters by a tag that no tasks have? The system MUST return an empty result set (not an error).
- What happens when the event bus is temporarily unreachable? Events MUST be retried or queued; no data loss.
- What happens when a recurring task is completed but the recurring task service is down? The event MUST be retained and processed when the service recovers.
- What happens when multiple reminders fire simultaneously for the same task? Each reminder MUST be processed independently.
- What happens when a month-end recurring task (e.g., Jan 31) cycles into a shorter month (e.g., Feb)? The system MUST handle date clamping to the last valid day.

## Requirements *(mandatory)*

### Functional Requirements

**Task Model Extensions:**

- **FR-001**: System MUST support an optional priority field on tasks with values: low, medium, high, critical.
- **FR-002**: System MUST support zero or more tags per task, scoped to the owning user.
- **FR-003**: System MUST support an optional due date (timestamp) on tasks.
- **FR-004**: System MUST support marking a task as recurring with a recurrence rule (daily, weekly, monthly).
- **FR-005**: System MUST support creating, updating, and deleting reminders associated with tasks.

**Query Capabilities:**

- **FR-006**: System MUST support searching tasks by title, description, and tags, scoped per user.
- **FR-007**: System MUST support filtering tasks by completion status, priority, tags, and due date range.
- **FR-008**: System MUST support sorting tasks by created date, due date, priority, and title.

**Reminder Workflows:**

- **FR-009**: Reminders MUST be scheduled via non-polling scheduled jobs (no cron polling loops).
- **FR-010**: When a reminder triggers, the system MUST publish a reminder event to the event bus.
- **FR-011**: A notification service MUST consume reminder events and process notifications.
- **FR-012**: Deleting a task MUST cancel all associated reminders and scheduled jobs.
- **FR-013**: System MUST reject reminders set for a time in the past.

**Recurring Task Workflows:**

- **FR-014**: When a recurring task is completed, the system MUST publish a task-completed event.
- **FR-015**: A recurring task service MUST consume task-completed events and create the next occurrence automatically.
- **FR-016**: The next occurrence MUST have a due date calculated from the recurrence rule, handling month-end edge cases.
- **FR-017**: Removing the recurrence rule from a task MUST stop future auto-creation on completion.

**Event Architecture:**

- **FR-018**: All task lifecycle events (created, updated, completed, deleted) MUST be published to the event bus.
- **FR-019**: Services MUST communicate asynchronously via events for all event-driven workflows.
- **FR-020**: Event delivery MUST be at-least-once; consumers MUST be idempotent.
- **FR-021**: The system MUST NOT use direct message broker client libraries in application services; all eventing MUST go through the distributed runtime abstraction.

**Audit:**

- **FR-022**: An audit service MUST subscribe to task lifecycle events and record immutable, user-scoped activity entries.

**Service Architecture:**

- **FR-023**: The system MUST have distinct services: Chat API + MCP, Notification, Recurring Task, Audit.
- **FR-024**: All services MUST be stateless; all state MUST be persisted externally.
- **FR-025**: Inter-service communication MUST use the distributed runtime's service invocation or event bus.

### Key Entities

- **Task**: Represents a user's work item. Has title, description, completion status, optional priority (low/medium/high/critical), optional tags (list), optional due date, optional recurrence rule (daily/weekly/monthly), timestamps (created/updated), and owning user reference.
- **Reminder**: Represents a scheduled notification for a task. Has owning task reference, owning user reference, reminder time, and creation timestamp. One task may have multiple reminders.
- **Audit Entry**: Represents an immutable record of a task lifecycle event. Has event type (created/updated/completed/deleted), task reference, user reference, event data, and timestamp.
- **Task Event**: Represents a domain event published when a task changes state. Has event type, task identifier, task data snapshot, user reference, and timestamp.
- **Reminder Event**: Represents a domain event published when a reminder fires. Has task identifier, task title, user reference, due date, reminder time, and timestamp.

### Assumptions

- Notification delivery mechanism (email, push, in-app) is deferred to a later specification. The notification service in Part A processes and logs events; delivery channel integration is out of scope.
- The recurrence rule supports three fixed intervals (daily, weekly, monthly). Custom cron expressions or complex RRULE patterns are out of scope for Part A.
- The audit log is append-only and does not support deletion or modification of entries.
- Search is basic text matching (case-insensitive substring). Full-text search with ranking is out of scope for Part A.
- Tag values are free-form strings. A tag taxonomy or autocomplete system is out of scope.
- Priority values are a fixed enum (low, medium, high, critical). Custom priority levels are out of scope.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Users can assign priorities and tags to tasks and retrieve them within 2 seconds through search, filter, and sort operations.
- **SC-002**: Users can set, update, and remove due dates on tasks with changes reflected immediately on the next retrieval.
- **SC-003**: Scheduled reminders fire within 60 seconds of their target time and produce a notification event without any polling mechanism.
- **SC-004**: When a recurring task is completed, the next occurrence is automatically created within 30 seconds with the correct next due date.
- **SC-005**: All task lifecycle events (create, update, complete, delete) are captured in an immutable audit log within 30 seconds of occurrence.
- **SC-006**: The system operates with 4 distinct services (Chat API, Notification, Recurring Task, Audit) communicating exclusively through the event bus and distributed runtime.
- **SC-007**: No service directly depends on message broker client libraries; all eventing uses the distributed runtime abstraction layer.
- **SC-008**: Event processing is idempotent — replaying the same event does not produce duplicate side effects.
- **SC-009**: The system handles temporary service unavailability gracefully — events are retained and processed when services recover (at-least-once delivery).
- **SC-010**: All features respect user data isolation — users can only see and manage their own tasks, reminders, tags, and audit entries.
