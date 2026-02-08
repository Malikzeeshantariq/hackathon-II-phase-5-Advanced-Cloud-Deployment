---
name: docker-fastapi
description: |
  Containerize Python/FastAPI applications with Docker from hello world to production.
  This skill should be used when users want to create Dockerfiles, docker-compose configurations,
  multi-stage builds, health checks, or deploy FastAPI apps in containers.
---

# Docker FastAPI

Containerize Python/FastAPI applications from development to production deployment.

## What This Skill Does

- Create Dockerfiles for FastAPI applications (basic to production)
- Configure multi-stage builds for minimal image sizes
- Set up Docker Compose for local development
- Implement health checks and graceful shutdown
- Apply security best practices (non-root users, minimal images)
- Handle environment variables correctly
- Configure production deployment patterns

## What This Skill Does NOT Do

- Kubernetes deployment (use k8s-specific tools)
- CI/CD pipeline configuration
- Cloud-specific container services (ECS, Cloud Run, etc.)
- Container registry management
- SSL/TLS certificate handling (use reverse proxy)

---

## Before Implementation

Gather context to ensure successful implementation:

| Source | Gather |
|--------|--------|
| **Codebase** | Project structure, existing Dockerfile, requirements.txt or pyproject.toml |
| **Conversation** | Development vs production, single vs multi-worker, uv vs pip |
| **Skill References** | Patterns from `references/` for specific scenarios |
| **User Guidelines** | Team Docker conventions, base image preferences |

---

## Required Clarifications

Ask about USER'S specific context:

1. **Environment**: "Development, production, or both?"
2. **Package Manager**: "Using pip, uv, or poetry?"
3. **Workers**: "Single process or multiple workers per container?"
4. **Compose**: "Need Docker Compose for local development?"

---

## Decision Tree

```
What environment?
├── Development only
│   └── Use basic Dockerfile + docker-compose with reload
├── Production only
│   └── Use multi-stage build + non-root user
└── Both
    └── Use multi-stage with dev/prod targets + compose

Package manager?
├── pip → Standard requirements.txt pattern
├── uv → COPY --from=ghcr.io/astral-sh/uv pattern
└── poetry → Multi-stage with poetry export

Workers per container?
├── Single (Kubernetes/orchestrated)
│   └── CMD ["fastapi", "run", ...] without --workers
└── Multiple (single server/Compose)
    └── CMD ["fastapi", "run", ..., "--workers", "4"]
```

---

## Core Patterns

### Pattern 1: Basic Dockerfile (Development)

```dockerfile
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 2: Production Multi-Stage Build

```dockerfile
# Build stage
FROM python:3.12-slim AS builder
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt

# Production stage
FROM python:3.12-slim
WORKDIR /app

# Security: Non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy dependencies from builder
COPY --from=builder /app/deps /usr/local/lib/python3.12/site-packages/

COPY --chown=appuser:appuser ./app ./app

USER appuser

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Pattern 3: With Health Check

```dockerfile
# Add health check endpoint in FastAPI:
# @app.get("/health")
# def health(): return {"status": "healthy"}

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1
```

### Pattern 4: Docker Compose (Development)

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app  # Live reload
    command: fastapi dev app/main.py --host 0.0.0.0 --port 8000
    environment:
      - DATABASE_URL=${DATABASE_URL}
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 10s
      timeout: 5s
      retries: 3
```

---

## Critical Rules

### MUST Follow

| Rule | Reason |
|------|--------|
| Use exec form for CMD: `CMD ["fastapi", ...]` | Enables graceful shutdown, proper signal handling |
| Copy requirements before code | Maximizes Docker layer caching |
| Use `--no-cache-dir` with pip | Reduces image size |
| Run as non-root in production | Security best practice |
| Set `PYTHONUNBUFFERED=1` | Ensures logs appear immediately |

### MUST Avoid

| Anti-Pattern | Correct Pattern |
|--------------|-----------------|
| `CMD fastapi run ...` (shell form) | `CMD ["fastapi", "run", ...]` |
| `FROM python:3.12` (full image) | `FROM python:3.12-slim` |
| Running as root in production | `USER appuser` |
| Copying entire project first | Copy requirements.txt first |
| Using deprecated base images | Build from official Python image |

---

## Health Check Implementation

### FastAPI Endpoint

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

### Dockerfile HEALTHCHECK

```dockerfile
# Without curl (recommended for slim images)
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1
```

### Docker Compose Health Check

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 5s
```

---

## Environment Variables

### Dockerfile ENV

```dockerfile
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000
```

### Runtime via docker run

```bash
docker run -e DATABASE_URL=postgresql://... -e SECRET_KEY=... myimage
```

### Docker Compose

```yaml
services:
  api:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    env_file:
      - .env
```

---

## Output Checklist

Before delivering Dockerfile/Compose:

- [ ] CMD uses exec form (array syntax)
- [ ] Requirements copied before application code
- [ ] `--no-cache-dir` used with pip
- [ ] Non-root user configured (production)
- [ ] `PYTHONUNBUFFERED=1` set
- [ ] Health check configured
- [ ] `.dockerignore` includes `.venv`, `__pycache__`, `.git`
- [ ] Slim base image used (`python:3.x-slim`)

---

## Reference Files

| File | When to Read |
|------|--------------|
| `references/dockerfile-patterns.md` | All Dockerfile variations (pip, uv, poetry) |
| `references/multi-stage-builds.md` | Production image optimization |
| `references/docker-compose.md` | Development setup, service dependencies |
| `references/security-best-practices.md` | Hardening containers |
| `references/production-deployment.md` | Reverse proxy, workers, orchestration |

---

## Quick Reference

### Build & Run

```bash
# Build
docker build -t myapp .

# Run (development)
docker run -p 8000:8000 myapp

# Run (with env vars)
docker run -p 8000:8000 -e DATABASE_URL=... myapp

# Compose up
docker compose up --build
```

### Common Issues

| Issue | Solution |
|-------|----------|
| 10s shutdown delay | Use exec form CMD, not shell form |
| pip cache bloating image | Use `--no-cache-dir` |
| Permission denied | Check file ownership with `--chown` |
| Container not receiving signals | Use exec form, not shell form |
