# Research: Phase 4 Infrastructure — Local Kubernetes Deployment

**Feature**: `001-k8s-helm-deployment`
**Date**: 2026-02-03
**Status**: Complete

---

## Research Summary

This document captures research findings for Phase 4 infrastructure decisions. All topics from the Technical Context have been resolved.

---

## 1. Docker Multi-Stage Builds for Python (FastAPI)

### Decision
Use Python 3.11-slim as base with two-stage build pattern.

### Rationale
- `python:3.11-slim` is ~130MB vs ~900MB for full image
- Multi-stage separates build dependencies from runtime
- `--user` flag for pip avoids root installation

### Alternatives Considered
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Alpine-based | Smaller (~50MB) | musl libc issues with some packages | Rejected |
| Single-stage slim | Simple | Includes pip cache, larger | Rejected |
| Distroless | Most secure | Difficult debugging | Future consideration |

### Implementation Pattern
```dockerfile
FROM python:3.11-slim AS builder
# Install to user directory
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim
# Copy only installed packages
COPY --from=builder /root/.local /root/.local
```

---

## 2. Docker Multi-Stage Builds for Next.js

### Decision
Use Node 20-alpine with three-stage build and standalone output.

### Rationale
- Next.js standalone mode reduces runtime to ~20MB
- Alpine images are smaller but Node-compatible
- Three stages: deps → build → runtime

### Alternatives Considered
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Two-stage | Simpler | Larger final image | Rejected |
| Node:slim | More compatible | Larger than alpine | Rejected |
| Static export | No server needed | Loses SSR/API routes | Rejected |

### Implementation Pattern
```dockerfile
FROM node:20-alpine AS deps
RUN npm ci

FROM node:20-alpine AS builder
COPY --from=deps /app/node_modules ./node_modules
RUN npm run build

FROM node:20-alpine
COPY --from=builder /app/.next/standalone ./
```

### Critical Configuration
Next.js config MUST include:
```javascript
// next.config.ts
export default {
  output: 'standalone'
}
```

---

## 3. Helm Chart Structure Best Practices

### Decision
Follow standard Helm chart structure with helpers template.

### Rationale
- `_helpers.tpl` enables reusable template functions
- Separate templates per resource type
- Values schema documents configuration contract

### Standard Structure
```text
charts/todo-backend/
├── Chart.yaml           # Chart metadata
├── values.yaml          # Default values
├── values.schema.json   # Optional: JSON schema
└── templates/
    ├── _helpers.tpl     # Template helpers
    ├── deployment.yaml  # Kubernetes Deployment
    ├── service.yaml     # Kubernetes Service
    ├── configmap.yaml   # Non-secret config
    └── secret.yaml      # Secrets (optional)
```

### Key Patterns
1. Use `{{ include "chart.fullname" . }}` for resource names
2. Use `{{ .Values.xxx }}` for configurable values
3. Use `{{- toYaml .Values.resources | nindent 12 }}` for nested YAML

---

## 4. Minikube Image Loading Strategy

### Decision
Use Minikube's Docker daemon directly (`eval $(minikube docker-env)`).

### Rationale
- No external registry dependency
- Images available immediately after build
- `imagePullPolicy: Never` or `IfNotPresent` works

### Alternatives Considered
| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| Docker Hub | Standard workflow | Requires auth, network | Rejected for local dev |
| `minikube image load` | Works with any daemon | Slower, copies images | Backup option |
| Local registry | Production-like | Extra setup | Rejected for local dev |

### Workflow
```bash
# Point shell to Minikube's Docker
eval $(minikube docker-env)

# Build images (they appear in Minikube automatically)
docker build -t todo-backend:latest ./backend
docker build -t todo-frontend:latest ./frontend

# Use imagePullPolicy: IfNotPresent in Helm
```

---

## 5. kubectl-ai Usage Patterns

### Decision
Use kubectl-ai for natural language → kubectl command generation.

### Rationale
- Satisfies constitution requirement for AI-mediated operations
- Generates correct kubectl syntax
- Can explain operations before execution

### Usage Examples
```bash
# Deployment operations
kubectl-ai "deploy todo-backend with 2 replicas"
kubectl-ai "scale frontend deployment to 3 pods"

# Debugging operations
kubectl-ai "show logs from todo-backend pod"
kubectl-ai "describe why todo-frontend pod is not ready"
kubectl-ai "list all pods with their status in todo namespace"

# Inspection operations
kubectl-ai "show resource usage for all pods"
kubectl-ai "check if services are exposing correct ports"
```

### Documentation Requirement
All kubectl-ai commands MUST be documented in task completion notes.

---

## 6. kagent Cluster Analysis

### Decision
Use kagent for cluster health and resource optimization analysis.

### Rationale
- Provides intelligent cluster analysis
- Identifies resource optimization opportunities
- Satisfies FR-4.3 requirement

### Usage Patterns
```bash
# Health analysis
kagent "analyze cluster health"
kagent "check for any pod issues"

# Resource analysis
kagent "recommend resource limits for todo-backend"
kagent "identify underutilized resources"

# Performance analysis
kagent "check network latency between services"
```

---

## 7. Service-to-Service Communication in Kubernetes

### Decision
Use Kubernetes DNS for service discovery within cluster.

### Rationale
- Built-in, no external dependencies
- Standard Kubernetes pattern
- Format: `<service>.<namespace>.svc.cluster.local`

### Communication Matrix
| From | To | DNS Name | Port |
|------|-----|----------|------|
| Frontend | Backend | `todo-backend.default.svc.cluster.local` | 8000 |
| Backend | PostgreSQL | External Neon URL | 5432 |
| Host | Frontend | `minikube ip`:30000 | 30000 |

### Environment Variable Configuration
```yaml
# Frontend deployment
env:
  - name: NEXT_PUBLIC_API_URL
    value: "http://todo-backend:8000"

# Simplified DNS (same namespace)
# Full: todo-backend.default.svc.cluster.local
# Short: todo-backend (works within namespace)
```

---

## 8. Next.js Runtime Environment Variables

### Decision
Use build-time variables for `NEXT_PUBLIC_*`, runtime variables for server-side config.

### Rationale
- `NEXT_PUBLIC_*` are baked into client bundle at build time
- Server-side env vars (DATABASE_URL, secrets) are runtime
- Requires careful configuration for Kubernetes

### Implementation Strategy

**Build-time variables** (must be set when building image):
- `NEXT_PUBLIC_API_URL` — Backend API endpoint

**Runtime variables** (set via Kubernetes env):
- `DATABASE_URL` — PostgreSQL connection
- `BETTER_AUTH_SECRET` — JWT signing secret

### Challenge: Dynamic API URL
For Kubernetes, the backend URL varies. Solutions:
1. **Build with placeholder, replace at runtime** — Complex
2. **Use relative paths** — Only works if same origin
3. **Configure at build with known K8s service URL** — Simple, chosen approach

**Chosen Approach**: Build frontend with `NEXT_PUBLIC_API_URL=http://todo-backend:8000` since this is the fixed K8s service name.

---

## Summary of Key Decisions

| Area | Decision | Impact |
|------|----------|--------|
| Python base image | python:3.11-slim | Balance of size and compatibility |
| Node base image | node:20-alpine | Small, compatible with Next.js |
| Next.js output | standalone mode | Minimal runtime footprint |
| Image registry | Minikube Docker daemon | No external dependency |
| Service types | Backend: ClusterIP, Frontend: NodePort | Proper network exposure |
| Service discovery | Kubernetes DNS | Standard, reliable |
| Frontend API URL | Build-time with K8s service name | Simple, deterministic |

---

## Unresolved Items

None. All research topics have been resolved.

---

## References

- [Docker multi-stage builds](https://docs.docker.com/build/building/multi-stage/)
- [Next.js standalone output](https://nextjs.org/docs/app/api-reference/config/next-config-js/output)
- [Helm chart best practices](https://helm.sh/docs/chart_best_practices/)
- [Kubernetes DNS](https://kubernetes.io/docs/concepts/services-networking/dns-pod-service/)
- [Minikube Docker environment](https://minikube.sigs.k8s.io/docs/commands/docker-env/)
