#!/usr/bin/env bash
# T034: Manual OKE cloud deployment script (for debugging / initial setup)
# Spec Reference: specs/003-dapr-k8s-deployment/quickstart.md
# Plan Reference: plan.md - Cloud Deployment
#
# Usage: ./scripts/deploy-cloud.sh
# Prerequisites: kubectl configured for OKE, helm installed, images pushed to OCIR
# Required env vars: OCI_REGION, OCIR_NAMESPACE, DATABASE_URL, BETTER_AUTH_SECRET, IMAGE_TAG

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "=== Phase V Part C: Cloud OKE Deployment ==="
echo "Project root: $PROJECT_ROOT"
echo ""

# Validate required environment variables
for var in OCI_REGION OCIR_NAMESPACE DATABASE_URL BETTER_AUTH_SECRET; do
    if [ -z "${!var:-}" ]; then
        echo "ERROR: $var environment variable not set."
        exit 1
    fi
done
IMAGE_TAG="${IMAGE_TAG:-latest}"
REGISTRY="${OCI_REGION}.ocir.io/${OCIR_NAMESPACE}"

echo "[1/6] Verifying kubectl context..."
kubectl get nodes || { echo "ERROR: Cannot reach OKE cluster."; exit 1; }
echo ""

echo "[2/6] Applying cloud Dapr components..."
kubectl apply -f "$PROJECT_ROOT/dapr/components/pubsub-cloud.yaml"
kubectl apply -f "$PROJECT_ROOT/dapr/components/statestore.yaml"
kubectl apply -f "$PROJECT_ROOT/dapr/components/secrets.yaml"
echo ""

echo "[3/6] Creating Kubernetes secrets..."
kubectl delete secret dapr-secrets --ignore-not-found
kubectl create secret generic dapr-secrets \
    --from-literal=database-url="$DATABASE_URL" \
    --from-literal=better-auth-secret="$BETTER_AUTH_SECRET"
echo ""

echo "[4/6] Deploying backend..."
helm upgrade --install todo-backend "$PROJECT_ROOT/charts/todo-backend/" \
    -f "$PROJECT_ROOT/charts/todo-backend/values-cloud.yaml" \
    --set image.repository="$REGISTRY/todo-backend" \
    --set image.tag="$IMAGE_TAG"
echo ""

echo "[5/6] Deploying supporting services..."
for svc in notification-service recurring-service audit-service; do
    helm upgrade --install "$svc" "$PROJECT_ROOT/charts/$svc/" \
        -f "$PROJECT_ROOT/charts/$svc/values-cloud.yaml" \
        --set image.repository="$REGISTRY/$svc" \
        --set image.tag="$IMAGE_TAG"
done
echo ""

echo "[6/6] Deploying frontend..."
helm upgrade --install todo-frontend "$PROJECT_ROOT/charts/todo-frontend/" \
    -f "$PROJECT_ROOT/charts/todo-frontend/values-cloud.yaml" \
    --set image.repository="$REGISTRY/todo-frontend" \
    --set image.tag="$IMAGE_TAG"
echo ""

echo "=== Cloud Deployment Complete ==="
echo ""
echo "Waiting for pods to be ready..."
kubectl rollout status deployment/todo-backend --timeout=120s || true
kubectl rollout status deployment/notification-service --timeout=120s || true
kubectl rollout status deployment/recurring-service --timeout=120s || true
kubectl rollout status deployment/audit-service --timeout=120s || true
kubectl rollout status deployment/todo-frontend --timeout=120s || true
echo ""
echo "Pod status:"
kubectl get pods
