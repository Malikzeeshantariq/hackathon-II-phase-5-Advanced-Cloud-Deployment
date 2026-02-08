# Multi-Stage Builds

Production-optimized Docker images with minimal footprint.

Source: [Docker Multi-Stage Builds](https://docs.docker.com/build/building/multi-stage/)

---

## Why Multi-Stage?

| Benefit | Impact |
|---------|--------|
| Smaller images | 70%+ size reduction typical |
| Security | No build tools in production |
| Faster deploys | Less data to transfer |
| Clean separation | Dev tools stay in build stage |

---

## Basic Multi-Stage Pattern

```dockerfile
# Stage 1: Build
FROM python:3.12-slim AS builder
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt

# Stage 2: Production
FROM python:3.12-slim
WORKDIR /app

COPY --from=builder /app/deps /usr/local/lib/python3.12/site-packages/
COPY ./app ./app

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Production Multi-Stage with Security

```dockerfile
# =============================================================================
# Stage 1: Builder
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build dependencies if needed
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Install to a specific directory for easy copying
RUN pip install --no-cache-dir --target=/build/deps -r requirements.txt

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.12-slim AS production

# Environment configuration
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Install runtime dependencies only (not build tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --no-create-home --shell /bin/false appuser

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

## Multi-Stage with uv

```dockerfile
# =============================================================================
# Stage 1: Builder with uv
# =============================================================================
FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:0.5 /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies only (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable --no-dev

# Copy source and install project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev

# =============================================================================
# Stage 2: Production
# =============================================================================
FROM python:3.12-slim AS production

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user
RUN groupadd --gid 1000 appuser \
    && useradd --uid 1000 --gid 1000 --no-create-home --shell /bin/false appuser

# Copy only the virtual environment
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/app /app/app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Named Stages and Targets

### Multiple Targets in One Dockerfile

```dockerfile
# =============================================================================
# Base stage
# =============================================================================
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

# =============================================================================
# Development target
# =============================================================================
FROM base AS development

RUN pip install --no-cache-dir pytest pytest-cov black ruff mypy

CMD ["fastapi", "dev", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

# =============================================================================
# Production target
# =============================================================================
FROM base AS production

RUN groupadd -r appuser && useradd -r -g appuser appuser
USER appuser

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

### Building Specific Targets

```bash
# Build development image
docker build --target development -t myapp:dev .

# Build production image
docker build --target production -t myapp:prod .
```

---

## COPY --from Syntax

### From Named Stage

```dockerfile
COPY --from=builder /app/deps /usr/local/lib/python3.12/site-packages/
```

### From Stage Number

```dockerfile
COPY --from=0 /app/deps /usr/local/lib/python3.12/site-packages/
```

### From External Image

```dockerfile
# Copy binary from external image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
```

---

## Image Size Comparison

| Approach | Typical Size |
|----------|--------------|
| `python:3.12` (full) | ~1 GB |
| `python:3.12-slim` | ~150 MB |
| Multi-stage with slim | ~100-150 MB |
| `python:3.12-alpine` | ~50 MB |
| Distroless Python | ~30-50 MB |

**Note**: Alpine can have compatibility issues with some Python packages (musl vs glibc).

---

## BuildKit Features

### Cache Mounts

```dockerfile
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -r requirements.txt
```

### Secret Mounts (for private packages)

```dockerfile
RUN --mount=type=secret,id=pip_conf,target=/root/.pip/pip.conf \
    pip install -r requirements.txt
```

### Bind Mounts (avoid copying during build)

```dockerfile
RUN --mount=type=bind,source=requirements.txt,target=requirements.txt \
    pip install --no-cache-dir -r requirements.txt
```

---

## Best Practices

1. **Name your stages**: Use `AS stagename` for clarity
2. **Order matters**: Less-changing content first for caching
3. **Minimize final stage**: Only copy what's needed to run
4. **Use slim/alpine**: Avoid full images in production
5. **BuildKit**: Enable for cache mounts and better builds
6. **Target production**: Always verify production target works

### Enable BuildKit

```bash
export DOCKER_BUILDKIT=1
docker build .

# Or with docker buildx
docker buildx build .
```
