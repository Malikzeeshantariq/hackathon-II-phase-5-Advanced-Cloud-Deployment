# Dapr Component Contracts: Phase V Part A

**Branch**: `002-advanced-features-dapr` | **Date**: 2026-02-08 | **Phase**: 1

---

## 1. Pub/Sub Component (Kafka via Redpanda)

**File**: `dapr/components/pubsub.yaml`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
  namespace: default
spec:
  type: pubsub.kafka
  version: v1
  metadata:
    - name: brokers
      value: "redpanda.default.svc.cluster.local:9092"
    - name: consumerGroup
      value: "{app-id}-group"
    - name: authType
      value: "none"
    - name: initialOffset
      value: "oldest"
```

**Topics Created**:
- `task-events`
- `reminders`
- `task-updates`

---

## 2. State Store Component (PostgreSQL)

**File**: `dapr/components/statestore.yaml`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
  namespace: default
spec:
  type: state.postgresql
  version: v1
  metadata:
    - name: connectionString
      secretKeyRef:
        name: dapr-secrets
        key: database-url
```

**Usage**: Optional cached state for conversation context and task snapshots.

---

## 3. Secrets Component (Kubernetes)

**File**: `dapr/components/secrets.yaml`

```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kubernetes-secrets
  namespace: default
spec:
  type: secretstores.kubernetes
  version: v1
  metadata: []
```

**Secrets Managed**:
- `database-url`: Neon PostgreSQL connection string
- `better-auth-secret`: JWT signing secret
- `openai-api-key`: LLM API key

---

## 4. Dapr Sidecar Annotations (Helm)

Each service Helm chart MUST include these annotations in the deployment template:

```yaml
annotations:
  dapr.io/enabled: "true"
  dapr.io/app-id: "<service-app-id>"
  dapr.io/app-port: "<service-port>"
  dapr.io/enable-api-logging: "true"
```

**App IDs**:
| Service              | App ID                | Port |
|----------------------|-----------------------|------|
| Backend (Chat API)   | `todo-backend`        | 8000 |
| Notification Service | `notification-service`| 8001 |
| Recurring Service    | `recurring-service`   | 8002 |
| Audit Service        | `audit-service`       | 8003 |

---

## 5. Dapr Subscriptions

Each consuming service declares subscriptions via programmatic API or config:

**Notification Service** subscribes to:
```yaml
- pubsubname: pubsub
  topic: reminders
  route: /events/reminders
```

**Recurring Task Service** subscribes to:
```yaml
- pubsubname: pubsub
  topic: task-events
  route: /events/task-events
```

**Audit Service** subscribes to:
```yaml
- pubsubname: pubsub
  topic: task-events
  route: /events/task-events
```
