# Feature Specification: Phase V Part B & C — Local and Cloud Kubernetes Deployment with Dapr

**Feature Branch**: `003-dapr-k8s-deployment`
**Created**: 2026-02-08
**Status**: Draft
**Input**: Phase V Part B (Local Minikube Deployment) and Part C (Cloud Kubernetes Deployment) — full Dapr runtime, Kafka-compatible Pub/Sub, Helm-based service deployment, CI/CD pipelines, monitoring, and cloud-grade infrastructure
**Constitution**: sp.constitution v4.0.0
**Scope**: Phase V — Part B and Part C only
**Depends On**: Phase V Part A (002-advanced-features-dapr) — feature logic and service code

## Governing Documents

This specification MUST comply with:

- sp.constitution v4.0.0
- Phase V Part A specification (002-advanced-features-dapr/spec.md)
- Phase II, III, IV artifacts (immutable contracts)
- Spec → Plan → Tasks → Code hierarchy

## Scope Boundary

**In Scope (Part B — Local Deployment):**

- Minikube cluster setup and validation
- Dapr runtime installation on local Kubernetes
- Kafka-compatible Pub/Sub deployment on local cluster (Redpanda or Strimzi)
- Helm chart creation and validation for all services (Chat API, Notification, Recurring Task, Audit)
- Dapr component manifests (Pub/Sub, State Store, Secrets) deployed to cluster
- Local end-to-end validation of stateless, event-driven behavior
- Container image builds for all services

**In Scope (Part C — Cloud Deployment):**

- Production-grade Kubernetes deployment on Azure AKS or Google GKE
- Full Dapr runtime on cloud Kubernetes
- Managed Kafka-compatible service (Confluent Cloud or Redpanda Cloud)
- CI/CD pipelines using GitHub Actions for build, test, and deploy
- Container registry setup and image push workflows
- Monitoring and logging configuration (health checks, structured logging)
- Secrets management for cloud environment
- Environment-specific Helm value overrides (local vs. cloud)

**Explicitly Out of Scope:**

- Feature logic implementation (covered by Part A)
- AI behavior rules (covered by constitution and Part A)
- Multi-region high availability (future phase)
- Custom domain and TLS certificate provisioning
- Cost optimization beyond basic resource sizing
- Performance load testing infrastructure

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Deploy Entire System Locally on Minikube (Priority: P1)

A developer wants to deploy the complete multi-service system — including Chat API, Notification Service, Recurring Task Service, and Audit Service — on a local Minikube cluster with Dapr and Kafka-compatible messaging. The developer runs a single set of Helm commands and the entire system comes up with all services communicating through Dapr Pub/Sub and the event bus operational.

**Why this priority**: Local deployment is the foundation for all development and testing. Without a working local cluster, cloud deployment cannot be validated. This story proves the complete system architecture works end-to-end.

**Independent Test**: Can be fully tested by running `minikube delete && minikube start`, installing Dapr and Kafka, deploying all Helm charts, and verifying services are healthy and events flow between them.

**Acceptance Scenarios**:

1. **Given** a fresh Minikube cluster with no prior state, **When** the developer follows the documented setup steps (install Dapr, deploy Kafka, deploy Helm charts), **Then** all services reach a healthy running state within 5 minutes.
2. **Given** all services are deployed, **When** querying each service's health endpoint, **Then** every service returns a healthy status.
3. **Given** all services are deployed with Dapr sidecars, **When** a task lifecycle event is triggered (e.g., task creation), **Then** the event flows through Dapr Pub/Sub and is received by subscribing services (Audit, Notification).
4. **Given** a fully deployed local cluster, **When** the developer runs `minikube delete && minikube start` and re-deploys, **Then** the system is fully restored from repository contents alone with no manual intervention.
5. **Given** a running pod is terminated, **When** Kubernetes restarts the pod, **Then** no application or workflow state is lost because all state is externalized.

---

### User Story 2 — Build and Push Container Images via CI/CD (Priority: P2)

A developer pushes code to the repository, and a CI/CD pipeline automatically builds container images for all services, runs basic validations, and pushes the images to a container registry ready for deployment.

**Why this priority**: Container images must exist before cloud deployment can happen. The CI/CD image build pipeline is a prerequisite for the cloud deployment story and ensures consistent, reproducible builds.

**Independent Test**: Can be fully tested by pushing a commit to the repository and verifying that the pipeline triggers, builds all service images, and pushes them to the configured container registry.

**Acceptance Scenarios**:

1. **Given** a code push to the main branch, **When** the CI/CD pipeline triggers, **Then** container images are built for all services (Chat API, Notification, Recurring Task, Audit).
2. **Given** the pipeline is building images, **When** the build completes, **Then** images are tagged with the commit SHA and pushed to the configured container registry.
3. **Given** a build fails for any service, **When** the failure is detected, **Then** the pipeline stops, reports the error clearly, and does not push partial images.
4. **Given** the pipeline configuration files, **When** reviewing repository contents, **Then** all pipeline definitions are stored in `.github/workflows/` and contain no plaintext secrets.

---

### User Story 3 — Deploy to Cloud Kubernetes via CI/CD (Priority: P3)

An operator wants to deploy the complete system to a cloud Kubernetes cluster (Azure AKS or Google GKE) with Dapr, managed Kafka, and all services running in a production-grade configuration. The deployment is triggered through a CI/CD pipeline with environment-specific configuration.

**Why this priority**: Cloud deployment is the ultimate deliverable for Part C. It validates that the local architecture translates to production infrastructure. This depends on both local validation (P1) and image builds (P2).

**Independent Test**: Can be fully tested by triggering the cloud deployment pipeline, verifying all services are healthy on the cloud cluster, and confirming events flow through the managed Kafka instance via Dapr Pub/Sub.

**Acceptance Scenarios**:

1. **Given** a cloud Kubernetes cluster with Dapr installed, **When** the deployment pipeline runs, **Then** all services are deployed with correct environment-specific configuration (managed Kafka endpoints, cloud database connection, secrets).
2. **Given** all services are deployed to cloud, **When** querying health endpoints from within the cluster, **Then** every service returns a healthy status.
3. **Given** all services are deployed with Dapr sidecars on cloud, **When** a task lifecycle event is triggered, **Then** the event flows through Dapr Pub/Sub over the managed Kafka instance and is received by subscribing services.
4. **Given** the cloud deployment pipeline, **When** a new version is deployed, **Then** the update is applied with zero-downtime using rolling updates.
5. **Given** the entire cloud environment, **When** rebuilding from repository plus CI/CD pipeline alone, **Then** the complete system is reproducible without any manual cloud console operations.

---

### User Story 4 — Monitor System Health and Logs in Production (Priority: P4)

An operator wants to monitor the health and behavior of all deployed services in the cloud environment, including structured log output, health check endpoints, and readiness probes, so that issues can be detected and diagnosed quickly.

**Why this priority**: Monitoring is essential for production operations but is additive — the system must first be deployable (P1-P3) before it can be monitored. This story ensures operational readiness.

**Independent Test**: Can be fully tested by deploying services and verifying that health endpoints respond correctly, structured logs are emitted to stdout/stderr, and Kubernetes probes report accurate service status.

**Acceptance Scenarios**:

1. **Given** a deployed service, **When** the service is healthy, **Then** the `/health` endpoint returns a success response and the `/readyz` endpoint confirms readiness.
2. **Given** a deployed service, **When** the service processes a request, **Then** structured log output is emitted to stdout/stderr with request context (timestamp, service name, request ID).
3. **Given** a service that fails its readiness check, **When** Kubernetes probes the readiness endpoint, **Then** the pod is removed from the service load balancer until it recovers.
4. **Given** a service that fails its liveness check, **When** Kubernetes probes the liveness endpoint, **Then** the pod is restarted automatically.
5. **Given** all services in the cloud cluster, **When** an operator reviews available monitoring data, **Then** health status, log output, and pod status are accessible without additional tooling beyond Kubernetes-native capabilities.

---

### Edge Cases

- What happens when Dapr sidecar injection fails for a service pod? The pod MUST NOT start in a degraded state; Kubernetes MUST report the failure and not route traffic to it.
- What happens when the Kafka-compatible broker is temporarily unreachable? Dapr MUST buffer or retry messages according to its configured policy; no events are silently dropped.
- What happens when a Helm chart deployment is interrupted mid-way? The system MUST be recoverable by re-running the Helm install/upgrade command.
- What happens when a CI/CD pipeline runs concurrently for multiple commits? The pipeline MUST handle concurrent runs safely (either queue or fail-fast for older runs).
- What happens when cloud Kubernetes node resources are exhausted? Pods MUST have resource requests/limits defined so Kubernetes can schedule and evict appropriately.
- What happens when secrets are rotated in the cloud environment? The deployment pipeline MUST support secret updates without requiring full redeployment of all services.
- What happens when minikube runs out of allocated resources? The documentation MUST specify minimum resource requirements for local deployment.

## Requirements *(mandatory)*

### Functional Requirements

**Part B — Local Deployment (Minikube):**

- **FR-001**: System MUST deploy on a single-node Minikube cluster that is disposable and rebuildable via `minikube delete && minikube start`.
- **FR-002**: Dapr runtime MUST be installed on the Minikube cluster with sidecar injection enabled for all application services.
- **FR-003**: A Kafka-compatible message broker MUST be deployed on the local cluster (Redpanda or Strimzi Kafka).
- **FR-004**: All services (Chat API, Notification, Recurring Task, Audit) MUST be deployable via Helm charts from the repository.
- **FR-005**: Dapr component manifests (Pub/Sub, State Store, Secrets) MUST be deployed to the cluster and correctly reference the local Kafka and database instances.
- **FR-006**: All services MUST start with Dapr sidecars injected and reach a healthy state.
- **FR-007**: Event-driven workflows (task events, reminders, recurring task creation, audit logging) MUST function end-to-end on the local cluster via Dapr Pub/Sub.
- **FR-008**: Container images for all services MUST be buildable locally and loadable into Minikube's image registry.
- **FR-009**: The local deployment MUST be fully reproducible from repository contents alone — no external state or manual configuration required.

**Part C — Cloud Deployment:**

- **FR-010**: System MUST deploy to a managed Kubernetes cluster (Azure AKS or Google GKE) via CI/CD pipeline.
- **FR-011**: Dapr runtime MUST be installed on the cloud Kubernetes cluster with sidecar injection enabled.
- **FR-012**: A managed Kafka-compatible service (Confluent Cloud or Redpanda Cloud) MUST be used for event messaging in the cloud environment.
- **FR-013**: Dapr component manifests MUST have environment-specific overrides for local vs. cloud (different broker endpoints, credentials, database connections).
- **FR-014**: All services MUST be deployed via Helm charts with environment-specific values files (local values vs. cloud values).
- **FR-015**: Container images MUST be built and pushed to a container registry via GitHub Actions CI/CD pipeline.
- **FR-016**: The CI/CD pipeline MUST support build, test, and deploy stages with clear separation.
- **FR-017**: Cloud deployments MUST use rolling updates for zero-downtime upgrades.
- **FR-018**: All secrets (database credentials, Kafka credentials, auth secrets) MUST be managed via Kubernetes Secrets or GitHub Actions Secrets — never in plaintext.

**Shared Requirements:**

- **FR-019**: Every service MUST expose `/health` and `/readyz` endpoints for liveness and readiness probes.
- **FR-020**: Every service MUST emit structured log output to stdout/stderr.
- **FR-021**: All Helm charts, Dapr component manifests, Dockerfiles, and CI/CD pipeline definitions MUST be versioned and stored in the repository.
- **FR-022**: All pods MUST have resource requests and limits defined in their Helm chart configurations.
- **FR-023**: The Helm chart structure MUST support environment-specific value overrides without chart modification.
- **FR-024**: No manual `kubectl`, `helm`, or cloud console changes are permitted — all operations MUST be scripted or pipelined.

### Key Entities

- **Helm Chart**: A packaged deployment unit for a single service, containing templates for Deployment, Service, ConfigMap, and Dapr annotations. Each service (Chat API, Notification, Recurring Task, Audit) has its own chart.
- **Dapr Component Manifest**: A configuration resource defining a Dapr building block (Pub/Sub, State Store, Secrets) with its backing infrastructure (Kafka, PostgreSQL, Kubernetes Secrets).
- **CI/CD Pipeline**: An automated workflow definition (GitHub Actions) that builds, tests, and deploys the system to cloud infrastructure.
- **Environment Configuration**: A set of Helm values and Dapr component overrides specific to a deployment target (local Minikube vs. cloud AKS/GKE).
- **Container Image**: A Docker image built from a service's Dockerfile, tagged with version/commit identifiers, and stored in a container registry.

### Assumptions

- The Part A feature code (002-advanced-features-dapr) is complete and working before Part B/C deployment begins. This spec only covers infrastructure and deployment.
- Minikube is already installed on the developer's machine or can be installed via documented prerequisites.
- For cloud deployment, the operator has an active cloud account (Azure or GCP) with permissions to create and manage Kubernetes clusters.
- The container registry for cloud deployment will be the cloud provider's native registry (Azure Container Registry or Google Container Registry / Artifact Registry).
- The managed Kafka service for cloud deployment requires manual one-time setup (account creation, cluster provisioning) documented as a prerequisite — the CI/CD pipeline manages topic creation and configuration.
- The Neon PostgreSQL database is external to both local and cloud clusters and accessible from both environments.
- Frontend deployment strategy (Vercel-hosted or in-cluster) is determined by Part A; this spec deploys whatever frontend configuration Part A defines.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A developer can deploy the complete multi-service system on Minikube from a fresh cluster in under 10 minutes using only documented commands from the repository.
- **SC-002**: After `minikube delete && minikube start`, the full system can be redeployed from repository contents alone with no external state or manual steps.
- **SC-003**: All 4 services (Chat API, Notification, Recurring Task, Audit) reach healthy status on the local cluster with Dapr sidecars attached.
- **SC-004**: Event-driven workflows function end-to-end on the local cluster — publishing a task event results in audit log entries and notification processing within 30 seconds.
- **SC-005**: The CI/CD pipeline builds and pushes container images for all services within 10 minutes of a code push.
- **SC-006**: The CI/CD pipeline deploys the complete system to cloud Kubernetes with zero-downtime rolling updates.
- **SC-007**: All services on the cloud cluster are healthy and event-driven workflows function through the managed Kafka service.
- **SC-008**: No plaintext secrets exist in repository files, container images, or pipeline definitions.
- **SC-009**: Every service responds to health and readiness probe endpoints, and Kubernetes correctly manages pod lifecycle based on probe results.
- **SC-010**: The cloud environment is fully reproducible from repository plus CI/CD pipeline — no manual cloud console operations are required for deployment.
