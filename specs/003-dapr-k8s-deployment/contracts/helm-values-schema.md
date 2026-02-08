# Helm Values Contract: Environment-Specific Configuration

**Branch**: `003-dapr-k8s-deployment` | **Date**: 2026-02-08

## values.yaml (Defaults — Local Minikube)

All charts use `values.yaml` as the default. These values work for local Minikube deployment without any overrides.

### Backend (todo-backend/values.yaml)

```yaml
replicaCount: 1

image:
  repository: todo-backend
  tag: latest
  pullPolicy: IfNotPresent    # Local images don't need pull

service:
  type: ClusterIP
  port: 8000

resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 500m
    memory: 512Mi

dapr:
  enabled: true
  appId: todo-backend
  appPort: 8000
  enableApiLogging: true
  sidecar:
    cpuLimit: "200m"
    memoryLimit: "256Mi"

probes:
  liveness:
    path: /health
    initialDelaySeconds: 10
    periodSeconds: 10
  readiness:
    path: /readyz
    initialDelaySeconds: 10
    periodSeconds: 10

env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: dapr-secrets
        key: database-url
  - name: BETTER_AUTH_SECRET
    valueFrom:
      secretKeyRef:
        name: dapr-secrets
        key: better-auth-secret
  - name: CORS_ORIGINS
    value: "http://localhost:3000"
```

### Microservices (notification, recurring, audit — shared pattern)

```yaml
replicaCount: 1

image:
  repository: <service-name>
  tag: latest
  pullPolicy: IfNotPresent

service:
  type: ClusterIP
  port: <service-port>      # 8001, 8002, 8003

resources:
  requests:
    cpu: 50m
    memory: 128Mi
  limits:
    cpu: 250m
    memory: 256Mi

dapr:
  enabled: true
  appId: <service-name>
  appPort: <service-port>
  enableApiLogging: true
  sidecar:
    cpuLimit: "100m"
    memoryLimit: "128Mi"

probes:
  liveness:
    path: /health
    initialDelaySeconds: 10
    periodSeconds: 10
  readiness:
    path: /readyz
    initialDelaySeconds: 10
    periodSeconds: 10

env:
  - name: DATABASE_URL
    valueFrom:
      secretKeyRef:
        name: dapr-secrets
        key: database-url
```

---

## values-cloud.yaml (OKE Free Tier Overrides)

These files override the defaults for cloud deployment. Only changed values need to be specified.

### Backend (todo-backend/values-cloud.yaml)

```yaml
image:
  repository: <region>.ocir.io/<namespace>/todo-backend
  tag: <commit-sha>
  pullPolicy: Always          # Always pull from registry

resources:
  requests:
    cpu: 100m
    memory: 256Mi
  limits:
    cpu: 300m                 # Tighter limits for free tier
    memory: 384Mi

dapr:
  sidecar:
    cpuLimit: "100m"          # Reduced for free tier
    memoryLimit: "128Mi"

env:
  - name: CORS_ORIGINS
    value: "*"                # Allow all origins for demo
```

### Microservices (notification, recurring, audit — cloud overrides)

```yaml
image:
  repository: <region>.ocir.io/<namespace>/<service-name>
  tag: <commit-sha>
  pullPolicy: Always

resources:
  requests:
    cpu: 50m
    memory: 128Mi
  limits:
    cpu: 150m                 # Tighter for free tier
    memory: 192Mi

dapr:
  sidecar:
    cpuLimit: "50m"
    memoryLimit: "96Mi"
```

---

## Dapr Component Contracts

### pubsub.yaml (Local — Kafka/Redpanda)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      value: "redpanda.default.svc.cluster.local:9093"
    - name: consumerGroup
      value: "{appId}-group"
    - name: authType
      value: "none"
    - name: initialOffset
      value: "oldest"
```

### pubsub-cloud.yaml (Cloud — PostgreSQL)

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.postgresql
  version: v1
  metadata:
    - name: connectionString
      secretKeyRef:
        name: dapr-secrets
        key: database-url
```

**Note**: Both components are named `pubsub` so application code references the same component name regardless of environment. Only the backing implementation changes.

---

## CI/CD Pipeline Contracts

### Required GitHub Secrets

| Secret Name | Description | Used By |
|-------------|-------------|---------|
| OCI_AUTH_TOKEN | OCI auth token for OCIR login | build.yml |
| OCI_TENANCY | OCI tenancy OCID | deploy-oke.yml |
| OCI_USER | OCI user OCID | deploy-oke.yml |
| OCI_FINGERPRINT | OCI API key fingerprint | deploy-oke.yml |
| OCI_KEY_CONTENT | OCI API private key (base64) | deploy-oke.yml |
| OCI_REGION | OCI region (e.g., `us-ashburn-1`) | build.yml, deploy-oke.yml |
| OKE_CLUSTER_ID | OKE cluster OCID | deploy-oke.yml |
| OCIR_NAMESPACE | OCIR tenancy namespace | build.yml |
| DATABASE_URL | Neon PostgreSQL connection string | deploy-oke.yml |
| BETTER_AUTH_SECRET | Auth secret key | deploy-oke.yml |

### Pipeline Trigger Contract

| Pipeline | Trigger | Concurrency |
|----------|---------|-------------|
| build.yml | `push` to `main` or `workflow_dispatch` | Cancel in-progress for same ref |
| deploy-oke.yml | `workflow_run` (after build.yml success) or `workflow_dispatch` | Queue (max 1 concurrent) |
