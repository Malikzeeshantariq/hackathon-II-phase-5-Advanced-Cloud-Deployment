# Dockerfile Patterns

Complete Dockerfile patterns for Python/FastAPI applications.

Source: [FastAPI Docker Documentation](https://fastapi.tiangolo.com/deployment/docker/)

---

## Pattern 1: Basic pip (Development)

```dockerfile
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./app ./app

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

**Use when**: Quick development setup, learning Docker.

---

## Pattern 2: pip with Production Hardening

```dockerfile
FROM python:3.12-slim

# Prevent Python from writing bytecode and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy application
COPY --chown=appuser:appuser ./app ./app

# Switch to non-root user
USER appuser

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

**Use when**: Single-stage production deployment.

---

## Pattern 3: uv Package Manager

Source: [uv Docker Guide](https://docs.astral.sh/uv/guides/integration/docker/)

```dockerfile
FROM python:3.12-slim

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install dependencies (cached layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# Copy application and install project
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

CMD ["uv", "run", "fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

**Use when**: Modern Python projects using uv for dependency management.

---

## Pattern 4: uv Multi-Stage Production

```dockerfile
# Build stage
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-editable --no-dev

COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-editable --no-dev

# Production stage
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment from builder
COPY --from=builder --chown=appuser:appuser /app/.venv /app/.venv
COPY --from=builder --chown=appuser:appuser /app/app /app/app

USER appuser

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Pattern 5: Poetry

```dockerfile
# Build stage
FROM python:3.12-slim AS builder

RUN pip install poetry

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Export to requirements.txt
RUN poetry export -f requirements.txt --output requirements.txt --without-hashes

# Install dependencies
RUN pip install --no-cache-dir --target=/app/deps -r requirements.txt

# Production stage
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy dependencies from builder
COPY --from=builder /app/deps /usr/local/lib/python3.12/site-packages/

COPY --chown=appuser:appuser ./app ./app

USER appuser

EXPOSE 8000

CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Pattern 6: Single-File Application

For projects with just `main.py`:

```dockerfile
FROM python:3.12-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./main.py .

CMD ["fastapi", "run", "main.py", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Pattern 7: Behind TLS Termination Proxy

When using Nginx, Traefik, or cloud load balancer:

```dockerfile
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
```

The `--proxy-headers` flag trusts `X-Forwarded-*` headers from the proxy.

---

## Pattern 8: Multiple Workers (Single Container)

For Docker Compose or single-server deployments:

```dockerfile
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Note**: For Kubernetes, prefer single worker per container and scale via replicas.

---

## Directory Structure

### Standard Package

```
project/
├── app/
│   ├── __init__.py
│   └── main.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

### Single File

```
project/
├── main.py
├── requirements.txt
├── Dockerfile
└── .dockerignore
```

---

## .dockerignore Template

```
.git
.gitignore
.venv
venv
__pycache__
*.pyc
*.pyo
.pytest_cache
.mypy_cache
.env
.env.local
*.md
!README.md
Dockerfile
docker-compose*.yml
.dockerignore
tests/
```

---

## CMD: Exec Form vs Shell Form

### Exec Form (CORRECT)

```dockerfile
CMD ["fastapi", "run", "app/main.py", "--port", "8000"]
```

- Process receives signals directly
- Graceful shutdown works
- Lifespan events trigger properly

### Shell Form (AVOID)

```dockerfile
CMD fastapi run app/main.py --port 8000
```

- Runs via `/bin/sh -c`
- Signals go to shell, not FastAPI
- 10-second delay on `docker stop`
- Lifespan events may not trigger

---

## Layer Caching Optimization

```dockerfile
# 1. Base image (rarely changes)
FROM python:3.12-slim

# 2. System dependencies (rarely changes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# 3. Python dependencies (changes occasionally)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Application code (changes frequently)
COPY ./app ./app
```

Copy things that change less frequently first to maximize cache hits.
