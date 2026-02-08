# Feature Specification: Phase 4 Infrastructure — Local Kubernetes Deployment

**Feature Branch**: `001-k8s-helm-deployment`
**Created**: 2026-02-03
**Status**: Draft
**Phase**: 4 (Cloud-Native Deployment)

---

## 1. Scope

This specification defines the requirements for **Phase 4: Local Kubernetes Deployment** of the Todo AI Chatbot.

Phase 4 focuses exclusively on:

- Containerization of the existing Phase 3 application (frontend + backend)
- Deployment to a local Kubernetes cluster using Minikube
- Packaging and lifecycle management using Helm charts
- AI-assisted DevOps operations using:
  - Docker AI Agent (Gordon) or Claude-generated Docker commands
  - kubectl-ai
  - kagent
- Ensuring full reproducibility, auditability, and stateless operation

**Phase 3 application behavior, MCP tools, and AI agent logic are immutable and MUST NOT be modified.**

---

## 2. Non-Goals

Phase 4 explicitly does NOT include:

- Any changes to application features or business logic
- Any changes to MCP tools or AI agent behavior
- Any production cloud deployment (EKS/GKE/AKS)
- Any CI/CD pipeline implementation
- Any non-Helm-based deployment method
- Any manual, undocumented infrastructure operations

---

## 3. Definitions

| Term | Definition |
|------|------------|
| **Application** | The Phase 3 Todo AI Chatbot (ChatKit + FastAPI + MCP + Agents SDK + PostgreSQL) |
| **Infrastructure** | Docker images, Helm charts, Kubernetes resources, Minikube cluster |
| **AI DevOps Tools** | Gordon (Docker AI), kubectl-ai, kagent |
| **Reproducible Deployment** | A deployment that can be recreated from the repository and specs alone |

---

## 4. User Scenarios & Testing

### User Story 1 — Deploy Application to Local Kubernetes (Priority: P1)

As a developer, I want to deploy the complete Todo AI Chatbot to a local Kubernetes cluster so that I can validate the containerized application works correctly before production.

**Why this priority**: Core deliverable of Phase 4 — without this, no other scenarios are possible.

**Independent Test**: Deploy via `helm install`, access the frontend, and verify chat functionality works.

**Acceptance Scenarios**:

1. **Given** Minikube is running and images are built, **When** I run `helm install`, **Then** all pods reach Ready state within 5 minutes
2. **Given** the system is deployed, **When** I access the frontend URL, **Then** I can interact with the AI chatbot
3. **Given** the system is deployed, **When** a pod restarts, **Then** no conversation data is lost

---

### User Story 2 — Reproducible Clean Deployment (Priority: P1)

As a developer, I want to completely destroy and recreate the deployment from scratch so that I can verify the system is fully reproducible.

**Why this priority**: Validates determinism and auditability — core Phase 4 principles.

**Independent Test**: Run `minikube delete && minikube start`, build images, run `helm install`, verify system works.

**Acceptance Scenarios**:

1. **Given** a running deployment, **When** I delete Minikube and restart it, **Then** I can redeploy the full system with only repo contents
2. **Given** a fresh Minikube cluster, **When** I follow the documented steps, **Then** the system deploys without manual intervention
3. **Given** the deployment workflow, **When** executed by any developer, **Then** the same deployment state is achieved

---

### User Story 3 — AI-Assisted DevOps Operations (Priority: P2)

As a developer, I want to use AI DevOps tools (kubectl-ai, kagent, Gordon) to perform infrastructure operations so that operations are auditable and consistent.

**Why this priority**: Demonstrates AI DevOps integration per constitution requirements.

**Independent Test**: Use kubectl-ai to inspect deployment, kagent to check cluster health, Gordon to build images.

**Acceptance Scenarios**:

1. **Given** I need to deploy, **When** I use kubectl-ai, **Then** it generates or applies correct manifests
2. **Given** I need to debug, **When** I use kagent to analyze cluster, **Then** it provides actionable insights
3. **Given** I need to build images, **When** I use Gordon or Claude-generated commands, **Then** images build successfully

---

### User Story 4 — Independent Scaling of Components (Priority: P3)

As an operator, I want to scale the frontend and backend independently so that I can optimize resource allocation.

**Why this priority**: Validates proper service separation and Helm configurability.

**Independent Test**: Modify replica count in `values.yaml`, run `helm upgrade`, verify pod count changes.

**Acceptance Scenarios**:

1. **Given** backend replica count is 1, **When** I set it to 3 via values.yaml, **Then** 3 backend pods run
2. **Given** frontend replica count changes, **When** I apply the change, **Then** frontend scales without affecting backend
3. **Given** scaled deployment, **When** I access the system, **Then** all replicas receive traffic

---

### Edge Cases

- What happens when Minikube has insufficient resources? → Clear error message and deployment halts
- What happens when image build fails? → Build fails with actionable error, deployment blocked
- What happens when services cannot connect? → Health checks fail, pods report NotReady
- What happens when external database (Neon) is unreachable? → Backend pods fail health checks, frontend shows error state

---

## 5. Functional Requirements

### FR-1: Docker Images

- **FR-1.1**: System MUST provide a Docker image for the backend
- **FR-1.2**: System MUST provide a Docker image for the frontend
- **FR-1.3**: Images MUST be built from versioned Dockerfiles in the repository
- **FR-1.4**: Images MUST start successfully and serve the application
- **FR-1.5**: Images MUST connect to the configured PostgreSQL database (Neon)
- **FR-1.6**: Images MUST be buildable using Gordon or Claude-generated Docker commands

---

### FR-2: Helm-Based Deployment

- **FR-2.1**: System MUST be deployable using Helm charts only
- **FR-2.2**: Helm charts MUST create Kubernetes Deployments for frontend and backend
- **FR-2.3**: Helm charts MUST create Kubernetes Services for frontend and backend
- **FR-2.4**: Helm charts MUST expose configurable values via `values.yaml`
- **FR-2.5**: Helm charts MUST support configurable replica counts
- **FR-2.6**: `helm install` MUST be sufficient to deploy the entire system
- **FR-2.7**: `helm uninstall` MUST cleanly remove all resources

---

### FR-3: Minikube Execution

- **FR-3.1**: System MUST run on a local Minikube cluster
- **FR-3.2**: Frontend MUST be accessible from the host machine
- **FR-3.3**: Backend MUST be reachable by the frontend inside the cluster
- **FR-3.4**: Backend MUST be able to connect to external PostgreSQL (Neon)

---

### FR-4: AI DevOps Tool Usage

- **FR-4.1**: kubectl-ai MUST be used for at least one deployment-related operation
- **FR-4.2**: kubectl-ai MUST be used for at least one debugging/inspection operation
- **FR-4.3**: kagent MUST be used for at least one cluster health or resource analysis operation
- **FR-4.4**: Gordon or Claude-generated Docker commands MUST be used for image creation
- **FR-4.5**: All AI-generated artifacts MUST be committed to the repository

---

### FR-5: Configuration Management

- **FR-5.1**: All configuration MUST be externalized via environment variables or Helm values
- **FR-5.2**: Secrets MUST NOT be hardcoded in images or Helm charts
- **FR-5.3**: Database connection string MUST be configurable at deployment time
- **FR-5.4**: API URLs MUST be configurable at deployment time

---

## 6. Key Entities

| Entity | Description | Key Attributes |
|--------|-------------|----------------|
| **Docker Image** | Containerized application component | tag, build context, exposed ports |
| **Helm Chart** | Deployment package for a service | name, version, values, templates |
| **Deployment** | Kubernetes workload resource | replicas, image, env vars, health checks |
| **Service** | Kubernetes network resource | type, port, selector |
| **ConfigMap** | Kubernetes configuration resource | key-value pairs for non-secret config |
| **Secret** | Kubernetes secret resource | database credentials, API keys |

---

## 7. Non-Functional Requirements

### NFR-1: Determinism

- The same specs and repository state MUST produce the same deployment outcome
- No manual cluster state is permitted

### NFR-2: Auditability

- All Dockerfiles, Helm charts, and configs MUST be version-controlled
- All artifacts MUST be traceable to tasks in `tasks.md`

### NFR-3: Statelessness

- No application state MUST be stored in containers or pods
- All persistent state MUST remain in PostgreSQL (Neon)

### NFR-4: Security

- Secrets MUST NOT be hardcoded in images or charts
- Configuration MUST be externalized via environment variables or values files
- Images SHOULD run as non-root users

### NFR-5: Availability

- Pod restarts MUST NOT cause data loss
- Health checks MUST be implemented for all containers
- System MUST recover automatically from transient pod failures

---

## 8. Constraints (Derived from sp.constitution)

| Category | Constraint |
|----------|------------|
| **Deployment Stack** | Docker, Minikube, Helm only |
| **AI DevOps Tools** | Gordon, kubectl-ai, kagent only |
| **Automation Mechanisms** | docker-fastapi skill, kubernetes skill only |
| **Operations** | Manual, undocumented Docker/Kubernetes/Helm operations are FORBIDDEN |
| **Application Code** | Phase 3 code MUST NOT be modified |

---

## 9. Success Criteria

Phase 4 is successful if:

- [ ] Users can deploy the system with `helm install` in under 5 minutes
- [ ] System remains functional after cluster restart
- [ ] Developers can reproduce deployment from repository alone
- [ ] Chat functionality works identically to Phase 3
- [ ] AI DevOps tools are demonstrably used in the workflow
- [ ] All deployment artifacts are version-controlled and traceable

---

## 10. Acceptance Criteria

Phase 4 is accepted if and only if:

- [ ] Frontend and backend are containerized with Docker
- [ ] Helm charts exist and deploy successfully
- [ ] System runs on Minikube
- [ ] `minikube delete && minikube start && helm install` reproduces the system
- [ ] kubectl-ai and kagent are demonstrably used
- [ ] No Phase 3 application code was modified
- [ ] No manual, undocumented infrastructure changes exist

---

## 11. Traceability Requirements

- This spec MUST be implemented via:
  - `plan.md` (architecture & deployment design)
  - `tasks.md` (implementation tasks)
- Every Dockerfile, Helm chart, and manifest MUST reference a Task ID
- All AI DevOps operations MUST be explainable via tasks

---

## 12. Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| AI-generated manifests require refinement | Medium | Low | Iterate via spec → plan → tasks → tool-mediated execution |
| Minikube resource limits cause pod scheduling issues | Medium | Medium | Document minimum resource requirements |
| Misconfigured services break frontend-backend connectivity | Medium | High | Define explicit service contracts in plan |
| External database (Neon) connectivity from Minikube | Low | High | Document network requirements, test early |

---

## 13. Assumptions

- Minikube is installed and functional on the development machine
- Docker Desktop is installed and running
- Neon PostgreSQL database from Phase 3 remains accessible
- Developer has sufficient local resources (CPU, memory) for Minikube
- AI DevOps tools (kubectl-ai, kagent, Gordon) are available

---

## 14. Exit Criteria

Phase 4 is complete when:

- The system is fully deployable on Minikube via Helm
- The deployment is reproducible from the repository alone
- All requirements and acceptance criteria are satisfied
- All artifacts are spec- and task-traceable
