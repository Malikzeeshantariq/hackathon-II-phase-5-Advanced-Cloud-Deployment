# Research: Phase V Part A — Advanced Task Features & Event-Driven Architecture

**Branch**: `002-advanced-features-dapr` | **Date**: 2026-02-08 | **Phase**: 0

## Technical Context Resolution

All NEEDS CLARIFICATION items resolved below.

---

### R-001: Dapr Python SDK for FastAPI Integration

**Decision**: Use `dapr` Python SDK (official) with `dapr-ext-fastapi` extension for Pub/Sub subscription endpoints, and raw HTTP calls to Dapr sidecar for publishing, state, jobs, and service invocation.

**Rationale**: The `dapr-ext-fastapi` extension provides native decorator-based topic subscription (`@app.subscribe`) that integrates cleanly with FastAPI. For publishing and other building blocks, the Dapr HTTP API via the sidecar (localhost:3500) is simpler and avoids gRPC complexity. This aligns with constitution rule: "Services MUST NOT embed vendor-specific SDK logic when Dapr abstractions exist."

**Alternatives Considered**:
- gRPC-based Dapr SDK: Higher complexity, requires proto generation. Rejected for Part A simplicity.
- Raw HTTP only (no SDK): Viable but loses subscription decorator convenience. Rejected.

---

### R-002: Kafka-Compatible Backend for Dapr Pub/Sub (Local Dev)

**Decision**: Use Redpanda (single-node, in-cluster) as the Kafka-compatible backend for local Minikube deployment.

**Rationale**: Redpanda is Kafka API-compatible, requires no JVM, runs as a single binary, and has minimal resource footprint — ideal for Minikube on developer machines. Dapr's `pubsub.kafka` component works unmodified with Redpanda. Strimzi Kafka requires JVM and significantly more memory.

**Alternatives Considered**:
- Apache Kafka via Strimzi: Too resource-heavy for local Minikube (requires JVM + ZooKeeper or KRaft). Rejected for Part A.
- Confluent Cloud: Requires external account. Out of scope for Part A (local only).
- Dapr in-memory Pub/Sub: Not Kafka-compatible, no persistence, not suitable for at-least-once delivery. Rejected.

---

### R-003: Dapr Jobs API for Reminder Scheduling

**Decision**: Use Dapr Jobs API (HTTP) to schedule one-shot jobs at `remind_at` time. When the job fires, Dapr calls a registered endpoint on the backend service, which then publishes a reminder event to the `reminders` topic.

**Rationale**: Dapr Jobs API provides non-polling, time-based job scheduling. This satisfies FR-009 (no polling) and aligns with constitution Dapr governance rules. The backend acts as the job handler, keeping the reminder-to-event flow traceable.

**Alternatives Considered**:
- Cron-based polling: Explicitly prohibited by spec (FR-009). Rejected.
- APScheduler (in-process): Stateful, violates stateless service principle. Rejected.
- Kubernetes CronJobs: Too coarse-grained (minute resolution), creates pod overhead per reminder. Rejected.

---

### R-004: Tags Storage Strategy in PostgreSQL

**Decision**: Store tags as a PostgreSQL `ARRAY(String)` column on the Task table via SQLModel/SQLAlchemy `Column(ARRAY(String))`.

**Rationale**: PostgreSQL native arrays support GIN indexing for efficient `@>` (contains) queries, avoid JOIN overhead of a separate tags table, and map directly to Python `list[str]`. This satisfies FR-002 (zero or more tags) and FR-007 (filter by tags) with minimal schema complexity. Tags are free-form strings per spec assumptions.

**Alternatives Considered**:
- Separate `Tag` table with M:N join: Over-engineered for free-form strings without taxonomy. Rejected for Part A.
- JSONB column: Less queryable than native arrays for simple string lists. Rejected.
- Comma-separated string: Not queryable, no type safety. Rejected.

---

### R-005: Priority Storage Strategy

**Decision**: Store priority as a PostgreSQL `VARCHAR` column with application-level validation against the enum set `{low, medium, high, critical}`. Define a Python `Enum` for type safety.

**Rationale**: Using a string column with Python enum validation keeps the database portable and avoids PostgreSQL-specific enum type DDL complexity. The four-value set is small and fixed per spec. Application-level validation (Pydantic/SQLModel) catches invalid values before persistence.

**Alternatives Considered**:
- PostgreSQL native ENUM type: Requires DDL migration to add values. Rejected for flexibility.
- Integer mapping (1-4): Less readable in queries and logs. Rejected.

---

### R-006: Recurrence Rule Representation

**Decision**: Store recurrence as two fields: `is_recurring: bool` and `recurrence_rule: Optional[str]` with values `daily`, `weekly`, or `monthly`. The Recurring Task Service computes the next due date using Python `datetime` + `dateutil.relativedelta`.

**Rationale**: Three fixed intervals per spec assumptions. A simple string field is sufficient. `dateutil.relativedelta` handles month-end edge cases (e.g., Jan 31 → Feb 28) correctly. No need for RRULE parser complexity.

**Alternatives Considered**:
- iCalendar RRULE format: Over-engineered for 3 fixed intervals. Rejected for Part A.
- Cron expression: Not needed for simple intervals. Rejected.
- Integer (days between occurrences): Doesn't handle monthly correctly. Rejected.

---

### R-007: Multi-Service Project Structure

**Decision**: Create new service directories at the repository root alongside existing `backend/` and `frontend/`:
- `services/notification/` — Notification Service
- `services/recurring/` — Recurring Task Service
- `services/audit/` — Audit Service

Each service is a standalone FastAPI application with its own `Dockerfile`, `requirements.txt`, and Helm chart under `charts/`.

**Rationale**: Keeps the existing `backend/` (Chat API + MCP) unchanged as the primary service. New services are lightweight FastAPI apps that subscribe to Dapr Pub/Sub topics. Separate directories enable independent containerization and deployment per constitution requirement.

**Alternatives Considered**:
- Monorepo with shared packages: Adds build complexity. Rejected for Part A.
- All services in `backend/`: Conflates concerns, violates multi-service architecture (FR-023). Rejected.

---

### R-008: Dapr Component Configuration for Minikube

**Decision**: Store Dapr component YAML files in `dapr/components/` at the repository root. Components include:
- `pubsub.yaml` — Kafka Pub/Sub (Redpanda)
- `statestore.yaml` — PostgreSQL state store
- `secrets.yaml` — Kubernetes secrets reference

Apply via Helm chart or `dapr components` CLI during deployment.

**Rationale**: Constitution requires "Dapr component definitions MUST be versioned and stored in the repository" and "Dapr sidecar injection MUST be configured via Helm chart annotations." Storing in `dapr/components/` with Helm-based application ensures reproducibility.

**Alternatives Considered**:
- Inline in Helm values: Less readable, harder to test independently. Rejected.
- Dapr CLI only: Not Helm-managed, breaks deployment reproducibility. Rejected.

---

### R-009: Audit Entry Storage

**Decision**: Store audit entries in a dedicated `audit_entries` table in the same Neon PostgreSQL database. The Audit Service writes directly to this table (it is the data owner).

**Rationale**: The audit service is the sole writer to this table (append-only per spec). Using the same PostgreSQL instance avoids additional infrastructure for Part A. The service still communicates via Dapr Pub/Sub for event consumption and uses its own database session (not shared with backend).

**Alternatives Considered**:
- Separate database: Unnecessary overhead for Part A. Can migrate later.
- Dapr state store only: Not queryable enough for audit log retrieval. Rejected.
- File-based logging: Not queryable, not user-scoped. Rejected.

---

### R-010: Event Idempotency Strategy

**Decision**: Each event includes a unique `event_id` (UUID). Consumers maintain a processed event log (simple table or set). Before processing, consumers check if the `event_id` has been seen. If yes, skip. If no, process and record.

**Rationale**: Dapr Pub/Sub provides at-least-once delivery (FR-020). Consumers MUST be idempotent (FR-020, SC-008). A processed-events table is the simplest reliable approach.

**Alternatives Considered**:
- Database unique constraints on business keys: Works for creates, harder for updates. Supplement with event log.
- Redis-based dedup: Adds infrastructure. Rejected for Part A.
