# Quickstart: Phase V Part A — Advanced Features & Event-Driven Architecture

**Branch**: `002-advanced-features-dapr` | **Date**: 2026-02-08

## Prerequisites

- Docker Desktop running
- Minikube installed and running (`minikube start`)
- Helm 3 installed
- Dapr CLI installed (`dapr init -k` for Kubernetes mode)
- kubectl configured for Minikube
- Neon PostgreSQL database provisioned (from Phase II)

## Step 1: Install Dapr on Minikube

```bash
# Install Dapr CLI (if not already installed)
# See: https://docs.dapr.io/getting-started/install-dapr-cli/

# Initialize Dapr in Kubernetes
dapr init -k --wait

# Verify Dapr is running
dapr status -k
kubectl get pods -n dapr-system
```

## Step 2: Deploy Redpanda (Kafka-Compatible)

```bash
# Add Redpanda Helm repo
helm repo add redpanda https://charts.redpanda.com
helm repo update

# Install single-node Redpanda for development
helm install redpanda redpanda/redpanda \
  --set statefulset.replicas=1 \
  --set resources.cpu.cores=0.5 \
  --set resources.memory.container.max=512Mi \
  --set storage.persistentVolume.size=2Gi \
  --set external.enabled=false \
  --set tls.enabled=false \
  --namespace default \
  --wait
```

## Step 3: Apply Dapr Components

```bash
kubectl apply -f dapr/components/pubsub.yaml
kubectl apply -f dapr/components/statestore.yaml
kubectl apply -f dapr/components/secrets.yaml
```

## Step 4: Build Service Images

```bash
# Build all service images for Minikube
eval $(minikube docker-env)

docker build -t todo-backend:latest backend/
docker build -t todo-frontend:latest frontend/
docker build -t notification-service:latest services/notification/
docker build -t recurring-service:latest services/recurring/
docker build -t audit-service:latest services/audit/
```

## Step 5: Deploy via Helm

```bash
# Deploy backend (Chat API + MCP)
helm upgrade --install todo-backend charts/todo-backend/ \
  --set image.tag=latest

# Deploy frontend
helm upgrade --install todo-frontend charts/todo-frontend/ \
  --set image.tag=latest

# Deploy new services
helm upgrade --install notification-service charts/notification-service/ \
  --set image.tag=latest

helm upgrade --install recurring-service charts/recurring-service/ \
  --set image.tag=latest

helm upgrade --install audit-service charts/audit-service/ \
  --set image.tag=latest
```

## Step 6: Verify Deployment

```bash
# Check all pods are running with Dapr sidecars
kubectl get pods

# Expected: each service pod has 2/2 containers (app + dapr sidecar)
# todo-backend-xxx         2/2   Running
# notification-service-xxx 2/2   Running
# recurring-service-xxx    2/2   Running
# audit-service-xxx        2/2   Running

# Check Dapr components
dapr components -k

# Check Dapr subscriptions
dapr configurations -k
```

## Step 7: Test Features

```bash
# Port-forward backend
kubectl port-forward svc/todo-backend 8000:8000

# Create a task with priority, tags, and due date
curl -X POST http://localhost:8000/api/{user_id}/tasks \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Weekly standup",
    "priority": "high",
    "tags": ["work", "meeting"],
    "due_at": "2026-02-15T09:00:00Z",
    "is_recurring": true,
    "recurrence_rule": "weekly"
  }'

# Set a reminder
curl -X POST http://localhost:8000/api/{user_id}/tasks/{task_id}/reminders \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"remind_at": "2026-02-14T09:00:00Z"}'

# Filter tasks by priority
curl "http://localhost:8000/api/{user_id}/tasks?priority=high&sort_by=due_at" \
  -H "Authorization: Bearer <token>"

# Search tasks
curl "http://localhost:8000/api/{user_id}/tasks?search=standup" \
  -H "Authorization: Bearer <token>"

# Check audit log
curl "http://localhost:8000/api/{user_id}/audit" \
  -H "Authorization: Bearer <token>"
```

## Step 8: Validate Event Flow

```bash
# Check notification service logs for reminder events
kubectl logs -l app=notification-service -c notification-service

# Check recurring service logs for task-completed events
kubectl logs -l app=recurring-service -c recurring-service

# Check audit service logs for all task events
kubectl logs -l app=audit-service -c audit-service

# Check Redpanda topics
kubectl exec -it redpanda-0 -- rpk topic list
kubectl exec -it redpanda-0 -- rpk topic consume task-events --num 5
```

## Clean Rebuild

```bash
# Full clean rebuild from repo
minikube delete
minikube start
dapr init -k --wait
# Then repeat Steps 2-6
```
