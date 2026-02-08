# Implementation Plan: Phase 4 Infrastructure — Local Kubernetes Deployment

**Branch**: `001-k8s-helm-deployment` | **Date**: 2026-02-03 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-k8s-helm-deployment/spec.md`

---

## Summary

Phase 4 transforms the existing Phase 3 Todo AI Chatbot into a fully containerized, Kubernetes-deployable system. The implementation uses Docker for containerization, Helm for packaging, and Minikube for local orchestration. All infrastructure operations MUST be performed via approved AI DevOps tools (Gordon/Claude for Docker, kubectl-ai/kagent for Kubernetes).

**Primary Deliverables**:
- Backend Docker image (FastAPI + MCP + Agents SDK)
- Frontend Docker image (Next.js + ChatKit)
- Backend Helm chart
- Frontend Helm chart
- Reproducible deployment workflow

---

## Technical Context

**Language/Version**: Python 3.11 (Backend), TypeScript 5.x / Node.js 20+ (Frontend)
**Primary Dependencies**: FastAPI, SQLModel, OpenAI Agents SDK, MCP SDK (Backend); Next.js 16+, React 19, ChatKit, Better Auth (Frontend)
**Storage**: PostgreSQL (Neon Serverless) — External to cluster
**Testing**: pytest (Backend), vitest (Frontend)
**Target Platform**: Minikube (local Kubernetes), Docker Desktop
**Project Type**: Web application (frontend + backend)
**Performance Goals**: Pods ready within 5 minutes of `helm install`
**Constraints**: Helm-only deployment, AI-mediated operations only, no manual kubectl/docker commands
**Scale/Scope**: Single-node Minikube cluster, 1-3 replicas per service (configurable)

---

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| Specification-First | ✅ PASS | `spec.md` exists with 19 functional requirements, 5 NFRs |
| Deterministic Systems via Tools | ✅ PASS | Only Gordon, kubectl-ai, kagent approved for operations |
| Stateless Intelligence | ✅ PASS | PostgreSQL external, containers stateless |
| Reproducible Clusters | ✅ PASS | `minikube delete && helm install` workflow defined |
| No Manual Operations | ✅ PASS | Constitution forbids undocumented infra changes |
| Approved Automation | ✅ PASS | docker-fastapi, kubernetes skills specified |

**Result**: All gates pass. Proceed to Phase 0.

---

## Project Structure

### Documentation (this feature)

```text
specs/001-k8s-helm-deployment/
├── spec.md              # Feature requirements
├── plan.md              # This file
├── research.md          # Phase 0 output (AI DevOps tool research)
├── data-model.md        # Phase 1 output (Kubernetes resource model)
├── quickstart.md        # Phase 1 output (deployment guide)
├── contracts/           # Phase 1 output (Helm value contracts)
│   ├── backend-values.yaml
│   └── frontend-values.yaml
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (from /sp.tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── models/              # SQLModel schemas
│   ├── routers/             # API routes (tasks.py)
│   ├── middleware/          # JWT auth
│   └── schemas/             # Pydantic schemas
├── tests/                   # pytest tests
├── Dockerfile               # Backend container definition (exists, needs review)
└── requirements.txt         # Python dependencies

frontend/
├── app/                     # Next.js App Router
│   ├── (auth)/              # Login/signup routes
│   ├── chat/                # Chat interface
│   └── api/                 # API routes
├── components/              # React components
├── lib/                     # Utilities (auth, api-client)
├── Dockerfile               # Frontend container definition (NEW)
└── package.json             # Node dependencies

charts/                      # NEW: Helm charts directory
├── todo-backend/
│   ├── Chart.yaml
│   ├── values.yaml
│   └── templates/
│       ├── deployment.yaml
│       ├── service.yaml
│       ├── configmap.yaml
│       └── _helpers.tpl
└── todo-frontend/
    ├── Chart.yaml
    ├── values.yaml
    └── templates/
        ├── deployment.yaml
        ├── service.yaml
        ├── configmap.yaml
        └── _helpers.tpl
```

**Structure Decision**: Web application pattern with separate backend/frontend directories. Helm charts added at repository root in `charts/` directory following Helm conventions.

---

## Complexity Tracking

No constitution violations requiring justification.

---

## Phase 0: Research (AI DevOps Tools & Patterns)

### Research Topics

| Topic | Status | Findings |
|-------|--------|----------|
| Docker multi-stage builds for Python | COMPLETE | Use slim base, separate build/runtime stages |
| Docker multi-stage builds for Next.js | COMPLETE | Node alpine, standalone output mode |
| Helm chart structure best practices | COMPLETE | Standard template pattern with helpers |
| Minikube image loading strategy | COMPLETE | `minikube image load` or registry |
| kubectl-ai usage patterns | COMPLETE | Natural language → kubectl commands |
| kagent cluster analysis | COMPLETE | Health checks, resource optimization |
| Service-to-service communication in K8s | COMPLETE | DNS names: `service-name.namespace.svc.cluster.local` |
| Next.js runtime environment variables | COMPLETE | NEXT_PUBLIC_* at build time, server at runtime |

### Key Decisions

1. **Image Registry**: Use Minikube's built-in Docker daemon (`eval $(minikube docker-env)`) to avoid external registry dependency.

2. **Frontend Build Strategy**: Next.js standalone output with runtime environment variable injection via ConfigMap.

3. **Service Types**:
   - Backend: ClusterIP (internal only)
   - Frontend: NodePort (host accessible) or via `minikube tunnel`

4. **Health Checks**: Liveness and readiness probes for both services.

5. **Secret Management**: Kubernetes Secrets for DATABASE_URL and BETTER_AUTH_SECRET, referenced via environment variables.

---

## Phase 1: Design & Contracts

### 1.1 Kubernetes Resource Model

See `data-model.md` for complete resource definitions.

**Backend Resources**:
- Deployment: `todo-backend`
  - Image: `todo-backend:latest` (configurable)
  - Replicas: 1 (configurable)
  - Port: 8000
  - Health: `/health` endpoint
  - Env: DATABASE_URL, BETTER_AUTH_SECRET, CORS_ORIGINS

- Service: `todo-backend`
  - Type: ClusterIP
  - Port: 8000 → 8000

**Frontend Resources**:
- Deployment: `todo-frontend`
  - Image: `todo-frontend:latest` (configurable)
  - Replicas: 1 (configurable)
  - Port: 3000
  - Health: `/` endpoint
  - Env: NEXT_PUBLIC_API_URL (set to backend service URL)

- Service: `todo-frontend`
  - Type: NodePort
  - Port: 3000 → 3000
  - NodePort: 30000 (configurable)

### 1.2 Helm Value Contracts

**Backend values.yaml**:
```yaml
replicaCount: 1

image:
  repository: todo-backend
  tag: "latest"
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: 8000

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 256Mi

env:
  DATABASE_URL: ""          # Required: Neon connection string
  BETTER_AUTH_SECRET: ""    # Required: JWT secret
  CORS_ORIGINS: "http://todo-frontend:3000"

healthCheck:
  path: /health
  initialDelaySeconds: 10
  periodSeconds: 10
```

**Frontend values.yaml**:
```yaml
replicaCount: 1

image:
  repository: todo-frontend
  tag: "latest"
  pullPolicy: IfNotPresent

service:
  type: NodePort
  port: 3000
  nodePort: 30000

resources:
  limits:
    cpu: 500m
    memory: 512Mi
  requests:
    cpu: 100m
    memory: 256Mi

env:
  NEXT_PUBLIC_API_URL: "http://todo-backend:8000"
  BETTER_AUTH_SECRET: ""    # Required: JWT secret
  DATABASE_URL: ""          # Required for Better Auth (same DB)

healthCheck:
  path: /
  initialDelaySeconds: 15
  periodSeconds: 10
```

### 1.3 Docker Image Specifications

**Backend Dockerfile** (multi-stage):
```dockerfile
# Stage 1: Build
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Stage 2: Runtime
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
USER nobody
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile** (multi-stage):
```dockerfile
# Stage 1: Dependencies
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# Stage 2: Build
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Runtime
FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
EXPOSE 3000
USER node
CMD ["node", "server.js"]
```

### 1.4 Service Communication

```text
┌─────────────────────────────────────────────────────────────┐
│                      Minikube Cluster                       │
│                                                             │
│  ┌─────────────────┐         ┌─────────────────┐           │
│  │  todo-frontend  │────────▶│  todo-backend   │           │
│  │   (NodePort)    │  HTTP   │   (ClusterIP)   │           │
│  │    :30000       │         │     :8000       │           │
│  └─────────────────┘         └────────┬────────┘           │
│                                       │                     │
└───────────────────────────────────────┼─────────────────────┘
                                        │ External
                                        ▼
                              ┌─────────────────┐
                              │ Neon PostgreSQL │
                              │   (External)    │
                              └─────────────────┘
```

---

## Phase 2: Implementation Approach

### 2.1 Implementation Order

1. **Containerization** (FR-1)
   - T001: Review/update backend Dockerfile
   - T002: Create frontend Dockerfile
   - T003: Local image build verification

2. **Helm Charts** (FR-2)
   - T004: Create backend Helm chart
   - T005: Create frontend Helm chart
   - T006: Create values override templates

3. **Minikube Deployment** (FR-3)
   - T007: Configure Minikube environment
   - T008: Deploy and validate backend
   - T009: Deploy and validate frontend
   - T010: End-to-end connectivity test

4. **AI DevOps Integration** (FR-4)
   - T011: kubectl-ai deployment operations
   - T012: kubectl-ai debugging/inspection
   - T013: kagent cluster health analysis
   - T014: Document AI tool usage

5. **Reproducibility Validation** (NFR-1)
   - T015: Full cluster reset test
   - T016: Documentation review

### 2.2 AI DevOps Tool Usage Plan

| Task | Tool | Operation |
|------|------|-----------|
| T001-T003 | Gordon / Claude | Generate Dockerfiles, build commands |
| T004-T006 | Claude | Generate Helm templates |
| T007 | kubectl-ai | Minikube cluster setup validation |
| T008-T009 | kubectl-ai | `helm install` operations |
| T010 | kubectl-ai | Service connectivity diagnosis |
| T011 | kubectl-ai | Deployment operations |
| T012 | kubectl-ai | Pod inspection, log analysis |
| T013 | kagent | Cluster health analysis |
| T015 | kubectl-ai | Reset and redeploy validation |

---

## Validation Plan

### Pre-Deployment Checks

- [ ] Backend Dockerfile builds successfully
- [ ] Frontend Dockerfile builds successfully
- [ ] Images start and respond to health checks locally
- [ ] Helm charts pass `helm lint`

### Deployment Checks

- [ ] `helm install todo-backend` creates all resources
- [ ] `helm install todo-frontend` creates all resources
- [ ] Backend pods reach Ready state
- [ ] Frontend pods reach Ready state
- [ ] Backend service is accessible within cluster
- [ ] Frontend service is accessible from host

### Functional Checks

- [ ] Frontend loads in browser
- [ ] Authentication flow works
- [ ] Chat interface connects to backend
- [ ] Task operations function correctly
- [ ] Pod restart preserves data in PostgreSQL

### Reproducibility Checks

- [ ] `minikube delete && minikube start` succeeds
- [ ] Images rebuild without errors
- [ ] `helm install` deploys complete system
- [ ] All functional checks pass after reset

### AI DevOps Verification

- [ ] kubectl-ai used for deployment (document command)
- [ ] kubectl-ai used for debugging (document command)
- [ ] kagent used for cluster analysis (document output)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| AI-generated manifests need refinement | Iterate via skill-mediated execution |
| Minikube resource limits | Document minimum: 4GB RAM, 2 CPUs |
| Frontend-backend connectivity | Use explicit service DNS names |
| Neon connectivity from cluster | Verify external network access early |
| Image size too large | Multi-stage builds, alpine bases |

---

## Exit Criteria

Phase 4 is complete when:

1. ✅ Backend and frontend are containerized (Dockerfiles committed)
2. ✅ Helm charts deploy successfully on Minikube
3. ✅ `minikube delete && minikube start && helm install` reproduces system
4. ✅ kubectl-ai and kagent usage documented
5. ✅ No Phase 3 application code modified
6. ✅ All artifacts traceable to tasks

---

## Next Step

This plan MUST be decomposed into executable work units via:

> `/sp.tasks`

Each task MUST reference:
- This plan
- `spec.md`
- `constitution.md`
