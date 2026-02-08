# Data Model: Phase V Part B & C — Infrastructure Entities

**Branch**: `003-dapr-k8s-deployment` | **Date**: 2026-02-08

This data model describes infrastructure entities — not application data entities (those are defined in Part A). These entities represent the deployment artifacts and configuration that make up the system.

## Helm Chart Entity

Represents a single service's deployment package.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Chart name (e.g., `todo-backend`) |
| version | semver | Chart version (e.g., `0.1.0`) |
| appVersion | string | Application version |
| service_port | integer | Container port the service listens on |
| service_type | enum | `ClusterIP` or `NodePort` |
| replicas | integer | Number of pod replicas (default: 1) |
| image.repository | string | Container image name |
| image.tag | string | Image tag (commit SHA or `latest`) |
| resources.requests.cpu | string | CPU request (e.g., `100m`) |
| resources.requests.memory | string | Memory request (e.g., `256Mi`) |
| resources.limits.cpu | string | CPU limit (e.g., `500m`) |
| resources.limits.memory | string | Memory limit (e.g., `512Mi`) |
| dapr.enabled | boolean | Whether Dapr sidecar is injected |
| dapr.appId | string | Dapr application identifier |
| dapr.appPort | integer | Port Dapr forwards traffic to |
| healthCheck.path | string | Liveness probe path (default: `/health`) |
| readinessCheck.path | string | Readiness probe path (default: `/readyz`) |

**Relationships**: Each Helm Chart deploys exactly one Service. Charts reference Environment Configuration for value overrides.

**Instances**: todo-backend, todo-frontend, notification-service, recurring-service, audit-service

---

## Dapr Component Entity

Represents a Dapr building block configuration.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Component name (e.g., `pubsub`) |
| type | string | Dapr component type (e.g., `pubsub.kafka`, `pubsub.postgresql`) |
| version | string | Component API version (e.g., `v1`) |
| metadata | map | Key-value configuration (broker address, credentials, etc.) |
| environment | enum | `local` or `cloud` — determines which variant is applied |

**Relationships**: Components are referenced by Services via Dapr sidecar. Pub/Sub components are backed by Redpanda (local) or PostgreSQL (cloud). State Store is backed by Neon PostgreSQL in both environments.

**Instances**: pubsub (local), pubsub-cloud (cloud), statestore (shared), kubernetes-secrets (shared)

---

## CI/CD Pipeline Entity

Represents a GitHub Actions workflow.

| Field | Type | Description |
|-------|------|-------------|
| name | string | Workflow name |
| trigger | object | Events that trigger the workflow (push, workflow_dispatch, workflow_run) |
| concurrency | object | Concurrency group and cancel policy |
| stages | list | Ordered list of jobs (build, push, deploy) |
| secrets | list | Required GitHub Actions secrets |
| artifacts | list | Outputs (container images, deployment status) |

**Relationships**: Build pipeline produces Container Images consumed by Deploy pipeline. Deploy pipeline applies Helm Charts to OKE cluster.

**Instances**: build.yml (build + push), deploy-oke.yml (deploy to OKE)

---

## Environment Configuration Entity

Represents the difference between deployment targets.

| Field | Type | Description |
|-------|------|-------------|
| name | enum | `local` or `cloud` |
| values_file | string | Helm values override file name |
| dapr_pubsub | string | Which pubsub component to apply |
| image_registry | string | Container image registry |
| image_load_method | enum | `minikube image load` or `docker push` |
| secrets_source | string | How secrets are created |
| resource_profile | enum | `generous` (local) or `constrained` (cloud) |

| Property | Local (Minikube) | Cloud (OKE) |
|----------|-----------------|-------------|
| values_file | `values.yaml` (defaults) | `values-cloud.yaml` |
| dapr_pubsub | `pubsub.yaml` (Kafka/Redpanda) | `pubsub-cloud.yaml` (PostgreSQL) |
| image_registry | Minikube local | `<region>.ocir.io/<namespace>` |
| image_load_method | `minikube image load` | `docker push` (via CI/CD) |
| secrets_source | `kubectl create secret` (manual) | GitHub Actions → `kubectl` |
| resource_profile | generous | constrained (ARM free tier) |

---

## Container Image Entity

Represents a built Docker image.

| Field | Type | Description |
|-------|------|-------------|
| service | string | Which service this image contains |
| dockerfile_path | string | Path to Dockerfile |
| platforms | list | Target architectures (`linux/amd64`, `linux/arm64`) |
| registry | string | Where the image is stored |
| tag | string | Version tag (commit SHA) |
| base_image | string | Base Docker image used |

**Instances**:

| Service | Dockerfile | Port | Base Image |
|---------|-----------|------|------------|
| todo-backend | `backend/Dockerfile` | 8000 | python:3.11-slim |
| todo-frontend | `frontend/Dockerfile` | 3000 | node:20-alpine |
| notification-service | `services/notification/Dockerfile` | 8001 | python:3.11-slim |
| recurring-service | `services/recurring/Dockerfile` | 8002 | python:3.11-slim |
| audit-service | `services/audit/Dockerfile` | 8003 | python:3.11-slim |
