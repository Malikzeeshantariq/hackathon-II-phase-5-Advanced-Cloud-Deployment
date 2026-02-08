# Security Best Practices

Hardening Docker containers for Python/FastAPI applications.

Sources:
- [Docker Security Best Practices](https://docs.docker.com/develop/security-best-practices/)
- [Python Docker Best Practices](https://testdriven.io/blog/docker-best-practices/)

---

## Non-Root User

Running containers as root is a security risk. If compromised, attackers have root access.

### Create Non-Root User

```dockerfile
# Method 1: Standard approach
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Method 2: More restrictive (no home, no shell)
RUN addgroup --gid 1000 --system app \
    && adduser --no-create-home --shell /bin/false --disabled-password \
       --uid 1000 --system --group app
```

### Switch to User

```dockerfile
# Copy files with correct ownership
COPY --chown=appuser:appuser ./app ./app

# Switch to non-root user (do this last)
USER appuser

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Complete Example

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Create non-root user early
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --no-create-home --shell /bin/false appuser

# Install dependencies as root
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app with correct ownership
COPY --chown=appuser:appuser ./app ./app

# Switch to non-root user
USER appuser

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Minimal Base Images

| Image | Size | Security |
|-------|------|----------|
| `python:3.12` | ~1 GB | More attack surface |
| `python:3.12-slim` | ~150 MB | Recommended |
| `python:3.12-alpine` | ~50 MB | Smallest, but musl issues |

### Slim Image Pattern

```dockerfile
FROM python:3.12-slim

# Install only needed runtime packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*
```

### Alpine Considerations

```dockerfile
FROM python:3.12-alpine

# Alpine uses musl, some packages need build tools
RUN apk add --no-cache libpq

# May need these for some packages
# RUN apk add --no-cache --virtual .build-deps gcc musl-dev \
#     && pip install ... \
#     && apk del .build-deps
```

**Warning**: Alpine's musl libc can cause issues with some Python packages.

---

## Environment Variables

### Never Hardcode Secrets

```dockerfile
# BAD - secrets in image
ENV DATABASE_URL=postgresql://user:password@host/db
ENV SECRET_KEY=my-secret-key

# GOOD - inject at runtime
ENV DATABASE_URL=""
ENV SECRET_KEY=""
```

### Runtime Injection

```bash
# Via command line
docker run -e DATABASE_URL=... -e SECRET_KEY=... myimage

# Via env file
docker run --env-file .env myimage
```

### Docker Secrets (Swarm/Compose)

```yaml
services:
  api:
    secrets:
      - db_password
      - secret_key

secrets:
  db_password:
    file: ./secrets/db_password.txt
  secret_key:
    file: ./secrets/secret_key.txt
```

---

## Read-Only Filesystem

```bash
docker run --read-only --tmpfs /tmp myimage
```

```yaml
services:
  api:
    read_only: true
    tmpfs:
      - /tmp
```

---

## Drop Capabilities

```yaml
services:
  api:
    cap_drop:
      - ALL
    # Only add back what's needed
    # cap_add:
    #   - NET_BIND_SERVICE
```

---

## No Privileged Mode

```yaml
services:
  api:
    privileged: false  # Default, but explicit is good
    security_opt:
      - no-new-privileges:true
```

---

## Image Scanning

### Trivy

```bash
# Scan image for vulnerabilities
trivy image myapp:latest
```

### Docker Scout

```bash
# Built into Docker Desktop
docker scout cves myapp:latest
```

### GitHub Actions

```yaml
- name: Scan image
  uses: aquasecurity/trivy-action@master
  with:
    image-ref: myapp:latest
    severity: CRITICAL,HIGH
```

---

## .dockerignore Security

Prevent sensitive files from being copied:

```
# Secrets
.env
.env.*
*.pem
*.key
secrets/
credentials/

# Git
.git
.gitignore

# Development
.venv
venv
__pycache__
*.pyc
.pytest_cache
.mypy_cache

# IDE
.vscode
.idea

# Docker
Dockerfile*
docker-compose*
.dockerignore

# Tests (usually not needed in prod)
tests/
*_test.py
test_*.py
```

---

## Pin Image Versions

```dockerfile
# BAD - mutable tag
FROM python:latest
FROM python:3.12

# GOOD - specific version
FROM python:3.12.8-slim

# BEST - SHA digest (immutable)
FROM python:3.12.8-slim@sha256:abc123...
```

Get SHA:
```bash
docker pull python:3.12-slim
docker inspect python:3.12-slim --format='{{index .RepoDigests 0}}'
```

---

## Network Isolation

```yaml
services:
  api:
    networks:
      - frontend
      - backend

  db:
    networks:
      - backend  # Only accessible from backend network

networks:
  frontend:
  backend:
    internal: true  # No external access
```

---

## Resource Limits

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

---

## Complete Secure Dockerfile

```dockerfile
# =============================================================================
# Production-Secure FastAPI Dockerfile
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/build/deps -r requirements.txt

# =============================================================================
FROM python:3.12-slim

# Security: Don't run as root
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --no-create-home --shell /bin/false appuser

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random

WORKDIR /app

# Runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy dependencies from builder
COPY --from=builder /build/deps /usr/local/lib/python3.12/site-packages/

# Copy application with correct ownership
COPY --chown=appuser:appuser ./app ./app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Security Checklist

- [ ] Non-root user configured
- [ ] Slim or minimal base image
- [ ] No secrets hardcoded in Dockerfile
- [ ] .dockerignore excludes sensitive files
- [ ] Image versions pinned (preferably with SHA)
- [ ] Only necessary packages installed
- [ ] apt cache cleaned after installs
- [ ] read_only filesystem where possible
- [ ] Capabilities dropped
- [ ] No privileged mode
- [ ] Regular vulnerability scanning
