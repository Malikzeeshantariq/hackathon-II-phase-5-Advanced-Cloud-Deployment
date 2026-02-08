<!--
============================================================================
SYNC IMPACT REPORT
============================================================================
Version Change: 3.0.0 → 4.0.0 (MAJOR - Phase V Advanced Cloud & Event-Driven Architecture)

Modified Principles:
- Principle II: "Deterministic Systems via Tools" → "Deterministic Systems via Tools and Runtimes"
  - Extended to include Dapr APIs (Pub/Sub, State, Jobs, Secrets, Service Invocation)
- Principle III: "Stateless Intelligence, Persistent Memory, Reproducible Clusters" →
  "Stateless Services, Persistent State, Reproducible Clusters"
  - Extended to include Dapr state stores and pipeline reproducibility
- Principle IV: "Engineering Rigor (AI + Infrastructure)" →
  "Engineering Rigor (AI + Cloud + Event-Driven Systems)"
  - Extended to include CI/CD, observability, runtime contracts, and pipeline governance

Added Sections:
- Dapr Governance Rules
- Event-Driven (Kafka/Redpanda) Governance Rules
- Infrastructure & Cloud Governance Rules (replaces Infrastructure Governance Rules)
- CI/CD & Observability Rules
- Phase V Technical Constraints (Dapr, Kafka, Cloud K8s, CI/CD, Observability)
- Phase V Success Criteria

Updated Sections:
- Technical Constraints: added Dapr, Kafka/Redpanda, Cloud K8s (Oracle OKE primary),
  CI/CD (GitHub Actions), Observability
- Architecture Constraints: added multi-service topology, Dapr service invocation,
  Dapr Pub/Sub over Kafka-compatible backends
- Quality & Validation Rules: added cloud reproducibility, pipeline validation
- Enforcement: expanded to cloud, CI/CD, event-driven services, and Dapr
- Success Criteria: Phase III/IV marked complete; Phase V criteria added
- Failure Conditions: added Dapr bypass, vendor SDK misuse, event schema violations
- Governance: versioning policy expanded for Dapr, eventing, cloud, infrastructure

Removed Sections:
- None

Templates Requiring Updates:
- .specify/templates/spec-template.md: ⚠ ADD Dapr + Event-Driven requirements checks
- .specify/templates/plan-template.md: ⚠ ADD Cloud + CI/CD + Observability architecture checks
- .specify/templates/tasks-template.md: ⚠ ADD multi-service + pipeline task traceability

Follow-up TODOs:
- Create sp5.spec.md (Phase V advanced features & cloud spec)
- Create sp5.plan.md (Phase V multi-service & cloud architecture plan)
- Create sp5.tasks.md (Phase V execution & delivery tasks)
============================================================================
-->

# Todo App (Phase V) Constitution

Spec-Driven, AI-Native, Cloud-Native, Event-Driven Software Development

---

## Project

**Todo AI System — Phase V (Advanced Cloud & Event-Driven Architecture)**

This constitution defines the non-negotiable principles, standards, constraints,
and success criteria governing Phase V of the Todo AI System.

Phase V extends Phase IV by adding:

- Event-driven architecture using Kafka-compatible systems (Kafka / Redpanda)
- Distributed application runtime via Dapr:
  - Pub/Sub
  - State Management
  - Jobs (Scheduler)
  - Secrets
  - Service Invocation
- Multi-service architecture:
  - Chat API + MCP
  - Notification Service
  - Recurring Task Service
  - Audit/Activity Service
  - Realtime/WebSocket Service
- Cloud Kubernetes deployments:
  - Oracle OKE (primary cloud target — Always Free tier)
- CI/CD via GitHub Actions
- Observability: logging, metrics, health checks
- Production-grade governance of infrastructure and pipelines

**Phase 2, Phase 3, and Phase 4 artifacts are immutable and treated as stable
contracts.** No Phase V change MAY violate or modify Phase 2, 3, or 4 specs,
plans, or task definitions.

All agents, tools, and contributors MUST comply with this constitution.

---

## Core Principles

### I. Specification-First, AI-Native Development

All application behavior, service behavior, infrastructure, pipelines, and AI
behavior MUST originate from written specifications.

No code, configuration, Dockerfile, Helm chart, Dapr component, Kubernetes
manifest, or CI/CD pipeline may exist without traceability to specs and tasks.

**Rationale**: Specifications are the only defense against AI-induced ambiguity
and architectural drift in distributed, event-driven systems.

---

### II. Deterministic Systems via Tools and Runtimes

AI agents MUST act exclusively through approved tools and runtimes:

- MCP tools for application side effects
- Dapr APIs for:
  - Pub/Sub (event publishing and subscription)
  - State (state management)
  - Jobs (scheduled workflows)
  - Secrets (secrets access)
  - Service Invocation (inter-service calls)
- Docker AI (Gordon), kubectl-ai, and kagent for infrastructure operations

AI agents MUST NOT perform hidden side effects or undocumented actions.

**Rationale**: Deterministic tools and runtimes enable auditability, safety,
and reproducibility across all system layers.

---

### III. Stateless Services, Persistent State, Reproducible Clusters

- All services and agents MUST be stateless
- All application and workflow state MUST live in:
  - PostgreSQL (Neon Serverless), and/or
  - Dapr state stores (PostgreSQL-backed or equivalent)
- All infrastructure and pipelines MUST be reproducible from:
  - Repository contents
  - Specifications and plans
  - Tasks
  - Versioned configurations (Dockerfiles, Helm charts, Dapr components,
    Kubernetes manifests, GitHub Actions workflows)

**Rationale**: Enables horizontal scaling, disaster recovery, deterministic
rebuilds, and cloud portability.

---

### IV. Engineering Rigor (AI + Cloud + Event-Driven Systems)

All development MUST adhere to:

- Stable API, tool, runtime, and chart contracts
- Typed MCP tool schemas
- Explicit agent, service, and pipeline behavior rules
- Clear separation between:
  - Reasoning (AI)
  - Execution (Tools / Dapr / CI)
  - State (Database / State Stores)
- Zero "vibe-coding", zero manual, undocumented operations

**Rationale**: AI-operated, distributed, event-driven systems require stricter
discipline than monolithic applications.

---

## Key Standards

### Specification Traceability

Every feature and change MUST map to:

- `sp5.spec.md` (requirements)
- `sp5.plan.md` (architecture & cloud deployment)
- `sp5.tasks.md` (execution units)

Every Dockerfile, Helm chart, Dapr component, Kubernetes manifest, CI/CD
workflow, and pipeline file MUST reference a Task ID.

Every AI agent prompt MUST reference governing specs.

---

### Source of Truth Hierarchy

1. **sp.constitution** (WHY — governance and principles)
2. **sp5.spec** (WHAT — requirements and acceptance criteria)
3. **sp5.plan** (HOW — architecture and deployment design)
4. **sp5.tasks** (WORK — executable task units)
5. **Code / Config / Charts / Pipelines** (IMPLEMENTATION)

Lower layers MUST conform to higher layers. Conflicts MUST be resolved by
amending the higher-layer artifact first.

---

## Technical Constraints (Phase V — Immutable)

### Frontend

- OpenAI ChatKit (Hosted UI) or Vercel-hosted Next.js frontend

### Backend & Services

- FastAPI (Python 3.11+)
- SQLModel (ORM)
- Multi-service architecture:
  - Chat API + MCP Server
  - Notification Service
  - Recurring Task Service
  - Audit/Activity Service
  - Realtime/WebSocket Service

### AI Framework

- OpenAI Agents SDK
- OpenAI-compatible LLM API

### MCP

- Official MCP SDK (Python or TypeScript)

### Authentication

- Better Auth (JWT-based, stateless)

### State

- PostgreSQL (Neon Serverless) — primary data store
- Dapr State Stores (PostgreSQL-backed or equivalent)

### Eventing

- Kafka-compatible system:
  - Redpanda / Kafka / Confluent / Strimzi (in-cluster or managed)

### Distributed Runtime

- Dapr (sidecar model):
  - Pub/Sub
  - State
  - Jobs (Scheduler)
  - Secrets
  - Service Invocation

### Containerization

- Docker
- Docker AI Agent (Gordon) or Claude-generated Docker commands

### Orchestration

- Kubernetes:
  - Minikube (local development)
  - Oracle OKE (primary cloud target — Always Free tier)

### Packaging

- Helm Charts (sole deployment mechanism)

### AI DevOps

- kubectl-ai
- kagent

### CI/CD

- GitHub Actions (mandatory for cloud deployments)

### Observability

- Centralized logging (stdout/stderr collected by cluster)
- Health check endpoints (`/health`, `/readyz`)
- Metrics endpoints (Prometheus-compatible where applicable)

---

## Architecture Constraints

- Single public chat entrypoint via Chat API service
- MCP server exposes task operations only
- All services MUST be stateless; no in-process state storage
- All application side effects MUST go through:
  - MCP tools, or
  - Dapr APIs (Pub/Sub, State, Jobs, Secrets, Service Invocation)
- AI agents MUST NOT store memory or context internally
- Conversation and workflow context MUST be reconstructed from DB or
  Dapr state store per request
- All services MUST be deployed via Helm charts
- All clusters MUST be rebuildable from repository contents alone
- All inter-service communication SHOULD use Dapr Service Invocation
- All asynchronous workflows MUST use Dapr Pub/Sub over Kafka-compatible
  backends
- Tool calls, deployments, and event flows MUST be traceable and auditable

---

## AI & MCP Governance Rules

### AI Agent Rules

AI agents MUST:

- Use MCP tools exclusively for application side effects
- Use Dapr APIs for state, events, scheduling, and service calls
- Use Gordon / kubectl-ai / kagent for infrastructure operations
- Ask for clarification on ambiguity
- Never guess task IDs, user IDs, resource names, or topic names
- Confirm all destructive or irreversible actions in natural language

AI agents MUST NOT:

- Access databases directly (bypass MCP or Dapr)
- Bypass Dapr, MCP, or authentication mechanisms
- Execute hidden or implicit logic
- Perform manual, undocumented infrastructure or pipeline changes
- Store state in memory between requests

---

### MCP Tool Rules

MCP tools MUST:

- Be deterministic (same inputs produce same outputs)
- Perform exactly one operation per invocation
- Validate all inputs strictly
- Enforce user ownership and data isolation
- Persist state only via backend services or Dapr state stores

MCP tools MUST NOT:

- Perform side effects outside their declared scope
- Access resources belonging to other users
- Depend on in-process state from previous invocations

---

## Dapr Governance Rules

- All Pub/Sub interactions MUST go through Dapr Pub/Sub APIs
- All state access SHOULD go through Dapr state APIs unless the spec
  explicitly mandates direct database access (e.g., complex queries)
- All scheduled workflows MUST use the Dapr Jobs API
- All secrets access SHOULD use Dapr Secrets API or Kubernetes Secrets
- Services MUST NOT embed vendor-specific Kafka, Redis, or messaging SDK
  logic when Dapr abstractions exist for the same capability
- Dapr component definitions MUST be versioned and stored in the repository
- Dapr sidecar injection MUST be configured via Helm chart annotations

---

## Event-Driven (Kafka/Redpanda) Governance Rules

- All domain events MUST be published via Dapr Pub/Sub
- Services MUST communicate asynchronously via events for all workflows
  designated as event-driven in the spec
- Topics MUST be versioned and documented in specifications
- Topic naming convention: `<service>.<entity>.<action>` (e.g.,
  `tasks.task.created`, `tasks.task.completed`)
- No service MAY depend on direct Kafka client libraries unless explicitly
  approved by spec with documented rationale
- Event schemas MUST be versioned and backward-compatible
- Event consumers MUST be idempotent
- Dead-letter handling MUST be specified for all critical event flows

---

## Infrastructure & Cloud Governance Rules

- Docker images MUST be built from versioned Dockerfiles stored in-repo
- Helm charts MUST be the sole deployment mechanism for all services
- Dapr component manifests MUST be versioned and stored in-repo
- kubectl-ai and kagent MAY be used to generate, analyze, or operate
  Kubernetes resources
- Manual kubectl, docker, helm, or cloud console actions MUST NOT be used
  unless generated or explicitly approved by specs and tasks
- The following skills are the ONLY approved automation mechanisms:
  - `docker-fastapi` skill
  - `kubernetes` skill
- Oracle OKE is the primary cloud target; all cloud specs MUST target OKE
  first and MAY include other providers as secondary
- No infrastructure or cloud operations MAY occur outside specifications
  and tasks

---

## CI/CD & Observability Rules

### CI/CD

- All cloud deployments MUST go through GitHub Actions pipelines
- Pipelines MUST be reproducible from repository contents alone
- No manual production deployments are allowed
- Pipeline definitions MUST be stored in `.github/workflows/` and
  referenced by Task IDs
- Pipeline secrets MUST use GitHub Actions Secrets or equivalent
  encrypted store; no plaintext secrets in workflow files

### Observability

- All services MUST expose `/health` and `/readyz` endpoints
- All services MUST log to stdout/stderr in structured format
- Logs and metrics MUST be available for all deployed services
- Failed deployments MUST fail fast and report errors visibly in
  pipeline output

---

## Quality & Validation Rules

### AI Safety & Validation

- Tool invocation MUST be explicit (no implicit tool calls)
- Tool chaining MUST be explainable and traceable
- Errors MUST surface clearly to the user
- AI responses MUST reflect real tool outcomes (no hallucinated results)

### Infrastructure & Cloud Validation

- `minikube delete && minikube start` MUST allow full local redeploy
  from repository
- Cloud clusters (Oracle OKE) MUST be deployable from repository plus
  CI/CD pipelines alone
- `helm install` / `helm upgrade` MUST reproduce the complete system
- Pod restarts MUST NOT lose application or workflow state
- No manual cluster, cloud console, or pipeline state is allowed

### Security

- All external requests MUST be authenticated (JWT via Better Auth)
- Cross-user access MUST return HTTP 403 Forbidden
- MCP tool misuse MUST be blocked and logged
- Secrets MUST remain externalized (environment variables, Dapr Secrets,
  Kubernetes Secrets, or GitHub Actions Secrets)
- No secrets in code, container images, Helm values files, or manifests

---

## Success Criteria

### Phase III (AI & MCP — Baseline)

- [x] Users manage tasks via natural language
- [x] AI actions are fully tool-mediated
- [x] Conversation context persists across restarts
- [x] MCP tools are stateless and auditable

### Phase IV (Cloud-Native Deployment — Baseline)

- [x] System deploys on Minikube via Helm
- [x] Deployment is reproducible from repository
- [x] App survives pod restarts without data loss

### Phase V (Advanced Cloud & Event-Driven)

- [ ] Multi-service architecture is deployed and operational
- [ ] Dapr is used for Pub/Sub, State, Jobs, Secrets, Service Invocation
- [ ] Kafka/Redpanda is operational via Dapr Pub/Sub
- [ ] Event-driven workflows function:
  - [ ] Notifications (task reminders)
  - [ ] Recurring task scheduling
  - [ ] Audit/activity logging
  - [ ] Realtime/WebSocket synchronization
- [ ] System deploys to Oracle OKE (primary cloud target)
- [ ] CI/CD pipeline (GitHub Actions) deploys the system end-to-end
- [ ] Observability is in place (health checks, logging, metrics)
- [ ] No manual, undocumented infrastructure or pipeline changes exist
- [ ] All event schemas are versioned and backward-compatible

---

## Failure Conditions

The project FAILS if any of the following conditions are true:

- AI bypasses MCP tools or Dapr APIs for side effects
- Application or workflow state is stored in service memory
- Behavior exists outside written specifications
- Infrastructure or pipelines are changed manually without spec/task
  authorization
- Cluster or cloud environment cannot be rebuilt from repository alone
- Services use direct vendor SDKs (Kafka, Redis, etc.) where Dapr
  abstractions are mandated
- Event schemas are changed without versioning and backward compatibility
- Tool logic duplicates backend service logic
- Secrets appear in code, images, or manifests
- Ambiguity is resolved without user confirmation

---

## Enforcement

All AI agents and developers MUST:

- Read this constitution before acting on any Phase V work
- Halt immediately on rule violations and report the violation
- Request clarification when specs are incomplete or ambiguous
- Reference Task IDs, tool names, service names, topic names, and chart
  names in all outputs
- Ensure all changes are traceable through the Source of Truth Hierarchy
- Verify that Dapr, MCP, and CI/CD governance rules are satisfied before
  marking tasks complete

---

## Governance

### Amendment Procedure

1. Propose amendment with rationale and impact assessment
2. Document impact on specs, plans, tasks, pipelines, and Dapr components
3. Explicit user approval required (no auto-amendments)
4. Update constitution version and date
5. Propagate changes to all dependent artifacts

### Versioning Policy

- **MAJOR**: Changes to AI governance, MCP rules, Dapr governance, eventing
  rules, cloud targeting, infrastructure governance, or core principles
- **MINOR**: New services, tools, constraints, or observability rules added
- **PATCH**: Clarifications, wording fixes, and non-semantic refinements

### Compliance Review

- All spec, plan, and task artifacts MUST pass constitution alignment check
  before implementation begins
- The `Constitution Check` section in plan templates MUST reference current
  constitution version (4.0.0)
- Periodic review SHOULD occur when new phases or major features are proposed

---

**Version**: 4.0.0
**Ratified**: 2026-02-02
**Last Amended**: 2026-02-08
