#!/usr/bin/env bash
# T004: Local Minikube full deployment script
# Spec Reference: specs/003-dapr-k8s-deployment/quickstart.md
# Plan Reference: plan.md - Deployment Order
#
# Usage: ./scripts/deploy-local.sh
# Prerequisites: minikube, helm, kubectl installed
# Minimum resources: 6 CPUs, 12GB RAM

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Phase V Part B: Local Minikube Deployment ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# Step 1: Verify Minikube is running
echo "[1/9] Verifying Minikube cluster..."
if ! kubectl get nodes &>/dev/null; then
    echo "ERROR: Minikube cluster not running. Start with:"
    echo "  minikube start --cpus=6 --memory=12288 --driver=docker"
    exit 1
fi
echo "  Cluster ready: $(kubectl get nodes -o name)"

# Step 2: Install Dapr runtime
echo "[2/9] Installing Dapr runtime..."
helm repo add dapr https://dapr.github.io/helm-charts/ 2>/dev/null || true
helm repo update dapr
if helm status dapr -n dapr-system &>/dev/null; then
    echo "  Dapr already installed, upgrading..."
    helm upgrade dapr dapr/dapr --namespace dapr-system --wait
else
    helm install dapr dapr/dapr --namespace dapr-system --create-namespace --wait
fi
echo "  Dapr installed. Pods:"
kubectl get pods -n dapr-system --no-headers

# Step 3: Deploy Redpanda (Kafka-compatible broker)
echo "[3/9] Deploying Redpanda..."
helm repo add redpanda https://charts.redpanda.com/ 2>/dev/null || true
helm repo update redpanda
if helm status redpanda &>/dev/null; then
    echo "  Redpanda already installed, upgrading..."
    helm upgrade redpanda redpanda/redpanda \
        --set resources.cpu.cores=1 \
        --set resources.memory.container.max=2Gi \
        --set statefulset.replicas=1 \
        --set tls.enabled=false \
        --set external.enabled=false \
        --wait --timeout 5m
else
    helm install redpanda redpanda/redpanda \
        --set resources.cpu.cores=1 \
        --set resources.memory.container.max=2Gi \
        --set statefulset.replicas=1 \
        --set tls.enabled=false \
        --set external.enabled=false \
        --wait --timeout 5m
fi
echo "  Redpanda deployed."

# Step 4: Create Kubernetes secrets
echo "[4/9] Creating Kubernetes secrets..."
if [ -z "${DATABASE_URL:-}" ]; then
    echo "ERROR: DATABASE_URL environment variable not set."
    echo "  Export it before running: export DATABASE_URL='postgresql://...'"
    exit 1
fi
kubectl delete secret dapr-secrets --ignore-not-found
kubectl create secret generic dapr-secrets \
    --from-literal=database-url="$DATABASE_URL" \
    --from-literal=better-auth-secret="${BETTER_AUTH_SECRET:-changeme-local-dev-secret}"
echo "  Secrets created."

# Step 5: Apply Dapr component manifests (local variants)
echo "[5/9] Applying Dapr components (local)..."
kubectl apply -f "$PROJECT_ROOT/dapr/components/pubsub.yaml"
kubectl apply -f "$PROJECT_ROOT/dapr/components/secrets.yaml"
# Note: statestore.yaml is excluded — state store is optional (architecture decision R-004)
# and its connection string parsing is incompatible with Neon URI format in Dapr 1.16.x
echo "  Dapr components applied."

# Step 5b: Create Redpanda topics
echo "  Creating Redpanda topics..."
kubectl wait --for=condition=ready pod/redpanda-0 --timeout=120s 2>/dev/null || true
kubectl exec redpanda-0 -c redpanda -- rpk topic create task-events task-updates reminders -r 1 -p 1 2>/dev/null || true
echo "  Topics created."

# Step 6: Build container images in Minikube Docker context
echo "[6/9] Building container images..."
eval $(minikube docker-env)
# Workaround: use empty Docker config to avoid credential helper issues in WSL2
DOCKER_CONFIG_TMP=$(mktemp -d)
echo '{}' > "$DOCKER_CONFIG_TMP/config.json"
export DOCKER_CONFIG="$DOCKER_CONFIG_TMP"
docker build -t todo-backend:latest "$PROJECT_ROOT/backend/"
docker build -t todo-frontend:latest "$PROJECT_ROOT/frontend/"
docker build -t notification-service:latest "$PROJECT_ROOT/services/notification/"
docker build -t recurring-service:latest "$PROJECT_ROOT/services/recurring/"
docker build -t audit-service:latest "$PROJECT_ROOT/services/audit/"
rm -rf "$DOCKER_CONFIG_TMP"
unset DOCKER_CONFIG
echo "  All images built."

# Step 7: Deploy backend via Helm
echo "[7/9] Deploying backend..."
helm upgrade --install todo-backend "$PROJECT_ROOT/charts/todo-backend/" \
    --set env.DATABASE_URL="$DATABASE_URL" \
    --set env.BETTER_AUTH_SECRET="${BETTER_AUTH_SECRET:-changeme-local-dev-secret}"
echo "  Backend deployed."

# Step 8: Deploy supporting services via Helm
echo "[8/9] Deploying supporting services..."
helm upgrade --install notification-service "$PROJECT_ROOT/charts/notification-service/" \
    --set env.DATABASE_URL="$DATABASE_URL"
helm upgrade --install recurring-service "$PROJECT_ROOT/charts/recurring-service/" \
    --set env.DATABASE_URL="$DATABASE_URL"
helm upgrade --install audit-service "$PROJECT_ROOT/charts/audit-service/" \
    --set env.DATABASE_URL="$DATABASE_URL"
echo "  Supporting services deployed."

# Step 9: Deploy frontend via Helm
echo "[9/9] Deploying frontend..."
helm upgrade --install todo-frontend "$PROJECT_ROOT/charts/todo-frontend/" \
    --set env.BETTER_AUTH_SECRET="${BETTER_AUTH_SECRET:-changeme-local-dev-secret}" \
    --set env.DATABASE_URL="$DATABASE_URL"
echo "  Frontend deployed."

echo ""
echo "=== Deployment Complete ==="
echo ""
echo "Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=todo-backend --timeout=120s 2>/dev/null || true
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=notification-service --timeout=120s 2>/dev/null || true
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=recurring-service --timeout=120s 2>/dev/null || true
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=audit-service --timeout=120s 2>/dev/null || true
kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=todo-frontend --timeout=120s 2>/dev/null || true

echo ""
echo "Pod status:"
kubectl get pods
echo ""
echo "To access frontend: minikube service todo-frontend --url"
echo "To check health: kubectl port-forward svc/todo-backend 8000:8000 & curl http://localhost:8000/health"
