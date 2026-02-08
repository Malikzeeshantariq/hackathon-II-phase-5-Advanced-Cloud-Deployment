# Quickstart: Phase 4 Kubernetes Deployment

**Feature**: `001-k8s-helm-deployment`
**Date**: 2026-02-03

---

## Prerequisites

Before deploying, ensure you have:

- [ ] Docker Desktop installed and running
- [ ] Minikube installed (`minikube version` returns 1.30+)
- [ ] Helm installed (`helm version` returns 3.x)
- [ ] kubectl installed (`kubectl version`)
- [ ] kubectl-ai installed (for AI-assisted operations)
- [ ] kagent installed (for cluster analysis)
- [ ] Access to Neon PostgreSQL database (DATABASE_URL)
- [ ] BETTER_AUTH_SECRET generated (`openssl rand -hex 32`)

---

## Quick Deploy (5-Step Process)

### Step 1: Start Minikube

```bash
# Start cluster with sufficient resources
minikube start --cpus=2 --memory=4096

# Verify cluster is running
minikube status
```

### Step 2: Configure Docker Environment

```bash
# Point shell to Minikube's Docker daemon
eval $(minikube docker-env)

# Verify (should show Minikube's Docker)
docker info | grep -i name
```

### Step 3: Build Docker Images

```bash
# Build backend image
docker build -t todo-backend:latest ./backend

# Build frontend image
docker build -t todo-frontend:latest ./frontend

# Verify images
docker images | grep todo
```

### Step 4: Deploy with Helm

```bash
# Create secrets file (DO NOT COMMIT)
cat > /tmp/secrets.yaml << EOF
env:
  DATABASE_URL: "postgresql://user:pass@host/db"
  BETTER_AUTH_SECRET: "your-32-char-secret"
EOF

# Deploy backend
helm install todo-backend ./charts/todo-backend -f /tmp/secrets.yaml

# Deploy frontend
helm install todo-frontend ./charts/todo-frontend -f /tmp/secrets.yaml

# Check pod status
kubectl get pods -w
```

### Step 5: Access the Application

```bash
# Get Minikube IP
minikube ip

# Access frontend (NodePort 30000)
# Open in browser: http://$(minikube ip):30000

# Or use minikube service command
minikube service todo-frontend --url
```

---

## AI-Assisted Operations

### Using kubectl-ai

```bash
# Deploy operations
kubectl-ai "show status of all pods"
kubectl-ai "describe the todo-backend deployment"

# Debugging
kubectl-ai "show logs from todo-backend pod"
kubectl-ai "why is todo-frontend pod not ready"
```

### Using kagent

```bash
# Cluster health
kagent "analyze cluster health"
kagent "check for resource issues"
```

---

## Full Cluster Reset (Reproducibility Test)

```bash
# Delete everything
minikube delete

# Fresh start
minikube start --cpus=2 --memory=4096
eval $(minikube docker-env)

# Rebuild images
docker build -t todo-backend:latest ./backend
docker build -t todo-frontend:latest ./frontend

# Redeploy
helm install todo-backend ./charts/todo-backend -f /tmp/secrets.yaml
helm install todo-frontend ./charts/todo-frontend -f /tmp/secrets.yaml

# Verify
kubectl get pods
minikube service todo-frontend --url
```

---

## Scaling

```bash
# Scale backend to 3 replicas
helm upgrade todo-backend ./charts/todo-backend \
  -f /tmp/secrets.yaml \
  --set replicaCount=3

# Scale frontend to 2 replicas
helm upgrade todo-frontend ./charts/todo-frontend \
  -f /tmp/secrets.yaml \
  --set replicaCount=2

# Verify scaling
kubectl get pods
```

---

## Troubleshooting

### Pods not starting

```bash
# Check pod status
kubectl get pods

# Describe pod for events
kubectl describe pod <pod-name>

# Check logs
kubectl logs <pod-name>
```

### Service not accessible

```bash
# Check services
kubectl get svc

# Check endpoints
kubectl get endpoints

# Test from within cluster
kubectl run -it --rm debug --image=alpine -- sh
# Then: wget -qO- http://todo-backend:8000/health
```

### Database connection issues

```bash
# Check if DATABASE_URL is set
kubectl exec <backend-pod> -- env | grep DATABASE

# Test database connectivity
kubectl exec <backend-pod> -- python -c "import psycopg2; print('OK')"
```

---

## Cleanup

```bash
# Remove deployments
helm uninstall todo-frontend
helm uninstall todo-backend

# Stop Minikube
minikube stop

# Delete cluster (full cleanup)
minikube delete
```

---

## Configuration Reference

### Backend values.yaml

| Key | Default | Description |
|-----|---------|-------------|
| `replicaCount` | 1 | Number of replicas |
| `image.repository` | todo-backend | Image name |
| `image.tag` | latest | Image tag |
| `service.port` | 8000 | Service port |
| `env.DATABASE_URL` | "" | PostgreSQL connection |
| `env.BETTER_AUTH_SECRET` | "" | JWT secret |
| `env.CORS_ORIGINS` | http://todo-frontend:3000 | CORS setting |

### Frontend values.yaml

| Key | Default | Description |
|-----|---------|-------------|
| `replicaCount` | 1 | Number of replicas |
| `image.repository` | todo-frontend | Image name |
| `image.tag` | latest | Image tag |
| `service.port` | 3000 | Service port |
| `service.nodePort` | 30000 | External port |
| `env.BETTER_AUTH_SECRET` | "" | JWT secret |
| `env.DATABASE_URL` | "" | PostgreSQL connection |

---

## Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| Minikube CPUs | 2 |
| Minikube Memory | 4GB |
| Minikube Disk | 20GB |
| Docker | 24.x+ |
| Helm | 3.x |
| kubectl | 1.28+ |
