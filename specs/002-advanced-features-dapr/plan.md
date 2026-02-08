# Implementation Plan: Phase V Part A — Advanced Task Features & Event-Driven Architecture

**Branch**: `002-advanced-features-dapr` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-advanced-features-dapr/spec.md`

## Summary

Phase V Part A extends the Todo AI System with advanced task features (priorities, tags, due dates, reminders, recurring tasks), a multi-service event-driven architecture using Dapr as the distributed runtime, and Kafka-compatible eventing via Redpanda. All services are stateless, communicate through Dapr Pub/Sub and Service Invocation, and deploy on Minikube via Helm with Dapr sidecars.

## Technical Context

**Language/Version**: Python 3.11+ (Backend & Services), TypeScript 5.x (Frontend)
**Primary Dependencies**: FastAPI, SQLModel, Dapr Python SDK, dapr-ext-fastapi, python-dateutil
**Storage**: PostgreSQL (Neon Serverless) — primary; Dapr State Store (PostgreSQL-backed) — optional cache
**Eventing**: Redpanda (Kafka-compatible, single-node, in-cluster on Minikube)
**Distributed Runtime**: Dapr 1.14+ (Pub/Sub, State, Jobs, Secrets, Service Invocation)
**Testing**: pytest, httpx (contract + integration tests)
**Target Platform**: Minikube (local Kubernetes) with Dapr sidecars
**Project Type**: Web application (multi-service)
**Performance Goals**: <2s task queries, <60s reminder trigger latency, <30s recurring task creation
**Constraints**: Stateless services, at-least-once event delivery, idempotent consumers
**Scale/Scope**: Single-user local dev, 4 services + Redpanda + Dapr

## Constitution Check

*GATE: Constitution v4.0.0 compliance. Checked 2026-02-08.*

| # | Gate                                           | Status | Notes                                    |
|---|------------------------------------------------|--------|------------------------------------------|
| 1 | All behavior traces to specs + tasks           | PASS   | spec.md → plan.md → tasks.md chain       |
| 2 | AI acts only via MCP tools                     | PASS   | FR-021, Section 8 of user spec           |
| 3 | All side effects via MCP or Dapr               | PASS   | Architecture constraints enforced         |
| 4 | Services are stateless                         | PASS   | FR-024, all state in PostgreSQL/Dapr     |
| 5 | No direct Kafka client libraries               | PASS   | FR-021, Dapr Pub/Sub abstraction only    |
| 6 | Dapr components versioned in repo              | PASS   | dapr/components/ directory planned        |
| 7 | Helm is sole deployment mechanism              | PASS   | All services deployed via Helm charts     |
| 8 | Cluster rebuildable from repo                  | PASS   | quickstart.md documents full rebuild      |
| 9 | Event schemas versioned                        | PASS   | event-contracts.md with v1.0 schemas     |
| 10| Consumers are idempotent                       | PASS   | ProcessedEvent table, R-010              |
| 11| Secrets externalized                           | PASS   | Dapr Secrets + K8s Secrets               |
| 12| User data isolation enforced                   | PASS   | JWT + user_id matching on all endpoints  |
| 13| Phase II/III/IV artifacts immutable             | PASS   | Existing Task fields unchanged; additive only |

**Result**: All gates PASS. No violations. No complexity tracking needed.

## Project Structure

### Documentation (this feature)

```text
specs/002-advanced-features-dapr/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 research decisions
├── data-model.md        # Phase 1 data model
├── quickstart.md        # Phase 1 deployment guide
├── checklists/
│   └── requirements.md  # Spec quality checklist
├── contracts/
│   ├── api-contracts.md    # REST API contracts
│   ├── event-contracts.md  # Pub/Sub event schemas
│   └── dapr-components.md  # Dapr component configurations
└── tasks.md             # Phase 2 output (/sp.tasks)
```

### Source Code (repository root)

```text
backend/                          # Chat API + MCP (existing, extended)
├── app/
│   ├── main.py                   # FastAPI entry (add Dapr subscription routes)
│   ├── config.py                 # Settings (add Dapr config)
│   ├── database.py               # DB engine (unchanged)
│   ├── models/
│   │   ├── task.py               # Task model (extend with new fields)
│   │   └── reminder.py           # NEW: Reminder model
│   ├── routers/
│   │   ├── tasks.py              # Task routes (extend with filter/sort/search)
│   │   ├── reminders.py          # NEW: Reminder CRUD routes
│   │   ├── audit.py              # NEW: Audit query routes (proxy or direct)
│   │   └── internal.py           # NEW: Dapr job callbacks
│   ├── middleware/
│   │   └── auth.py               # JWT verification (unchanged)
│   ├── services/
│   │   └── event_publisher.py    # NEW: Dapr Pub/Sub publishing helper
│   ├── schemas/
│   │   ├── task.py               # NEW: Pydantic schemas for extended task
│   │   ├── reminder.py           # NEW: Pydantic schemas for reminders
│   │   └── events.py             # NEW: Event payload schemas
│   └── mcp/
│       ├── server.py             # MCP server (extend tool definitions)
│       └── task_tools.py         # MCP tools (extend for new features)
├── Dockerfile                    # (unchanged)
└── requirements.txt              # (add dapr, dapr-ext-fastapi, python-dateutil)

services/                         # NEW: Microservices directory
├── notification/
│   ├── app/
│   │   ├── main.py               # FastAPI + Dapr subscription
│   │   ├── config.py             # Service config
│   │   └── handlers/
│   │       └── reminder_handler.py  # Reminder event processor
│   ├── Dockerfile
│   └── requirements.txt
├── recurring/
│   ├── app/
│   │   ├── main.py               # FastAPI + Dapr subscription
│   │   ├── config.py             # Service config
│   │   └── handlers/
│   │       └── recurrence_handler.py  # Recurring task processor
│   ├── Dockerfile
│   └── requirements.txt
└── audit/
    ├── app/
    │   ├── main.py               # FastAPI + Dapr subscription
    │   ├── config.py             # Service config
    │   ├── models/
    │   │   ├── audit_entry.py    # AuditEntry model
    │   │   └── processed_event.py # Idempotency tracking
    │   ├── database.py           # DB session for audit tables
    │   └── handlers/
    │       └── audit_handler.py  # Task event processor
    ├── Dockerfile
    └── requirements.txt

dapr/                             # NEW: Dapr component definitions
└── components/
    ├── pubsub.yaml               # Kafka Pub/Sub (Redpanda)
    ├── statestore.yaml           # PostgreSQL state store
    └── secrets.yaml              # Kubernetes secrets reference

charts/                           # Helm charts (existing + new)
├── todo-backend/                 # (update: add Dapr annotations)
├── todo-frontend/                # (unchanged)
├── notification-service/         # NEW
├── recurring-service/            # NEW
└── audit-service/                # NEW

frontend/                         # (existing, minimal changes)
├── lib/
│   ├── types.ts                  # Extend Task type with new fields
│   └── api-client.ts            # Add reminder endpoints, query params
└── components/
    └── TaskItem.tsx              # Show priority, tags, due date
```

**Structure Decision**: Multi-service web application with shared Dapr infrastructure. Existing `backend/` is extended (not replaced). New services live in `services/` to maintain separation. Each service has its own Dockerfile and Helm chart.

## Complexity Tracking

No constitution violations. No complexity justification needed.

---

## Architecture Design

### Service Topology

```
                    ┌─────────────────────────┐
                    │       Frontend           │
                    │    (Next.js / ChatKit)   │
                    └───────────┬─────────────┘
                                │ HTTP
                    ┌───────────▼─────────────┐
                    │   Backend (Chat API)     │
                    │   + MCP Server           │
                    │   + Dapr Sidecar         │
                    └──┬────────┬────────┬────┘
                       │        │        │
            Dapr Pub/Sub│  Dapr Jobs│  Dapr Pub/Sub│
                       │        │        │
          ┌────────────▼──┐  ┌──▼────┐  ┌▼───────────────┐
          │  task-events   │  │ Jobs  │  │   reminders     │
          │  (Redpanda)    │  │ (Dapr)│  │  (Redpanda)     │
          └──┬─────────┬──┘  └──┬────┘  └──┬──────────────┘
             │         │        │           │
    ┌────────▼──┐  ┌───▼────┐   │    ┌──────▼───────────┐
    │ Recurring  │  │ Audit  │   │    │  Notification    │
    │ Task Svc   │  │ Svc    │   │    │  Service         │
    │ +Dapr      │  │ +Dapr  │   │    │  +Dapr           │
    └────────────┘  └────────┘   │    └──────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │    Backend callback       │
                    │  (reminder-trigger)       │
                    └──────────────────────────┘
```

### Event Flow: Task CRUD

1. User creates/updates/completes/deletes task via API or MCP tool
2. Backend persists change in PostgreSQL
3. Backend publishes `TaskEvent` to `task-events` topic via Dapr Pub/Sub
4. Backend publishes `TaskUpdateEvent` to `task-updates` topic via Dapr Pub/Sub
5. Recurring Task Service receives `task-events` (filters for `completed` + `is_recurring`)
6. Audit Service receives `task-events` (processes all types)

### Event Flow: Reminders

1. User creates reminder via API
2. Backend persists reminder in PostgreSQL
3. Backend schedules Dapr Job at `remind_at` time
4. At `remind_at`, Dapr calls backend's `/internal/jobs/reminder-trigger`
5. Backend looks up reminder + task, publishes `ReminderEvent` to `reminders` topic
6. Notification Service receives event, processes/logs notification

### Event Flow: Recurring Tasks

1. User completes a recurring task
2. Backend publishes `TaskEvent(completed)` with `is_recurring=true`
3. Recurring Task Service receives event
4. Service computes next due date from `recurrence_rule`
5. Service calls Backend `POST /api/{user_id}/tasks` via Dapr Service Invocation
6. Backend creates new task → publishes `TaskEvent(created)` for the new occurrence

### Data Flow: Search, Filter, Sort

1. User calls `GET /api/{user_id}/tasks` with query parameters
2. Backend builds SQLAlchemy query with:
   - `WHERE user_id = :user_id` (always)
   - `WHERE priority = :priority` (if filter)
   - `WHERE tags @> ARRAY[:tags]` (if tag filter, uses GIN index)
   - `WHERE completed = :status` (if status filter)
   - `WHERE due_at BETWEEN :after AND :before` (if date range)
   - `WHERE title ILIKE :search OR description ILIKE :search` (if search)
   - `ORDER BY :sort_by :sort_order`
3. Results returned as JSON array

---

## Dapr Integration Details

### Building Blocks Used

| Building Block     | Usage                                    | Component       |
|--------------------|------------------------------------------|-----------------|
| Pub/Sub            | Event publishing and subscription        | pubsub.kafka    |
| Jobs               | Scheduling reminders                     | (built-in)      |
| State Management   | Optional conversation state cache        | state.postgresql |
| Service Invocation | Recurring Service → Backend task creation| (built-in)      |
| Secrets            | Database credentials, API keys           | secretstores.kubernetes |

### Dapr HTTP API Endpoints (Sidecar at localhost:3500)

| Operation          | Method | URL                                           |
|--------------------|--------|-----------------------------------------------|
| Publish event      | POST   | `/v1.0/publish/pubsub/{topic}`                |
| Schedule job       | POST   | `/v1.0-alpha1/jobs/{name}`                    |
| Delete job         | DELETE | `/v1.0-alpha1/jobs/{name}`                    |
| Get state          | GET    | `/v1.0/state/statestore/{key}`                |
| Save state         | POST   | `/v1.0/state/statestore`                      |
| Invoke service     | POST   | `/v1.0/invoke/{app-id}/method/{method}`       |
| Get secret         | GET    | `/v1.0/secrets/kubernetes-secrets/{name}`      |

---

## MCP Tool Updates

### Extended Tools

| Tool          | Changes                                                    |
|---------------|------------------------------------------------------------|
| `add_task`    | Accept priority, tags, due_at, is_recurring, recurrence_rule |
| `list_tasks`  | Accept filter, sort, search parameters                     |
| `update_task` | Accept priority, tags, due_at, is_recurring, recurrence_rule |

### New Tools

| Tool              | Description                                    |
|-------------------|------------------------------------------------|
| `set_reminder`    | Create a reminder for a task at a specific time |
| `list_reminders`  | List reminders for a task                       |
| `delete_reminder` | Delete a specific reminder                      |
| `search_tasks`    | Search tasks by keyword                         |

---

## Deployment Topology (Minikube)

| Pod                    | Containers      | Dapr App ID             | Port |
|------------------------|-----------------|-------------------------|------|
| todo-backend           | app + dapr      | `todo-backend`          | 8000 |
| todo-frontend          | app             | (no Dapr needed)        | 3000 |
| notification-service   | app + dapr      | `notification-service`  | 8001 |
| recurring-service      | app + dapr      | `recurring-service`     | 8002 |
| audit-service          | app + dapr      | `audit-service`         | 8003 |
| redpanda-0             | redpanda        | (infrastructure)        | 9092 |

---

## Validation Strategy

Phase V Part A is considered complete when all of the following are true:

1. **Intermediate features**: Priority, tags, search, filter, sort work via API
2. **Due dates**: Create, update, remove, filter, sort by due_at
3. **Reminders**: Schedule via Dapr Jobs, trigger publishes event, Notification Service consumes
4. **Recurring tasks**: Completion publishes event, Recurring Service creates next occurrence
5. **Audit**: All task lifecycle events recorded by Audit Service
6. **No Kafka client libraries**: All eventing via Dapr Pub/Sub
7. **No polling**: Reminders use Dapr Jobs, not cron
8. **Idempotent consumers**: Duplicate events don't produce duplicate effects
9. **Helm deployment**: All services deploy via Helm on Minikube with Dapr sidecars
10. **Reproducible**: `minikube delete && minikube start` + quickstart.md rebuilds everything

---

## Generated Artifacts

| Artifact                        | Path                                              | Phase |
|---------------------------------|---------------------------------------------------|-------|
| Research decisions              | `specs/002-advanced-features-dapr/research.md`    | 0     |
| Data model                      | `specs/002-advanced-features-dapr/data-model.md`  | 1     |
| API contracts                   | `specs/002-advanced-features-dapr/contracts/api-contracts.md` | 1 |
| Event contracts                 | `specs/002-advanced-features-dapr/contracts/event-contracts.md` | 1 |
| Dapr component contracts        | `specs/002-advanced-features-dapr/contracts/dapr-components.md` | 1 |
| Quickstart guide                | `specs/002-advanced-features-dapr/quickstart.md`  | 1     |
| Tasks (next step)               | `specs/002-advanced-features-dapr/tasks.md`       | 2     |
