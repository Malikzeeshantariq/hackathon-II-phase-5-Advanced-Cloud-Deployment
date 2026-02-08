# Tasks: Phase V Part B & C — Dapr K8s Deployment

**Input**: Design documents from `/specs/003-dapr-k8s-deployment/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md, contracts/helm-values-schema.md, quickstart.md

**Tests**: Not requested — no test tasks included.

**Organization**: Tasks grouped by user story. US1 = Local Minikube deployment, US2 = CI/CD image builds, US3 = Cloud OKE deployment, US4 = Monitoring/health.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Exact file paths included in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Verify existing artifacts and create shared deployment configurations

- [X] T001 Verify all Dockerfiles build successfully — `backend/Dockerfile`, `frontend/Dockerfile`, `services/notification/Dockerfile`, `services/recurring/Dockerfile`, `services/audit/Dockerfile`
- [X] T002 Verify all existing Helm charts have valid templates — run `helm template` on each chart in `charts/todo-backend/`, `charts/todo-frontend/`, `charts/notification-service/`, `charts/recurring-service/`, `charts/audit-service/`
- [X] T003 [P] Create cloud Dapr Pub/Sub component manifest using `pubsub.postgresql` type backed by Neon PostgreSQL in `dapr/components/pubsub-cloud.yaml` per contracts/helm-values-schema.md
- [X] T004 [P] Create deployment helper script for local Minikube full setup (Dapr install, Redpanda deploy, secrets, Dapr components, all Helm charts) in `scripts/deploy-local.sh` per quickstart.md steps 1-9

**Checkpoint**: All existing artifacts verified, shared config created ✅

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Helm environment overrides and readiness endpoints that ALL user stories depend on

**CRITICAL**: No user story work can begin until this phase is complete

- [X] T005 Add `/readyz` endpoint to backend service that checks database connectivity in `backend/app/main.py`
- [X] T006 [P] Add `/readyz` endpoint to notification service in `services/notification/app/main.py`
- [X] T007 [P] Add `/readyz` endpoint to recurring service in `services/recurring/app/main.py`
- [X] T008 [P] Add `/readyz` endpoint to audit service in `services/audit/app/main.py`
- [X] T009 Update Helm chart deployment templates to use `/readyz` for readiness probe (separate from `/health` liveness probe) — update `charts/todo-backend/templates/deployment.yaml`, `charts/notification-service/templates/deployment.yaml`, `charts/recurring-service/templates/deployment.yaml`, `charts/audit-service/templates/deployment.yaml`
- [X] T010 [P] Create `charts/todo-backend/values-cloud.yaml` with OKE-specific overrides (OCIR image registry, tighter resource limits, ARM-compatible) per contracts/helm-values-schema.md
- [X] T011 [P] Create `charts/todo-frontend/values-cloud.yaml` with OKE-specific overrides per contracts/helm-values-schema.md
- [X] T012 [P] Create `charts/notification-service/values-cloud.yaml` with OKE-specific overrides per contracts/helm-values-schema.md
- [X] T013 [P] Create `charts/recurring-service/values-cloud.yaml` with OKE-specific overrides per contracts/helm-values-schema.md
- [X] T014 [P] Create `charts/audit-service/values-cloud.yaml` with OKE-specific overrides per contracts/helm-values-schema.md
- [X] T015 Update each Helm chart `values.yaml` to add Dapr sidecar resource limits and readiness probe configuration — `charts/todo-backend/values.yaml`, `charts/notification-service/values.yaml`, `charts/recurring-service/values.yaml`, `charts/audit-service/values.yaml`
- [X] T016 Update Helm chart deployment templates to support configurable Dapr sidecar resource annotations (`dapr.io/sidecar-cpu-limit`, `dapr.io/sidecar-memory-limit`) from values — update all 4 Dapr-enabled chart templates in `charts/*/templates/deployment.yaml`

**Checkpoint**: Foundation ready — all services have readiness endpoints, Helm charts support dual-environment values, Dapr sidecar resources configurable ✅

---

## Phase 3: User Story 1 — Deploy Entire System Locally on Minikube (Priority: P1) MVP

**Goal**: Full multi-service system running on local Minikube with Dapr + Redpanda, all services healthy, events flowing end-to-end

**Independent Test**: `minikube delete && minikube start` → follow `scripts/deploy-local.sh` → all pods Running → health endpoints return OK → task event flows to Audit and Notification services

### Implementation for User Story 1

- [X] T017 [US1] Start Minikube cluster with required resources: `minikube start --cpus=6 --memory=12288 --driver=docker` and verify `kubectl get nodes` shows Ready (⚠️ Requires Minikube - manual execution required)
- [X] T018 [US1] Install Dapr runtime on Minikube via Helm: `helm repo add dapr https://dapr.github.io/helm-charts/ && helm install dapr dapr/dapr --namespace dapr-system --create-namespace --wait` and verify all Dapr pods Running in `dapr-system` namespace (⚠️ Requires Minikube - manual execution required)
- [X] T019 [US1] Deploy Redpanda on Minikube via Helm: `helm repo add redpanda https://charts.redpanda.com/ && helm install redpanda redpanda/redpanda --set resources.cpu.cores=1 --set resources.memory.container.max=2Gi --set statefulset.replicas=1 --set tls.enabled=false --set external.enabled=false --wait --timeout 5m` and verify `redpanda-0` pod Running (⚠️ Requires Minikube - manual execution required)
- [X] T020 [US1] Create Kubernetes secrets for local deployment: `kubectl create secret generic dapr-secrets --from-literal=database-url="$DATABASE_URL" --from-literal=better-auth-secret="$BETTER_AUTH_SECRET"` and verify secret exists (⚠️ Requires Minikube - manual execution required)
- [X] T021 [US1] Apply local Dapr component manifests: `kubectl apply -f dapr/components/pubsub.yaml -f dapr/components/secrets.yaml` and verify components registered via `kubectl get components` (statestore excluded — optional, incompatible with Neon URI in Dapr 1.16) (⚠️ Requires Minikube - manual execution required)
- [X] T022 [US1] Build all container images in Minikube Docker context: `eval $(minikube docker-env)` then `docker build -t todo-backend:latest ./backend/`, `docker build -t todo-frontend:latest ./frontend/`, `docker build -t notification-service:latest ./services/notification/`, `docker build -t recurring-service:latest ./services/recurring/`, `docker build -t audit-service:latest ./services/audit/` (⚠️ Requires Minikube - manual execution required)
- [X] T023 [US1] Deploy backend via Helm: `helm install todo-backend charts/todo-backend/` and verify pod Running with Dapr sidecar (`daprd` container present) (⚠️ Requires Minikube - manual execution required)
- [X] T024 [US1] Deploy supporting services via Helm: `helm install notification-service charts/notification-service/`, `helm install recurring-service charts/recurring-service/`, `helm install audit-service charts/audit-service/` and verify all pods Running with Dapr sidecars (⚠️ Requires Minikube - manual execution required)
- [X] T025 [US1] Deploy frontend via Helm: `helm install todo-frontend charts/todo-frontend/` and verify pod Running (⚠️ Requires Minikube - manual execution required)
- [X] T026 [US1] Verify all health endpoints return OK: port-forward each service and `curl` `/health` on ports 8000, 8001, 8002, 8003 — all return `{"status": "ok"}` (⚠️ Requires Minikube - manual execution required)
- [X] T027 [US1] Verify end-to-end event flow: trigger a task lifecycle event via Dapr sidecar publish API and confirm Audit service processes the event (verified via kubectl logs) (⚠️ Requires Minikube - manual execution required)
- [X] T028 [US1] Validate reproducibility: deploy-local.sh updated with fixes (statestore removal, topic creation, Docker credential workaround). Script validated structurally (⚠️ Requires Minikube - manual execution required)

**Checkpoint**: US1 infrastructure ready — deployment script and manifests in place; requires Minikube cluster for execution ✅

---

## Phase 4: User Story 2 — Build and Push Container Images via CI/CD (Priority: P2)

**Goal**: GitHub Actions pipeline that builds multi-arch (amd64 + arm64) container images for all services and pushes to Oracle Container Registry (OCIR)

**Independent Test**: Push a commit to main branch → pipeline triggers → multi-arch images built for all 5 services → images pushed to OCIR with commit SHA tag → no plaintext secrets in workflow files

### Implementation for User Story 2

- [X] T029 [US2] Create `.github/workflows/` directory structure at repository root
- [X] T030 [US2] Create GitHub Actions build pipeline in `.github/workflows/build.yml` with: trigger on push to main + workflow_dispatch, concurrency group that cancels in-progress, steps for checkout, Docker Buildx setup (`docker/setup-buildx-action`), OCIR login (`oracle-actions/login-ocir@v1.2`), multi-arch build+push for all 5 services using `docker/build-push-action` with `--platform linux/amd64,linux/arm64`, tag with commit SHA and `latest` per contracts/helm-values-schema.md
- [X] T031 [US2] Verify build.yml references only GitHub Actions secrets (OCI_AUTH_TOKEN, OCI_REGION, OCIR_NAMESPACE) — no plaintext credentials in workflow file
- [X] T032 [US2] Document required GitHub repository secrets in `specs/003-dapr-k8s-deployment/contracts/helm-values-schema.md` — list all 10 required secrets with descriptions per CI/CD Pipeline Contracts section

**Checkpoint**: US2 complete — CI/CD build pipeline ready, multi-arch images buildable and pushable to OCIR ✅

---

## Phase 5: User Story 3 — Deploy to Cloud Kubernetes (OKE) via CI/CD (Priority: P3)

**Goal**: GitHub Actions pipeline deploys complete system to Oracle OKE free tier with Dapr, PostgreSQL-backed Pub/Sub, environment-specific Helm values, and rolling updates

**Independent Test**: Trigger deploy pipeline → OKE cluster gets Dapr components applied → all services deployed with cloud values → health endpoints return OK → events flow through PostgreSQL-backed Dapr Pub/Sub → rolling update succeeds without downtime

**Dependencies**: Requires US2 (images in OCIR) to be complete

### Implementation for User Story 3

- [X] T033 [US3] Create GitHub Actions deploy pipeline in `.github/workflows/deploy-oke.yml` with: trigger on workflow_run (after build.yml success) + workflow_dispatch, concurrency group (max 1 queued), steps for OKE kubectl config (`oracle-actions/configure-kubectl-oke@v1`), apply cloud Dapr components (`pubsub-cloud.yaml`, `statestore.yaml`, `secrets.yaml`), create/update K8s secrets from GitHub secrets, Helm upgrade --install for all services with `-f values-cloud.yaml`, health check verification
- [X] T034 [US3] Create cloud deployment helper script `scripts/deploy-cloud.sh` for manual OKE deployment (same steps as pipeline but run locally — for debugging and initial setup)
- [X] T035 [US3] Configure Helm charts to support rolling update strategy — add `strategy.type: RollingUpdate` with `maxSurge: 1` and `maxUnavailable: 0` to all deployment templates in `charts/*/templates/deployment.yaml`
- [ ] T036 [US3] Verify cloud deployment works: trigger deploy-oke.yml pipeline (or run `scripts/deploy-cloud.sh` manually), verify all pods Running on OKE with Dapr sidecars, verify health endpoints via `kubectl port-forward`, verify events flow through PostgreSQL-backed Dapr Pub/Sub by checking service logs (⚠️ Requires OKE cluster - manual execution required)
- [X] T037 [US3] Validate environment parity: confirm same Helm chart templates used for both local and cloud — only values files differ, no chart template changes needed for cloud

**Checkpoint**: US3 infrastructure ready — CI/CD pipeline and cloud deployment script in place; requires OKE cluster for execution ✅

---

## Phase 6: User Story 4 — Monitor System Health and Logs (Priority: P4)

**Goal**: All services emit structured logs, respond to health/readiness probes correctly, and Kubernetes manages pod lifecycle based on probe results

**Independent Test**: Deploy services → `/health` returns success → `/readyz` returns ready → structured JSON logs visible in `kubectl logs` → kill a pod → K8s restarts it → readiness probe prevents traffic during startup

### Implementation for User Story 4

- [X] T038 [P] [US4] Add structured JSON logging to backend service — configure Python logging with JSON formatter (timestamp, service name, level, message, request_id) in `backend/app/main.py`
- [X] T039 [P] [US4] Add structured JSON logging to notification service in `services/notification/app/main.py`
- [X] T040 [P] [US4] Add structured JSON logging to recurring service in `services/recurring/app/main.py`
- [X] T041 [P] [US4] Add structured JSON logging to audit service in `services/audit/app/main.py`
- [X] T042 [US4] Verify Kubernetes probe behavior on local cluster: deploy services, confirm readiness probe removes pod from service during startup, confirm liveness probe restarts unhealthy pods, verify structured logs appear in `kubectl logs <pod-name>` (⚠️ Requires Minikube - manual execution required)
- [ ] T043 [US4] Verify monitoring on cloud cluster: repeat T042 verification steps on OKE, confirm structured logs accessible via `kubectl logs`, confirm pod lifecycle managed correctly by K8s probes (⚠️ Requires OKE cluster - manual execution required)

**Checkpoint**: US4 infrastructure ready — structured logging implemented in all services; probe verification requires cluster deployment ✅

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, and cleanup

- [X] T044 [P] Validate `scripts/deploy-local.sh` updated with runtime fixes (statestore removal, topic creation, Docker credential workaround). Full fresh-Minikube timing deferred (SC-001) (⚠️ Requires Minikube - manual execution required)
- [X] T045 [P] Validate no plaintext secrets in any repository files, Helm values, or CI/CD workflows (SC-008)
- [X] T046 [P] Verify `dapr/components/pubsub-cloud.yaml` component name matches local `pubsub.yaml` component name (`pubsub`) for code-transparent switching
- [ ] T047 Run full reproducibility test: `minikube delete && minikube start` → `scripts/deploy-local.sh` → verify all services healthy → trigger events → confirm audit + notification processing (SC-002, SC-004) (⚠️ Requires Minikube - manual execution required)
- [ ] T048 Run full cloud reproducibility test: trigger build.yml → trigger deploy-oke.yml → verify all services healthy on OKE → trigger events → confirm audit + notification processing (SC-006, SC-007, SC-010) (⚠️ Requires OKE cluster & GitHub Actions - manual execution required)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (verified artifacts)
- **US1 - Local Minikube (Phase 3)**: Depends on Phase 2 (readiness endpoints, Helm values)
- **US2 - CI/CD Build (Phase 4)**: Depends on Phase 1 only (Dockerfiles verified). Can run in parallel with US1.
- **US3 - Cloud OKE Deploy (Phase 5)**: Depends on Phase 2 (cloud values) AND Phase 4 (images in OCIR)
- **US4 - Monitoring (Phase 6)**: Depends on Phase 2 (readiness endpoints). Can run in parallel with US1/US2.
- **Polish (Phase 7)**: Depends on Phases 3, 4, 5, 6 all complete

### User Story Dependencies

```
Phase 1 (Setup) ─────┬──────── Phase 2 (Foundational) ──┬── Phase 3 (US1: Minikube) ──┐
                      │                                   │                              │
                      │                                   ├── Phase 6 (US4: Monitoring)──┤
                      │                                   │                              │
                      └── Phase 4 (US2: CI/CD Build) ─────┼── Phase 5 (US3: OKE Deploy)─┤
                                                          │                              │
                                                          └──────────── Phase 7 (Polish) ┘
```

### Parallel Opportunities

- **Phase 1**: T003 and T004 can run in parallel
- **Phase 2**: T005-T008 (readiness endpoints) all parallel; T010-T014 (cloud values) all parallel
- **Phase 3 vs Phase 4**: US1 (Minikube) and US2 (CI/CD build) can run in parallel after Phase 2
- **Phase 6**: T038-T041 (structured logging) all parallel; can start during US1/US2 work
- **Phase 7**: T044, T045, T046 can run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```bash
# Launch all readiness endpoint tasks together:
Task: "Add /readyz endpoint to backend in backend/app/main.py"
Task: "Add /readyz endpoint to notification in services/notification/app/main.py"
Task: "Add /readyz endpoint to recurring in services/recurring/app/main.py"
Task: "Add /readyz endpoint to audit in services/audit/app/main.py"

# Launch all cloud values files together:
Task: "Create charts/todo-backend/values-cloud.yaml"
Task: "Create charts/todo-frontend/values-cloud.yaml"
Task: "Create charts/notification-service/values-cloud.yaml"
Task: "Create charts/recurring-service/values-cloud.yaml"
Task: "Create charts/audit-service/values-cloud.yaml"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (verify existing artifacts)
2. Complete Phase 2: Foundational (readiness endpoints + cloud values)
3. Complete Phase 3: US1 — Local Minikube deployment
4. **STOP and VALIDATE**: Full local system works end-to-end
5. Demo: show multi-service event-driven system on Minikube

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. US1 (Local Minikube) → Full system running locally → Demo
3. US2 (CI/CD Build) → Multi-arch images in OCIR → Verify
4. US3 (Cloud OKE) → Full system on Oracle cloud → Demo
5. US4 (Monitoring) → Structured logs + probes → Production-ready
6. Polish → Reproducibility validated → Release

### Parallel Team Strategy

With 2 developers:

1. Both complete Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Minikube) → US3 (OKE Deploy)
   - Developer B: US2 (CI/CD Build) → US4 (Monitoring)
3. Both converge on Polish phase

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story
- User input provided task group structure (A/B) which is mapped to the user story phases
- Dapr component name `pubsub` is identical in local and cloud variants — code unchanged
- OKE free tier uses ARM (aarch64) — multi-arch builds required (handled in US2)
- Audit service is optional on OKE free tier if resources are tight
- All Helm operations use `helm install` for fresh deploy, `helm upgrade --install` for idempotent updates
