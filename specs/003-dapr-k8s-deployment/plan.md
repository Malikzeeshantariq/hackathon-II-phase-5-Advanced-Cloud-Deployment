# Implementation Plan: Phase V Part B & C — Dapr K8s Deployment

**Branch**: `003-dapr-k8s-deployment` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-dapr-k8s-deployment/spec.md`

## Summary

Deploy the complete multi-service Todo system (Chat API, Notification, Recurring Task, Audit) to Kubernetes with Dapr runtime and Kafka-compatible messaging. Part B validates the full architecture locally on Minikube with Redpanda. Part C promotes the same architecture to Oracle OKE Always Free Tier with PostgreSQL-backed Dapr Pub/Sub and GitHub Actions CI/CD. Environment parity is enforced — only configuration (values, secrets, endpoints) differs between local and cloud.

## Technical Context

**Language/Version**: Python 3.11+ (all backend services), TypeScript/Node.js 20+ (frontend)
**Primary Dependencies**: FastAPI, SQLModel, Dapr Python SDK, dapr-ext-fastapi, Helm 3.10+, Dapr 1.14+
**Storage**: PostgreSQL (Neon Serverless) — external to cluster
**Testing**: Helm template validation, health endpoint verification, event flow integration tests
**Target Platform**: Kubernetes (Minikube local, Oracle OKE cloud)
**Project Type**: Multi-service web application
**Performance Goals**: All services healthy within 5 minutes of deployment; events processed within 30 seconds
**Constraints**: OKE Free Tier (4 ARM vCPUs, 24GB RAM); ARM multi-arch images required
**Scale/Scope**: 4-5 services, 2 environments (local/cloud), 1 CI/CD pipeline

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| All services containerized | PASS | Dockerfiles exist for all 5 services (backend, notification, recurring, audit, frontend) |
| All services stateless | PASS | All state in Neon PostgreSQL / Dapr state stores |
| All deployment via Helm | PASS | Helm charts exist for all 5 services under `charts/` |
| Cluster reproducible from repo | PASS | All manifests, charts, and Dapr components in repo |
| No manual kubectl/helm/console ops | PASS | All ops scripted or pipelined |
| Service-to-service via Dapr | PASS | All services use Dapr Pub/Sub and Service Invocation |
| Async workflows via Dapr Pub/Sub | PASS | Pub/Sub component configured for Kafka (local) and PostgreSQL (cloud) |
| Secrets externalized | PASS | Kubernetes Secrets + Dapr Secrets store |
| Health endpoints on all services | PASS | All services expose /health |
| Structured logging | NEEDS WORK | Services log to stdout but structured format needs verification |
| CI/CD via GitHub Actions | NEEDS WORK | No pipelines exist yet — Part C deliverable |
| ARM multi-arch images | NEEDS WORK | Current Dockerfiles are amd64 only — need buildx |

**Post-Design Re-check**: Structured logging, CI/CD, and ARM builds are addressed in this plan as explicit deliverables.

## Project Structure

### Documentation (this feature)

```text
specs/003-dapr-k8s-deployment/
├── plan.md              # This file
├── research.md          # Phase 0 output (completed)
├── data-model.md        # Phase 1 output (infrastructure entities)
├── quickstart.md        # Phase 1 output (local deployment guide)
├── contracts/           # Phase 1 output (Helm value schemas, pipeline specs)
└── tasks.md             # Phase 2 output (/sp.tasks command)
```

### Source Code (repository root)

```text
# Existing (from Part A)
backend/                     # Chat API + MCP service
├── Dockerfile
├── app/
│   └── main.py             # /health endpoint exists
└── requirements.txt

services/
├── notification/            # Notification service
│   ├── Dockerfile
│   └── app/main.py         # /health + /dapr/subscribe
├── recurring/               # Recurring task service
│   ├── Dockerfile
│   └── app/main.py         # /health + /dapr/subscribe
└── audit/                   # Audit service
    ├── Dockerfile
    └── app/main.py          # /health + /dapr/subscribe

frontend/                    # Next.js frontend
├── Dockerfile
└── ...

charts/
├── todo-backend/            # Helm chart (Dapr-enabled)
├── todo-frontend/           # Helm chart (no Dapr)
├── notification-service/    # Helm chart (Dapr-enabled)
├── recurring-service/       # Helm chart (Dapr-enabled)
└── audit-service/           # Helm chart (Dapr-enabled)

dapr/
└── components/
    ├── pubsub.yaml          # pubsub.kafka (local Redpanda)
    ├── statestore.yaml      # state.postgresql (Neon)
    └── secrets.yaml         # secretstores.kubernetes

# New (Part B & C deliverables)
dapr/
└── components/
    └── pubsub-cloud.yaml    # pubsub.postgresql (Neon — OKE free tier)

charts/
├── */values-local.yaml      # Local Minikube overrides
└── */values-cloud.yaml      # OKE cloud overrides

scripts/
├── deploy-local.sh          # Minikube full deployment script
└── deploy-cloud.sh          # OKE deployment script (for manual runs)

.github/
└── workflows/
    ├── build.yml             # Build + push multi-arch images to OCIR
    └── deploy-oke.yml        # Deploy to OKE via Helm
```

**Structure Decision**: Multi-service web application with per-service Helm charts. Existing structure from Part A is preserved. New artifacts are environment-specific value files, cloud Dapr components, deployment scripts, and CI/CD pipelines.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| PostgreSQL-backed Pub/Sub for cloud | OKE free tier lacks resources for Redpanda | Kafka on ARM free tier would consume >50% of available resources |
| Multi-arch Docker builds | OKE free tier uses ARM nodes | Separate ARM-only images would break local Minikube (amd64) |

---

## Architecture Design

### Environment Parity Strategy

Local (Minikube) and Cloud (OKE) share:
- Identical container images (multi-arch: amd64 + arm64)
- Identical Helm chart templates
- Identical Dapr API calls in application code
- Identical service topology (Chat API, Notification, Recurring, Audit)
- Identical Kubernetes resource types (Deployment, Service, ConfigMap)

Only these differ:
- Helm values files (`values-local.yaml` vs `values-cloud.yaml`)
- Dapr Pub/Sub component (`pubsub.kafka` local vs `pubsub.postgresql` cloud)
- Image registry (Minikube local registry vs OCIR)
- Secrets source (local kubectl create secret vs GitHub Actions secrets)
- Resource allocations (generous local vs constrained cloud)

### Part B — Local Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Minikube Cluster                          │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Chat API    │  │ Notification │  │  Recurring   │     │
│  │  + MCP       │  │  Service     │  │  Service     │     │
│  │  [Dapr]      │  │  [Dapr]      │  │  [Dapr]      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │               │
│  ┌──────┴─────────────────┴─────────────────┴──────┐       │
│  │              Dapr Control Plane                   │       │
│  │    (placement + operator + sentry + dashboard)    │       │
│  └──────────────────────┬────────────────────────────┘       │
│                         │                                    │
│  ┌──────────────────────┴────────────────────────────┐       │
│  │           Redpanda (Kafka-compatible)              │       │
│  │              pubsub.kafka component                │       │
│  └───────────────────────────────────────────────────┘       │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Audit Service│  │  Frontend    │                        │
│  │  [Dapr]      │  │  (no Dapr)   │                        │
│  └──────────────┘  └──────────────┘                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         │ External
         ▼
  ┌──────────────────┐
  │  Neon PostgreSQL  │
  │  (state + data)   │
  └──────────────────┘
```

**Local Cluster Requirements**:
- Minikube: `minikube start --cpus=6 --memory=12288 --driver=docker`
- Dapr: non-HA mode (1 replica per control plane component)
- Redpanda: single broker, 1 CPU, 2GB RAM
- All images loaded via `minikube image load` or `eval $(minikube docker-env)`

### Part C — Cloud Deployment Architecture (OKE Free Tier)

```
┌─────────────────────────────────────────────────────────────┐
│               Oracle OKE Cluster (Free Tier)                │
│           2 nodes × VM.Standard.A1.Flex (ARM)               │
│           2 vCPU + 12GB RAM per node                        │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Chat API    │  │ Notification │  │  Recurring   │     │
│  │  + MCP       │  │  Service     │  │  Service     │     │
│  │  [Dapr]      │  │  [Dapr]      │  │  [Dapr]      │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │               │
│  ┌──────┴─────────────────┴─────────────────┴──────┐       │
│  │              Dapr Control Plane (non-HA)          │       │
│  └──────────────────────┬────────────────────────────┘       │
│                         │                                    │
│         (No Kafka broker — Dapr uses PostgreSQL Pub/Sub)    │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Audit Service│  │  Frontend    │                        │
│  │  [Dapr]      │  │  (no Dapr)   │                        │
│  │  (optional)  │  └──────────────┘                        │
│  └──────────────┘                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
         │
         │ External
         ▼
  ┌──────────────────┐
  │  Neon PostgreSQL  │
  │ (state + data +   │
  │  pub/sub backing)  │
  └──────────────────┘
```

**OKE Free Tier Resource Budget**:

| Component | vCPU Request | Memory Request | Notes |
|-----------|-------------|----------------|-------|
| Dapr control plane (non-HA) | 300m | 1GB | 3 components × ~100m/330MB |
| Chat API + MCP | 100m | 256MB | Core service |
| Notification Service | 50m | 128MB | Lightweight |
| Recurring Task Service | 50m | 128MB | Lightweight |
| Audit Service (optional) | 50m | 128MB | Exclude if resources tight |
| Frontend | 100m | 256MB | Static serve |
| Dapr sidecars (×3-4) | 200m | 512MB | ~50m/128MB each |
| K8s system | 500m | 1GB | DNS, kube-proxy |
| **Total (with Audit)** | **1350m** | **3.4GB** | Well within 4000m/24GB |
| **Total (without Audit)** | **1300m** | **3.3GB** | Even more headroom |

### CI/CD Pipeline Design

```
┌──────────────┐    ┌───────────────┐    ┌──────────────┐
│  Push to     │───▶│  Build Stage  │───▶│  Push Stage  │
│  main branch │    │  (buildx      │    │  (OCIR)      │
│              │    │   multi-arch) │    │              │
└──────────────┘    └───────────────┘    └──────┬───────┘
                                                │
                                         ┌──────▼───────┐
                                         │ Deploy Stage │
                                         │ (Helm to OKE)│
                                         └──────────────┘
```

**Pipeline: build.yml**
- Trigger: Push to main branch (or manual dispatch)
- Steps:
  1. Checkout code
  2. Set up Docker Buildx
  3. Login to OCIR (`oracle-actions/login-ocir`)
  4. Build multi-arch images (amd64 + arm64) for all services
  5. Push to OCIR with commit SHA tag + `latest` tag
- Concurrency: Cancel in-progress builds for same branch

**Pipeline: deploy-oke.yml**
- Trigger: Successful build.yml completion (or manual dispatch)
- Steps:
  1. Configure kubectl for OKE (`oracle-actions/configure-kubectl-oke`)
  2. Apply Dapr components (cloud variants)
  3. Helm upgrade --install for each service with `values-cloud.yaml`
  4. Verify health endpoints
- Concurrency: Single deploy at a time (queue)

### Helm Values Strategy

Each chart will have:
- `values.yaml` — defaults (works for local Minikube)
- `values-cloud.yaml` — cloud overrides (OKE-specific resource limits, image registry, etc.)

Local deployment: `helm install <svc> charts/<svc>/`
Cloud deployment: `helm install <svc> charts/<svc>/ -f charts/<svc>/values-cloud.yaml`

### Dapr Component Strategy

```text
dapr/components/
├── pubsub.yaml              # Local: pubsub.kafka (Redpanda)
├── pubsub-cloud.yaml        # Cloud: pubsub.postgresql (Neon)
├── statestore.yaml          # Shared: state.postgresql (Neon)
└── secrets.yaml             # Shared: secretstores.kubernetes
```

Local deployment: `kubectl apply -f dapr/components/pubsub.yaml -f dapr/components/statestore.yaml -f dapr/components/secrets.yaml`
Cloud deployment: `kubectl apply -f dapr/components/pubsub-cloud.yaml -f dapr/components/statestore.yaml -f dapr/components/secrets.yaml`

### Health & Readiness Strategy

All services already expose `/health`. Add `/readyz` where missing:
- `/health` → liveness probe (is the process alive?)
- `/readyz` → readiness probe (is the service ready to accept traffic?)

Readiness should check:
- Database connection (for data services)
- Dapr sidecar availability (for Dapr-enabled services)

### Secrets Management

**Local (Minikube)**:
```bash
kubectl create secret generic dapr-secrets \
  --from-literal=database-url="$DATABASE_URL" \
  --from-literal=better-auth-secret="$BETTER_AUTH_SECRET"
```

**Cloud (OKE)**:
- GitHub Actions secrets → injected into pipeline
- kubectl create secret in deploy pipeline step
- Never stored in repo or Helm values

### Deployment Order

Both environments follow this order:
1. Install Dapr runtime (`helm install dapr dapr/dapr`)
2. Deploy Redpanda (local only) or apply cloud Dapr components
3. Apply Dapr component manifests
4. Create Kubernetes secrets
5. Deploy backend (Chat API + MCP)
6. Deploy supporting services (Notification, Recurring, Audit)
7. Deploy frontend
8. Verify health endpoints

---

## Risk Analysis

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| OKE free tier resource exhaustion | Medium | High | Tight resource budgets; Audit service optional; monitoring |
| ARM image build failures | Low | High | Test multi-arch builds in CI before cloud deploy |
| Dapr PostgreSQL Pub/Sub throughput limits | Low | Medium | Sufficient for demo/dev; document limitation |
| Minikube resource exhaustion on dev machines | Medium | Medium | Document minimum requirements (6 CPU, 12GB RAM) |
| OCI auth token expiry | Medium | Medium | Document token rotation; use OIDC when possible |
