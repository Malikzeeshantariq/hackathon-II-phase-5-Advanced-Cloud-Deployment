# Quickstart: Local Deployment on Minikube

**Branch**: `003-dapr-k8s-deployment` | **Date**: 2026-02-08

## Prerequisites

- Docker Desktop (running)
- Minikube 1.32+ installed
- Helm 3.10+ installed
- Dapr CLI 1.14+ installed
- kubectl installed
- Minimum system resources: **6 CPUs, 12GB RAM** available for Minikube

## Step 1: Start Minikube

```bash
minikube delete  # Clean slate (optional)
minikube start --cpus=6 --memory=12288 --driver=docker
```

Verify:
```bash
kubectl get nodes
# Should show 1 node in Ready state
```

## Step 2: Install Dapr Runtime

```bash
helm repo add dapr https://dapr.github.io/helm-charts/
helm repo update
helm install dapr dapr/dapr --namespace dapr-system --create-namespace --wait
```

Verify:
```bash
kubectl get pods -n dapr-system
# Should show dapr-operator, dapr-sentry, dapr-placement all Running
```

## Step 3: Deploy Redpanda (Kafka-Compatible Broker)

```bash
helm repo add redpanda https://charts.redpanda.com/
helm repo update
helm install redpanda redpanda/redpanda \
  --namespace default \
  --set resources.cpu.cores=1 \
  --set resources.memory.container.max=2Gi \
  --set statefulset.replicas=1 \
  --set tls.enabled=false \
  --set external.enabled=false \
  --wait --timeout 5m
```

Verify:
```bash
kubectl get pods -l app.kubernetes.io/name=redpanda
# Should show redpanda-0 Running
```

## Step 4: Create Kubernetes Secrets

```bash
kubectl create secret generic dapr-secrets \
  --from-literal=database-url="$DATABASE_URL" \
  --from-literal=better-auth-secret="$BETTER_AUTH_SECRET"
```

## Step 5: Apply Dapr Components

```bash
kubectl apply -f dapr/components/pubsub.yaml
kubectl apply -f dapr/components/statestore.yaml
kubectl apply -f dapr/components/secrets.yaml
```

Verify:
```bash
kubectl get components
# Should show pubsub, statestore, kubernetes-secrets
```

## Step 6: Build and Load Container Images

```bash
# Use Minikube's Docker daemon
eval $(minikube docker-env)

# Build all service images
docker build -t todo-backend:latest ./backend/
docker build -t todo-frontend:latest ./frontend/
docker build -t notification-service:latest ./services/notification/
docker build -t recurring-service:latest ./services/recurring/
docker build -t audit-service:latest ./services/audit/
```

## Step 7: Deploy Services via Helm

```bash
# Deploy backend first (other services may depend on it)
helm install todo-backend charts/todo-backend/

# Deploy supporting services
helm install notification-service charts/notification-service/
helm install recurring-service charts/recurring-service/
helm install audit-service charts/audit-service/

# Deploy frontend last
helm install todo-frontend charts/todo-frontend/
```

## Step 8: Verify Deployment

```bash
# Check all pods are running
kubectl get pods

# Check health endpoints
kubectl port-forward svc/todo-backend 8000:8000 &
curl http://localhost:8000/health
# Expected: {"status": "ok"}

kubectl port-forward svc/notification-service 8001:8001 &
curl http://localhost:8001/health
# Expected: {"status": "ok", "service": "notification-service"}

kubectl port-forward svc/recurring-service 8002:8002 &
curl http://localhost:8002/health
# Expected: {"status": "ok", "service": "recurring-service"}

kubectl port-forward svc/audit-service 8003:8003 &
curl http://localhost:8003/health
# Expected: {"status": "ok", "service": "audit-service"}
```

## Step 9: Access Frontend

```bash
minikube service todo-frontend --url
# Open the returned URL in browser
```

## Teardown

```bash
# Remove all services
helm uninstall todo-frontend todo-backend notification-service recurring-service audit-service

# Remove Redpanda
helm uninstall redpanda

# Remove Dapr
helm uninstall dapr -n dapr-system

# Or destroy entire cluster
minikube delete
```

## Troubleshooting

**Pods stuck in CrashLoopBackOff**:
- Check logs: `kubectl logs <pod-name> -c <container-name>`
- Check Dapr sidecar: `kubectl logs <pod-name> -c daprd`
- Verify secrets exist: `kubectl get secrets`

**Dapr components not connecting**:
- Verify Redpanda is running: `kubectl get pods -l app.kubernetes.io/name=redpanda`
- Check component status: `kubectl get components`
- Check Dapr logs: `kubectl logs -n dapr-system -l app=dapr-operator`

**Resource issues**:
- Check node resources: `kubectl top nodes`
- Check pod resources: `kubectl top pods`
- Increase Minikube resources: `minikube start --cpus=8 --memory=16384`
