# Docker Compose

Local development and multi-service orchestration for FastAPI.

Source: [Docker Compose Documentation](https://docs.docker.com/compose/)

---

## Development Setup

### Basic docker-compose.yml

```yaml
services:
  api:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app  # Live code reload
    command: fastapi dev app/main.py --host 0.0.0.0 --port 8000
    environment:
      - DEBUG=true
```

### With Database

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
    command: fastapi dev app/main.py --host 0.0.0.0 --port 8000
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d appdb"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

---

## Development with Neon PostgreSQL

```yaml
services:
  api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
    command: fastapi dev app/main.py --host 0.0.0.0 --port 8000
    env_file:
      - .env
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 10s
      timeout: 5s
      retries: 3
```

`.env`:
```
DATABASE_URL=postgresql://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require
SECRET_KEY=your-secret-key
```

---

## Full Development Stack

```yaml
services:
  api:
    build:
      context: .
      target: development  # Use dev target from multi-stage
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app
      - ./tests:/app/tests
    command: fastapi dev app/main.py --host 0.0.0.0 --port 8000
    environment:
      - DATABASE_URL=postgresql://user:password@db:5432/appdb
      - REDIS_URL=redis://redis:6379
      - DEBUG=true
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 10s
      timeout: 5s
      retries: 3

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: appdb
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"  # Expose for local tools
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U user -d appdb"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

---

## Production Compose

```yaml
services:
  api:
    build:
      context: .
      target: production
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    restart: unless-stopped
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
```

---

## Health Checks

### API Health Check

```yaml
services:
  api:
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 5s
```

### PostgreSQL Health Check

```yaml
services:
  db:
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5
```

### Redis Health Check

```yaml
services:
  redis:
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
```

---

## depends_on with Conditions

```yaml
services:
  api:
    depends_on:
      db:
        condition: service_healthy  # Wait for health check
      redis:
        condition: service_started  # Just wait for container start
      migrations:
        condition: service_completed_successfully  # Wait for exit 0
```

---

## Environment Variables

### Inline

```yaml
services:
  api:
    environment:
      - DEBUG=true
      - LOG_LEVEL=info
```

### From Host Environment

```yaml
services:
  api:
    environment:
      - DATABASE_URL  # Uses value from host
      - SECRET_KEY=${SECRET_KEY}  # Explicit reference
```

### From File

```yaml
services:
  api:
    env_file:
      - .env
      - .env.local
```

---

## Volumes for Development

### Code Mounting (Live Reload)

```yaml
services:
  api:
    volumes:
      - ./app:/app/app:cached  # Cached for better perf on Mac
      - ./tests:/app/tests
```

### Named Volumes (Persistent Data)

```yaml
services:
  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

### Anonymous Volumes (Exclude from mount)

```yaml
services:
  api:
    volumes:
      - ./app:/app/app
      - /app/.venv  # Don't override container's venv
```

---

## Networking

### Custom Network

```yaml
services:
  api:
    networks:
      - backend

  db:
    networks:
      - backend

networks:
  backend:
    driver: bridge
```

### Expose Internal Port Only

```yaml
services:
  db:
    expose:
      - "5432"  # Only accessible within network
    # ports:   # Don't expose to host
```

---

## Common Commands

```bash
# Start services
docker compose up

# Start in background
docker compose up -d

# Rebuild and start
docker compose up --build

# Stop services
docker compose down

# Stop and remove volumes
docker compose down -v

# View logs
docker compose logs -f api

# Execute command in running container
docker compose exec api bash

# Run one-off command
docker compose run --rm api pytest

# Scale service
docker compose up -d --scale api=3
```

---

## Multiple Compose Files

### Development Override

`docker-compose.yml`:
```yaml
services:
  api:
    build: .
    environment:
      - DATABASE_URL=${DATABASE_URL}
```

`docker-compose.override.yml` (auto-loaded):
```yaml
services:
  api:
    volumes:
      - ./app:/app/app
    command: fastapi dev app/main.py --host 0.0.0.0 --port 8000
    environment:
      - DEBUG=true
```

### Production Override

`docker-compose.prod.yml`:
```yaml
services:
  api:
    restart: unless-stopped
    command: fastapi run app/main.py --host 0.0.0.0 --port 8000 --workers 4
```

```bash
# Use production config
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```
