# Tasks: Phase V Part A — Advanced Task Features & Event-Driven Architecture

**Input**: Design documents from `/specs/002-advanced-features-dapr/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/
**Branch**: `002-advanced-features-dapr` | **Date**: 2026-02-08

## Task Governance

- Every task MUST trace to a spec requirement (FR-xxx) or success criterion (SC-xxx)
- Tasks MUST be executed in dependency order within each phase
- Tasks marked [P] can run in parallel (different files, no dependencies)
- Each user story MUST be independently testable at its checkpoint
- No task may introduce a direct Kafka client library (FR-021, Constitution v4.0.0)
- All event publishing MUST go through Dapr sidecar HTTP API (Constitution Gate 5)

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Task Index

| ID    | Story | Phase | Description                                                | Files                                              |
|-------|-------|-------|------------------------------------------------------------|----------------------------------------------------|
| T001  | —     | 1     | Add Python dependencies for Dapr and date utilities        | `backend/requirements.txt`                         |
| T002  | —     | 1     | Create service project scaffolds                           | `services/notification/`, `services/recurring/`, `services/audit/` |
| T003  | —     | 1     | Create Dapr component YAML files                           | `dapr/components/`                                 |
| T004  | —     | 2     | Extend Task model with new fields                          | `backend/app/models/task.py`                       |
| T005  | —     | 2     | Create Reminder model                                      | `backend/app/models/reminder.py`                   |
| T006  | —     | 2     | Create AuditEntry and ProcessedEvent models                | `services/audit/app/models/`                       |
| T007  | —     | 2     | Create Pydantic schemas for extended task and events       | `backend/app/schemas/`                             |
| T008  | —     | 2     | Create event publisher helper (Dapr Pub/Sub)               | `backend/app/services/event_publisher.py`          |
| T009  | —     | 2     | Run database migration for new columns and tables          | Neon PostgreSQL                                    |
| T010  | US1   | 3     | Extend task CRUD routes with priority, tags fields         | `backend/app/routers/tasks.py`                     |
| T011  | US1   | 3     | Implement filter, sort, search query parameters            | `backend/app/routers/tasks.py`                     |
| T012  | US1   | 3     | Publish TaskEvent on all task CRUD operations              | `backend/app/routers/tasks.py`, `backend/app/services/event_publisher.py` |
| T013  | US2   | 4     | Implement due date create, update, remove in task routes   | `backend/app/routers/tasks.py`                     |
| T014  | US2   | 4     | Implement due date filtering and sorting                   | `backend/app/routers/tasks.py`                     |
| T015  | US3   | 5     | Create reminder CRUD routes                                | `backend/app/routers/reminders.py`                 |
| T016  | US3   | 5     | Implement Dapr Jobs scheduling for reminders               | `backend/app/services/event_publisher.py`, `backend/app/routers/reminders.py` |
| T017  | US3   | 5     | Create reminder trigger callback endpoint                  | `backend/app/routers/internal.py`                  |
| T018  | US3   | 5     | Implement Notification Service                             | `services/notification/`                           |
| T019  | US4   | 6     | Implement Recurring Task Service                           | `services/recurring/`                              |
| T020  | US4   | 6     | Validate recurring task next-due-date calculation          | `services/recurring/app/handlers/recurrence_handler.py` |
| T021  | US5   | 7     | Implement Audit Service                                    | `services/audit/`                                  |
| T022  | US5   | 7     | Create audit query route (proxy or direct)                 | `backend/app/routers/audit.py`                     |
| T023  | —     | 8     | Extend MCP tools for new task features                     | `backend/app/mcp/task_tools.py`                    |
| T024  | —     | 8     | Add new MCP tools (reminders, search)                      | `backend/app/mcp/task_tools.py`, `backend/app/mcp/server.py` |
| T025  | —     | 8     | Create Helm charts for new services                        | `charts/notification-service/`, `charts/recurring-service/`, `charts/audit-service/` |
| T026  | —     | 8     | Update backend Helm chart with Dapr annotations            | `charts/todo-backend/`                             |
| T027  | —     | 8     | End-to-end validation per quickstart.md                    | All services                                       |

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Add dependencies, scaffold new services, create Dapr component configs

- [x] T001 Add Python dependencies for Dapr and date utilities in `backend/requirements.txt` — add `dapr>=1.14.0`, `dapr-ext-fastapi>=1.14.0`, `python-dateutil>=2.9.0` (R-001, R-006)
- [x] T002 [P] Create service project scaffolds for Notification, Recurring Task, and Audit services under `services/notification/`, `services/recurring/`, `services/audit/` — each with `app/main.py`, `app/config.py`, `Dockerfile`, `requirements.txt` per plan.md structure (FR-023)
- [x] T003 [P] Create Dapr component YAML files in `dapr/components/` — `pubsub.yaml` (pubsub.kafka pointing to Redpanda), `statestore.yaml` (state.postgresql with secretKeyRef), `secrets.yaml` (secretstores.kubernetes) per dapr-components.md contracts (R-002, FR-021, Constitution Gate 6)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core schema extensions, models, event infrastructure that MUST be complete before ANY user story

**CRITICAL**: No user story work can begin until this phase is complete

- [x] T004 Extend Task SQLModel in `backend/app/models/task.py` — add `priority: Optional[str]` (String(10), nullable), `tags: List[str]` (ARRAY(String), default=[]), `due_at: Optional[datetime]` (nullable), `is_recurring: bool` (default=false), `recurrence_rule: Optional[str]` (String(20), nullable). Preserve all existing 7 fields immutable. Add validation: priority in {low,medium,high,critical,null}, is_recurring=true requires recurrence_rule non-null, recurrence_rule requires is_recurring=true (FR-001, FR-002, FR-003, FR-004, data-model.md Section 1)
- [x] T005 [P] Create Reminder SQLModel in `backend/app/models/reminder.py` — fields: `id` (UUID PK), `task_id` (UUID FK→task.id ON DELETE CASCADE), `user_id` (String NOT NULL), `remind_at` (DateTime NOT NULL), `created_at` (DateTime auto). Add indexes: `idx_reminder_task_id`, `idx_reminder_user_id`, `idx_reminder_remind_at` (FR-005, data-model.md Section 2)
- [x] T006 [P] Create AuditEntry SQLModel in `services/audit/app/models/audit_entry.py` — fields: `id` (UUID PK), `event_type` (String(20) NOT NULL), `task_id` (UUID NOT NULL, NOT FK), `user_id` (String NOT NULL), `event_data` (JSON NOT NULL), `timestamp` (DateTime NOT NULL). Create ProcessedEvent SQLModel in `services/audit/app/models/processed_event.py` — fields: `event_id` (UUID PK), `service_name` (String(50) NOT NULL), `processed_at` (DateTime auto). Add indexes per data-model.md Sections 3-4 (FR-020, FR-022, R-010)
- [x] T007 [P] Create Pydantic schemas in `backend/app/schemas/` — `task.py` (TaskCreate, TaskUpdate, TaskResponse with new fields), `reminder.py` (ReminderCreate, ReminderResponse), `events.py` (TaskEventPayload, ReminderEventPayload, TaskUpdateEventPayload matching CloudEvents 1.0 data field per event-contracts.md) (api-contracts.md, event-contracts.md)
- [x] T008 Create event publisher helper in `backend/app/services/event_publisher.py` — implement `publish_task_event(event_type, task, user_id)` and `publish_task_update_event(change_type, task_id, user_id)` using httpx POST to Dapr sidecar `http://localhost:3500/v1.0/publish/pubsub/{topic}` with CloudEvents 1.0 envelope. NO direct Kafka client imports (FR-018, FR-021, event-contracts.md, Constitution Gate 5)
- [x] T009 Run database migration for new columns and tables on Neon PostgreSQL — ALTER TABLE task ADD COLUMN priority, tags, due_at, is_recurring, recurrence_rule; CREATE TABLE reminder; CREATE TABLE audit_entry; CREATE TABLE processed_event; CREATE indexes per data-model.md (data-model.md Sections 1-4)

**Checkpoint**: Foundation ready — all models, schemas, event infrastructure, and database changes in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Organize Tasks with Priorities, Tags, and Sorting (Priority: P1)

**Goal**: Users can assign priorities and tags to tasks, then filter, sort, and search their task list
**Traces to**: FR-001, FR-002, FR-006, FR-007, FR-008, SC-001
**Independent Test**: Create tasks with priorities/tags, then verify filter/sort/search returns correct results

### Implementation for User Story 1

- [x] T010 [US1] Extend task CRUD routes in `backend/app/routers/tasks.py` — accept `priority`, `tags` fields in create/update request bodies. Validate priority in {low, medium, high, critical, null}. Validate tags as array of non-empty strings, deduplicate on write. Return new fields in all task responses (FR-001, FR-002, api-contracts.md 1.1, 1.3)
- [x] T011 [US1] Implement filter, sort, and search query parameters in `backend/app/routers/tasks.py` GET list endpoint — add query params: `priority` (filter), `tags` (comma-separated AND filter using `@>` operator), `status` (completed/pending/all), `search` (ILIKE on title, description), `sort_by` (created_at/due_at/priority/title), `sort_order` (asc/desc). Priority sort order: critical>high>medium>low>null. Tasks without due_at sort to end when sorting by due_at (FR-006, FR-007, FR-008, SC-001, api-contracts.md 1.2)
- [x] T012 [US1] Wire event publishing into all task CRUD operations in `backend/app/routers/tasks.py` — after each create/update/complete/delete, call `publish_task_event()` and `publish_task_update_event()` from `event_publisher.py`. Events are fire-and-forget (log errors, don't fail the request). Publishes to `task-events` and `task-updates` topics (FR-018, FR-014, event-contracts.md)

**Checkpoint**: Users can create tasks with priorities and tags, filter by priority/tags/status, sort by multiple fields, and search by keyword. All task mutations publish events to Dapr Pub/Sub. Verify SC-001: <2s query performance.

---

## Phase 4: User Story 2 — Set Due Dates on Tasks (Priority: P2)

**Goal**: Users can assign, update, and remove due dates on tasks, and filter/sort by date range
**Traces to**: FR-003, SC-002
**Independent Test**: Create tasks with due dates, update/remove dates, filter by date range, sort by due_at

### Implementation for User Story 2

- [x] T013 [US2] Implement due date handling in task create/update routes in `backend/app/routers/tasks.py` — accept `due_at` (ISO8601 datetime or null) in create/update. Validate as UTC timestamp. Setting to null removes due date. Return `due_at` in all task responses (FR-003, api-contracts.md 1.1, 1.3)
- [x] T014 [US2] Implement due date filtering and sorting in `backend/app/routers/tasks.py` GET list endpoint — add `due_before` and `due_after` query params for date range filtering (`WHERE due_at BETWEEN`). When sorting by `due_at`, tasks without due dates sort to end (NULLS LAST). Combine with existing priority/tags/status filters (FR-007, FR-008, SC-002, api-contracts.md 1.2)

**Checkpoint**: Users can set, update, and remove due dates. Date range filtering works. Due date sorting places null-due-date tasks at end. All due date changes publish events.

---

## Phase 5: User Story 3 — Receive Reminders for Upcoming Tasks (Priority: P3)

**Goal**: Users can schedule reminders that trigger automatically via Dapr Jobs, producing notification events
**Traces to**: FR-005, FR-009, FR-010, FR-011, FR-012, FR-013, SC-003
**Independent Test**: Create reminder, verify Dapr Job scheduled, wait for trigger, verify event published, verify Notification Service receives it

### Implementation for User Story 3

- [x] T015 [US3] Create reminder CRUD routes in `backend/app/routers/reminders.py` — POST `/api/{user_id}/tasks/{task_id}/reminders` (create, validate remind_at in future, validate task ownership), GET `/api/{user_id}/tasks/{task_id}/reminders` (list), DELETE `/api/{user_id}/tasks/{task_id}/reminders/{reminder_id}` (delete). Register router in `backend/app/main.py` (FR-005, FR-013, api-contracts.md Section 2)
- [x] T016 [US3] Implement Dapr Jobs scheduling in `backend/app/services/event_publisher.py` and wire into `backend/app/routers/reminders.py` — add `schedule_reminder_job(reminder_id, task_id, user_id, remind_at)` that POSTs to Dapr sidecar `http://localhost:3500/v1.0-alpha1/jobs/{name}` with reminder data and schedule time. Add `cancel_reminder_job(reminder_id)` that DELETEs the job. Call schedule on reminder create, cancel on reminder delete. Also cancel all reminder jobs when a task is deleted (FR-009, FR-012, dapr-components.md Section 4)
- [x] T017 [US3] Create reminder trigger callback endpoint in `backend/app/routers/internal.py` — POST `/internal/jobs/reminder-trigger` called by Dapr when job fires. Look up reminder + task from DB, publish `ReminderEvent` to `reminders` topic via `event_publisher.py`. Register router in `backend/app/main.py` (FR-010, api-contracts.md 4.1, event-contracts.md Section 2)
- [x] T018 [US3] Implement Notification Service in `services/notification/` — FastAPI app with Dapr subscription to `reminders` topic on route `/events/reminders`. Implement `reminder_handler.py` that receives ReminderEvent, checks idempotency via ProcessedEvent table, logs notification details (delivery channel integration deferred per Assumption 1). Add `dapr/subscribe` endpoint or programmatic subscription. Create `services/notification/app/models/processed_event.py` and `services/notification/app/database.py` for idempotency (FR-011, FR-020, SC-003, dapr-components.md Section 5)

**Checkpoint**: Reminders can be scheduled and trigger automatically. Notification Service receives and processes events idempotently. Verify SC-003: reminder fires within 60s, no polling.

---

## Phase 6: User Story 4 — Automatically Recreate Recurring Tasks (Priority: P4)

**Goal**: When a recurring task is completed, the next occurrence is automatically created by the Recurring Task Service
**Traces to**: FR-004, FR-014, FR-015, FR-016, FR-017, SC-004
**Independent Test**: Create recurring task, complete it, verify event published, verify new task created with correct next due date

### Implementation for User Story 4

- [x] T019 [US4] Implement Recurring Task Service in `services/recurring/` — FastAPI app with Dapr subscription to `task-events` topic on route `/events/task-events`. Implement `recurrence_handler.py` that filters for `event_type == "completed"` AND `task_data.is_recurring == true`. Compute next due date using `python-dateutil.relativedelta` per recurrence_rule (daily=+1 day, weekly=+7 days, monthly=+1 month). Create new task via Dapr Service Invocation POST to `todo-backend` app-id at `/api/{user_id}/tasks`. Include idempotency check via ProcessedEvent table. Create `services/recurring/app/models/processed_event.py` and `services/recurring/app/database.py` (FR-015, FR-016, R-006, SC-004, dapr-components.md Section 5)
- [x] T020 [US4] Validate recurring task next-due-date edge cases in `services/recurring/app/handlers/recurrence_handler.py` — handle month-end clamping (Jan 31 → Feb 28/29), missing due_at (use current date as base), recurrence_rule removed (skip processing). Verify FR-016 month-end edge case from spec: "Jan 31 monthly → Feb 28 (or 29 in leap year)" (FR-016, FR-017)

**Checkpoint**: Recurring tasks auto-create next occurrence on completion. Verify SC-004: new task created within 30s with correct next due date.

---

## Phase 7: User Story 5 — Track Task Activity via Audit Log (Priority: P5)

**Goal**: All task lifecycle events are recorded in an immutable, user-scoped audit log by the Audit Service
**Traces to**: FR-022, SC-005
**Independent Test**: Perform task CRUD, verify corresponding audit entries recorded, query audit log per user

### Implementation for User Story 5

- [x] T021 [US5] Implement Audit Service in `services/audit/` — FastAPI app with Dapr subscription to `task-events` topic on route `/events/task-events`. Implement `audit_handler.py` that processes ALL event types (created, updated, completed, deleted), creates AuditEntry records with full event_data snapshot. Include idempotency check via ProcessedEvent table. Wire up `services/audit/app/database.py` to Neon PostgreSQL. Append-only: no UPDATE or DELETE on audit_entry table (FR-022, FR-020, SC-005, data-model.md Section 3)
- [x] T022 [US5] Create audit query route in `backend/app/routers/audit.py` — GET `/api/{user_id}/audit` with query params: `task_id` (filter), `event_type` (filter), `limit` (default 50, max 200), `offset` (default 0). Query audit_entry table filtered by `user_id` (user isolation). Register router in `backend/app/main.py`. Alternatively, proxy to Audit Service via Dapr Service Invocation (FR-022, SC-010, api-contracts.md Section 3)

**Checkpoint**: All task lifecycle events produce audit entries. Audit log is user-scoped, immutable, and queryable. Verify SC-005: entries recorded within 30s.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: MCP tool updates, Helm charts, deployment validation

- [x] T023 [P] Extend existing MCP tools in `backend/app/mcp/task_tools.py` — update `add_task` to accept priority, tags, due_at, is_recurring, recurrence_rule. Update `list_tasks` to accept filter, sort, search params. Update `update_task` to accept new fields (plan.md MCP Tool Updates — Extended Tools)
- [x] T024 [P] Add new MCP tools in `backend/app/mcp/task_tools.py` and register in `backend/app/mcp/server.py` — `set_reminder` (create reminder for task), `list_reminders` (list reminders for task), `delete_reminder` (delete specific reminder), `search_tasks` (search by keyword). Follow existing tool pattern with user_id scoping (plan.md MCP Tool Updates — New Tools)
- [x] T025 [P] Create Helm charts for new services — `charts/notification-service/`, `charts/recurring-service/`, `charts/audit-service/`. Each chart includes: Deployment (with Dapr annotations: `dapr.io/enabled: "true"`, `dapr.io/app-id`, `dapr.io/app-port`, `dapr.io/enable-api-logging: "true"`), Service, ConfigMap. Use same Helm chart structure as existing `charts/todo-backend/` (FR-023, dapr-components.md Section 4, Constitution Gate 7)
- [x] T026 [P] Update backend Helm chart in `charts/todo-backend/` — add Dapr sidecar annotations to deployment template: `dapr.io/enabled: "true"`, `dapr.io/app-id: "todo-backend"`, `dapr.io/app-port: "8000"`, `dapr.io/enable-api-logging: "true"` (dapr-components.md Section 4)
- [x] T027 End-to-end validation per `specs/002-advanced-features-dapr/quickstart.md` — verify full deployment cycle: Dapr init, Redpanda deploy, Dapr components apply, all service images build, Helm install all charts, all pods running with 2/2 containers (app + Dapr sidecar), test task CRUD with new fields, verify events flow through Redpanda topics, verify reminder triggers, verify recurring task creation, verify audit log entries. Run `rpk topic list` and `rpk topic consume` to validate event flow (quickstart.md Steps 1-8, Validation Strategy points 1-10)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — can start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 (T001) for dependencies — BLOCKS all user stories
- **Phase 3 (US1 — P1)**: Depends on Phase 2 completion
- **Phase 4 (US2 — P2)**: Depends on Phase 2 completion. Can run in parallel with US1 (different query params), but T013/T014 touch same file as T010/T011 so recommend sequential after US1
- **Phase 5 (US3 — P3)**: Depends on Phase 2 completion. New files (reminders.py, internal.py, notification service) — can start after Phase 2
- **Phase 6 (US4 — P4)**: Depends on Phase 2 (event publishing) and Phase 3 (T012 wires event publishing). Recurring Service is new files
- **Phase 7 (US5 — P5)**: Depends on Phase 2 (event publishing) and Phase 3 (T012 wires event publishing). Audit Service is new files
- **Phase 8 (Polish)**: MCP tools (T023/T024) depend on US1-US3. Helm charts (T025/T026) can start after Phase 1. E2E validation (T027) depends on all phases

### Recommended Execution Order (Sequential)

```
Phase 1: T001 → T002, T003 (parallel)
Phase 2: T004 → T005, T006, T007 (parallel) → T008 → T009
Phase 3: T010 → T011 → T012
Phase 4: T013 → T014
Phase 5: T015 → T016 → T017 → T018
Phase 6: T019 → T020
Phase 7: T021 → T022
Phase 8: T023, T024, T025, T026 (parallel) → T027
```

### Parallel Opportunities

- T002 and T003 (different directories)
- T005, T006, T007 (different files, all depend on T004)
- T023, T024, T025, T026 (different files/directories)
- US5 (Phase 7) can run in parallel with US3/US4 (different services, all consume same events)

---

## Exit Criteria

All of the following MUST be true before Phase V Part A is considered complete:

1. Priority, tags, search, filter, sort work via API (SC-001)
2. Due dates create, update, remove, filter, sort work (SC-002)
3. Reminders trigger via Dapr Jobs within 60s, no polling (SC-003)
4. Recurring tasks auto-create next occurrence within 30s (SC-004)
5. Audit log records all lifecycle events within 30s (SC-005)
6. 4 distinct services communicate via Dapr Pub/Sub (SC-006)
7. No Kafka client libraries in any service (SC-007, FR-021)
8. Idempotent consumers — duplicate events produce no duplicate effects (SC-008)
9. At-least-once delivery — events retained during service downtime (SC-009)
10. User data isolation enforced on all endpoints (SC-010)
11. All services deploy via Helm with Dapr sidecars on Minikube (Constitution Gate 7)
12. Cluster rebuildable from repo per quickstart.md (Constitution Gate 8)
