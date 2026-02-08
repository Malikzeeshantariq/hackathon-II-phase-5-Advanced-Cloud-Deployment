# Minikube Setup & Remaining Tasks

**Spec Reference**: spec.md FR-1, FR-2, FR-3, FR-4
**Plan Reference**: plan.md Sections 7, 8
**Tasks Reference**: tasks.md T4-04 through T4-16

---

## Prerequisites

Before continuing, install the required tools:

### 1. Install Minikube

**macOS:**
```bash
brew install minikube
```

**Linux:**
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

**Windows (WSL2):**
```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
```

### 2. Install kubectl

```bash
# macOS
brew install kubectl

# Linux/WSL
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

### 3. Install Helm

```bash
# macOS
brew install helm

# Linux/WSL
curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

### 4. Install AI DevOps Tools (Optional but Required for T4-13, T4-14)

**kubectl-ai:**
```bash
# See: https://github.com/sozercan/kubectl-ai
brew install sozercan/kubectl-ai/kubectl-ai  # macOS
# or follow GitHub installation for Linux
```

**kagent:**
```bash
# See: https://github.com/kagent-ai/kagent
pip install kagent
```

---

## T4-04: Build & Tag Backend Image

```bash
# Start Minikube
minikube start --cpus=2 --memory=4096

# Configure shell to use Minikube's Docker daemon
eval $(minikube docker-env)

# Build backend image
docker build -t todo-backend:latest ./backend

# Verify image
docker images | grep todo-backend
```

**Expected Output:**
```
todo-backend   latest   <image-id>   <time>   <size>
```

---

## T4-05: Build & Tag Frontend Image

```bash
# Ensure Minikube Docker environment (if not already set)
eval $(minikube docker-env)

# Build frontend image with API URL
docker build \
  --build-arg NEXT_PUBLIC_API_URL=http://todo-backend:8000 \
  -t todo-frontend:latest \
  ./frontend

# Verify image
docker images | grep todo-frontend
```

**Expected Output:**
```
todo-frontend   latest   <image-id>   <time>   <size>
```

---

## T4-09 & T4-10: Deploy via Helm

### Prepare Secrets (DO NOT COMMIT)

```bash
cat > /tmp/secrets.yaml << 'EOF'
env:
  DATABASE_URL: "postgresql://user:password@host/database?sslmode=require"
  BETTER_AUTH_SECRET: "your-32-character-secret-here"
EOF
```

### Deploy Backend

```bash
helm install todo-backend ./charts/todo-backend -f /tmp/secrets.yaml

# Wait for pod
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=todo-backend --timeout=300s

# Verify
kubectl get pods,svc -l app.kubernetes.io/name=todo-backend
```

### Deploy Frontend

```bash
helm install todo-frontend ./charts/todo-frontend -f /tmp/secrets.yaml

# Wait for pod
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=todo-frontend --timeout=300s

# Verify
kubectl get pods,svc -l app.kubernetes.io/name=todo-frontend
```

---

## T4-11: Validate Service Connectivity

### 1. Frontend Accessibility

```bash
# Get frontend URL
minikube service todo-frontend --url

# Test connectivity
curl -I $(minikube service todo-frontend --url)
```

### 2. Frontend-to-Backend Communication

```bash
kubectl exec -it deployment/todo-frontend -- \
  wget -qO- http://todo-backend:8000/health
```

### 3. Backend Logs (Database Connectivity)

```bash
kubectl logs deployment/todo-backend | head -50
```

### 4. Browser Test

Open the URL from `minikube service todo-frontend --url` in your browser.

---

## T4-12: Reproducibility Test

```bash
# Delete everything
minikube delete

# Start fresh
minikube start --cpus=2 --memory=4096

# Configure Docker
eval $(minikube docker-env)

# Rebuild images
docker build -t todo-backend:latest ./backend
docker build --build-arg NEXT_PUBLIC_API_URL=http://todo-backend:8000 -t todo-frontend:latest ./frontend

# Redeploy
helm install todo-backend ./charts/todo-backend -f /tmp/secrets.yaml
helm install todo-frontend ./charts/todo-frontend -f /tmp/secrets.yaml

# Wait for all pods
kubectl wait --for=condition=ready pod --all --timeout=300s

# Verify
minikube service todo-frontend --url
```

---

## T4-13: kubectl-ai Operations

```bash
# Deployment operation
kubectl-ai "show the status of all deployments in the default namespace"

# Debugging operation
kubectl-ai "describe why todo-backend pods are running and show their resource usage"

# Additional operations
kubectl-ai "show logs from the todo-frontend pod"
kubectl-ai "check if services have correct endpoints"
```

---

## T4-14: kagent Analysis

```bash
kagent "analyze the health of my kubernetes cluster and identify any issues"

# Or
kagent "recommend resource optimizations for the todo application pods"
```

---

## T4-15: Failure & Restart Resilience Test

```bash
# Create test data in the application first, then:

# Force pod restart
kubectl delete pod -l app.kubernetes.io/name=todo-backend
kubectl delete pod -l app.kubernetes.io/name=todo-frontend

# Wait for recovery
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=todo-backend --timeout=120s
kubectl wait --for=condition=ready pod -l app.kubernetes.io/name=todo-frontend --timeout=120s

# Verify data persistence in browser
minikube service todo-frontend --url
```

---

## Common Commands Reference

```bash
# Check Minikube status
minikube status

# View all resources
kubectl get all

# View pod logs
kubectl logs -f deployment/todo-backend
kubectl logs -f deployment/todo-frontend

# Helm list releases
helm list

# Upgrade deployments after changes
helm upgrade todo-backend ./charts/todo-backend -f /tmp/secrets.yaml
helm upgrade todo-frontend ./charts/todo-frontend -f /tmp/secrets.yaml

# Uninstall
helm uninstall todo-frontend
helm uninstall todo-backend

# Stop Minikube
minikube stop

# Delete Minikube cluster
minikube delete
```

---

## Troubleshooting

### Pod in CrashLoopBackOff

```bash
kubectl describe pod <pod-name>
kubectl logs <pod-name> --previous
```

### Service Not Accessible

```bash
kubectl get endpoints
kubectl describe svc todo-frontend
```

### Image Pull Errors

```bash
# Ensure you built in Minikube's Docker context
eval $(minikube docker-env)
docker images | grep todo
```

### Database Connection Issues

```bash
# Verify DATABASE_URL is set
kubectl exec -it deployment/todo-backend -- env | grep DATABASE
```
