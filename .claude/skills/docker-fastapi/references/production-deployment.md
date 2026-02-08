# Production Deployment

Production patterns for FastAPI containers.

Source: [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

## Deployment Architectures

### Single Server (Docker Compose)

```
┌─────────────────────────────────────────┐
│ Server                                  │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │ Nginx   │─▶│ FastAPI │─▶│ Postgres│ │
│  │ (TLS)   │  │ (4 wkrs)│  │         │ │
│  └─────────┘  └─────────┘  └─────────┘ │
└─────────────────────────────────────────┘
```

- Single container with multiple workers
- Nginx handles TLS termination
- Use `--workers 4` for multi-core utilization

### Orchestrated (Kubernetes)

```
┌─────────────────────────────────────────────────┐
│ Cluster                                         │
│  ┌─────────────┐                               │
│  │ Ingress     │                               │
│  │ Controller  │                               │
│  └──────┬──────┘                               │
│         │                                       │
│    ┌────┴────┐                                 │
│    ▼         ▼                                 │
│ ┌───────┐ ┌───────┐ ┌───────┐                 │
│ │FastAPI│ │FastAPI│ │FastAPI│  (Replicas)     │
│ │ Pod 1 │ │ Pod 2 │ │ Pod 3 │                 │
│ └───────┘ └───────┘ └───────┘                 │
└─────────────────────────────────────────────────┘
```

- One process per container
- Scaling via replicas (not workers)
- Load balancing at cluster level

---

## Workers Configuration

### Single Server (Multiple Workers)

```dockerfile
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

**Formula**: `workers = (2 × CPU cores) + 1`

### Kubernetes (Single Worker)

```dockerfile
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]
```

Scale via replicas in deployment:
```yaml
spec:
  replicas: 4
```

---

## Reverse Proxy Setup

### Nginx Configuration

```nginx
upstream fastapi {
    server api:8000;
}

server {
    listen 80;
    server_name example.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name example.com;

    ssl_certificate /etc/letsencrypt/live/example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/example.com/privkey.pem;

    location / {
        proxy_pass http://fastapi;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### FastAPI with Proxy Headers

```dockerfile
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
```

The `--proxy-headers` flag tells FastAPI to trust `X-Forwarded-*` headers.

---

## Docker Compose Production

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./certs:/etc/letsencrypt:ro
    depends_on:
      - api
    restart: unless-stopped

  api:
    build:
      context: .
      target: production
    expose:
      - "8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
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
```

---

## Traefik as Reverse Proxy

```yaml
services:
  traefik:
    image: traefik:v3.0
    command:
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
      - "--entrypoints.websecure.address=:443"
      - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
      - "--certificatesresolvers.letsencrypt.acme.email=admin@example.com"
      - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
      - letsencrypt:/letsencrypt

  api:
    build: .
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.api.rule=Host(`api.example.com`)"
      - "traefik.http.routers.api.entrypoints=websecure"
      - "traefik.http.routers.api.tls.certresolver=letsencrypt"

volumes:
  letsencrypt:
```

---

## Health Checks

### Liveness vs Readiness

| Check | Purpose | Action on Failure |
|-------|---------|-------------------|
| Liveness | Is the process running? | Restart container |
| Readiness | Can it serve traffic? | Remove from load balancer |

### FastAPI Endpoints

```python
from fastapi import FastAPI, status

app = FastAPI()

@app.get("/health/live", status_code=status.HTTP_200_OK)
def liveness():
    """Container is alive."""
    return {"status": "alive"}

@app.get("/health/ready", status_code=status.HTTP_200_OK)
def readiness():
    """Ready to serve traffic."""
    # Check database connection, etc.
    return {"status": "ready"}
```

### Kubernetes Probes

```yaml
spec:
  containers:
    - name: api
      livenessProbe:
        httpGet:
          path: /health/live
          port: 8000
        initialDelaySeconds: 5
        periodSeconds: 10
      readinessProbe:
        httpGet:
          path: /health/ready
          port: 8000
        initialDelaySeconds: 5
        periodSeconds: 5
```

---

## Graceful Shutdown

### Why It Matters

When container receives SIGTERM:
1. Stop accepting new requests
2. Complete in-flight requests
3. Clean up resources
4. Exit

### FastAPI Lifespan

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")
    # Close database connections, etc.

app = FastAPI(lifespan=lifespan)
```

### CMD Exec Form (Required)

```dockerfile
# CORRECT - receives SIGTERM directly
CMD ["fastapi", "run", "app/main.py", "--host", "0.0.0.0", "--port", "8000"]

# WRONG - shell intercepts signals
CMD fastapi run app/main.py --host 0.0.0.0 --port 8000
```

### Docker Stop Timeout

```bash
# Default 10 seconds
docker stop mycontainer

# Custom timeout
docker stop --time 30 mycontainer
```

---

## Logging

### Structured Logging

```python
import logging
import json

class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_record)

handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logging.root.addHandler(handler)
```

### Docker Logging Drivers

```yaml
services:
  api:
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"
```

---

## Database Migrations

### Separate Migration Container

```yaml
services:
  migrate:
    build: .
    command: alembic upgrade head
    environment:
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      db:
        condition: service_healthy

  api:
    build: .
    depends_on:
      migrate:
        condition: service_completed_successfully
```

### Kubernetes Init Container

```yaml
spec:
  initContainers:
    - name: migrate
      image: myapp:latest
      command: ["alembic", "upgrade", "head"]
      env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: db-secret
              key: url
  containers:
    - name: api
      image: myapp:latest
```

---

## Production Checklist

### Container
- [ ] Multi-stage build for minimal image
- [ ] Non-root user
- [ ] Health check configured
- [ ] Graceful shutdown (exec form CMD)
- [ ] Structured logging
- [ ] Resource limits set

### Infrastructure
- [ ] TLS termination (Nginx/Traefik/Cloud)
- [ ] Reverse proxy configured
- [ ] Horizontal scaling strategy
- [ ] Database migrations strategy
- [ ] Secrets management (not in image)

### Monitoring
- [ ] Health endpoints exposed
- [ ] Metrics collection (Prometheus)
- [ ] Log aggregation
- [ ] Alerting configured
