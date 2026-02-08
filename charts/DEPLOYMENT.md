# T4-08: Helm Deployment Instructions

**Spec Reference**: spec.md FR-5.1, FR-5.2, FR-5.3, FR-5.4
**Plan Reference**: plan.md Section 9 (Security & Configuration)

---

## Prerequisites

1. Minikube running: `minikube status`
2. Docker images built and loaded into Minikube
3. Secrets prepared (DO NOT COMMIT)

---

## Secrets Configuration

Create a secrets file (DO NOT COMMIT TO GIT):

```bash
cat > /tmp/secrets.yaml << 'EOF'
env:
  DATABASE_URL: "postgresql://user:password@host/database?sslmode=require"
  BETTER_AUTH_SECRET: "your-32-character-secret-here"
EOF
```

---

## Deployment Commands

### Deploy Backend

```bash
helm install todo-backend ./charts/todo-backend \
  -f /tmp/secrets.yaml
```

### Deploy Frontend

```bash
helm install todo-frontend ./charts/todo-frontend \
  -f /tmp/secrets.yaml
```

### Upgrade Deployments

```bash
helm upgrade todo-backend ./charts/todo-backend -f /tmp/secrets.yaml
helm upgrade todo-frontend ./charts/todo-frontend -f /tmp/secrets.yaml
```

### Uninstall

```bash
helm uninstall todo-frontend
helm uninstall todo-backend
```

---

## Service Communication

| From | To | URL |
|------|-----|-----|
| Frontend | Backend | `http://todo-backend:8000` |
| Backend | PostgreSQL | External Neon URL via DATABASE_URL |
| Host | Frontend | `http://$(minikube ip):30000` |

---

## Accessing the Application

```bash
# Get Minikube IP
minikube ip

# Or use service URL
minikube service todo-frontend --url
```

---

## Environment Variables Reference

### Backend

| Variable | Source | Description |
|----------|--------|-------------|
| DATABASE_URL | Secret | Neon PostgreSQL connection string |
| BETTER_AUTH_SECRET | Secret | JWT signing secret |
| CORS_ORIGINS | ConfigMap | Allowed CORS origins |

### Frontend

| Variable | Source | Description |
|----------|--------|-------------|
| DATABASE_URL | Secret | Neon PostgreSQL (for Better Auth) |
| BETTER_AUTH_SECRET | Secret | JWT signing secret |
| NEXT_PUBLIC_API_URL | Build-time ARG | Backend API URL (baked into image) |
