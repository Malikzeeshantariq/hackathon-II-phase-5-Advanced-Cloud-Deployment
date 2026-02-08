# Production Deployment Patterns

Best practices for deploying MCP servers in production environments.

## Architecture Patterns

### Single-Purpose Servers
```
✅ Good: One server per domain
- user-management-mcp
- analytics-mcp
- notification-mcp

❌ Bad: Monolithic server
- mega-server (handles everything)
```

**Benefits:**
- Independent scaling
- Isolated failures
- Clear ownership
- Easier maintenance

### Gateway Pattern
```
┌─────────┐     ┌─────────────┐     ┌──────────────┐
│ Client  │────▶│ MCP Gateway │────▶│ MCP Server 1 │
└─────────┘     │             │────▶│ MCP Server 2 │
                │ - Auth      │────▶│ MCP Server 3 │
                │ - Routing   │     └──────────────┘
                │ - Rate Limit│
                └─────────────┘
```

**Use when:**
- Multiple servers
- Centralized auth needed
- Enterprise environments

---

## Environment Configuration

### Environment Variables
```bash
# .env.production
NODE_ENV=production
LOG_LEVEL=info

# Server
SERVER_HOST=0.0.0.0
SERVER_PORT=3000

# Auth
OAUTH_ISSUER=https://auth.example.com
OAUTH_CLIENT_ID=mcp-server
OAUTH_CLIENT_SECRET=${SECRET_FROM_VAULT}

# External APIs
API_BASE_URL=https://api.example.com
API_KEY=${SECRET_FROM_VAULT}

# Database
DATABASE_URL=postgresql://user:pass@host:5432/db

# Monitoring
SENTRY_DSN=https://xxx@sentry.io/123
```

### Configuration Loading
```typescript
import { z } from "zod";

const ConfigSchema = z.object({
  nodeEnv: z.enum(["development", "production", "test"]),
  logLevel: z.enum(["debug", "info", "warn", "error"]),
  server: z.object({
    host: z.string().default("127.0.0.1"),
    port: z.number().default(3000),
  }),
  oauth: z.object({
    issuer: z.string().url(),
    clientId: z.string(),
    clientSecret: z.string(),
  }),
});

const config = ConfigSchema.parse({
  nodeEnv: process.env.NODE_ENV,
  logLevel: process.env.LOG_LEVEL,
  server: {
    host: process.env.SERVER_HOST,
    port: parseInt(process.env.SERVER_PORT || "3000"),
  },
  oauth: {
    issuer: process.env.OAUTH_ISSUER,
    clientId: process.env.OAUTH_CLIENT_ID,
    clientSecret: process.env.OAUTH_CLIENT_SECRET,
  },
});
```

---

## Health Checks

### Basic Health Endpoint
```typescript
app.get("/health", (req, res) => {
  res.json({ status: "healthy" });
});
```

### Comprehensive Health Check
```typescript
app.get("/health", async (req, res) => {
  const checks = {
    server: "healthy",
    database: await checkDatabase(),
    cache: await checkCache(),
    externalApi: await checkExternalApi(),
  };

  const isHealthy = Object.values(checks).every(
    (status) => status === "healthy"
  );

  res.status(isHealthy ? 200 : 503).json({
    status: isHealthy ? "healthy" : "unhealthy",
    checks,
    timestamp: new Date().toISOString(),
  });
});

async function checkDatabase(): Promise<string> {
  try {
    await db.query("SELECT 1");
    return "healthy";
  } catch {
    return "unhealthy";
  }
}
```

### Kubernetes Probes
```yaml
apiVersion: v1
kind: Pod
spec:
  containers:
    - name: mcp-server
      livenessProbe:
        httpGet:
          path: /health
          port: 3000
        initialDelaySeconds: 10
        periodSeconds: 10
      readinessProbe:
        httpGet:
          path: /health
          port: 3000
        initialDelaySeconds: 5
        periodSeconds: 5
```

---

## Monitoring & Observability

### Structured Logging
```typescript
import pino from "pino";

const logger = pino({
  level: process.env.LOG_LEVEL || "info",
  formatters: {
    level: (label) => ({ level: label }),
  },
  timestamp: pino.stdTimeFunctions.isoTime,
});

// Log with context
logger.info({
  event: "tool_called",
  tool: "search_users",
  clientId: context.clientId,
  duration: 150,
}, "Tool execution completed");
```

### Metrics (Prometheus)
```typescript
import { Registry, Counter, Histogram } from "prom-client";

const register = new Registry();

const toolCallsTotal = new Counter({
  name: "mcp_tool_calls_total",
  help: "Total tool calls",
  labelNames: ["tool", "status"],
  registers: [register],
});

const toolDuration = new Histogram({
  name: "mcp_tool_duration_seconds",
  help: "Tool execution duration",
  labelNames: ["tool"],
  buckets: [0.01, 0.05, 0.1, 0.5, 1, 5],
  registers: [register],
});

// Usage
server.registerTool("my_tool", {}, async (params) => {
  const timer = toolDuration.startTimer({ tool: "my_tool" });
  try {
    const result = await execute(params);
    toolCallsTotal.inc({ tool: "my_tool", status: "success" });
    return result;
  } catch (error) {
    toolCallsTotal.inc({ tool: "my_tool", status: "error" });
    throw error;
  } finally {
    timer();
  }
});

// Metrics endpoint
app.get("/metrics", async (req, res) => {
  res.set("Content-Type", register.contentType);
  res.end(await register.metrics());
});
```

### Error Tracking (Sentry)
```typescript
import * as Sentry from "@sentry/node";

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  environment: process.env.NODE_ENV,
  tracesSampleRate: 0.1,
});

server.registerTool("risky_tool", {}, async (params) => {
  try {
    return await riskyOperation(params);
  } catch (error) {
    Sentry.captureException(error, {
      tags: { tool: "risky_tool" },
      extra: { params },
    });
    throw error;
  }
});
```

---

## Error Handling

### Graceful Degradation
```typescript
async function fetchWithFallback<T>(
  primary: () => Promise<T>,
  fallback: () => Promise<T>,
  fallbackOnError: boolean = true
): Promise<T> {
  try {
    return await primary();
  } catch (error) {
    if (fallbackOnError) {
      console.error("Primary failed, using fallback:", error);
      return await fallback();
    }
    throw error;
  }
}

server.registerTool("get_data", {}, async () => {
  const data = await fetchWithFallback(
    () => fetchFromApi(),
    () => fetchFromCache()
  );
  return { content: [{ type: "text", text: JSON.stringify(data) }] };
});
```

### Circuit Breaker
```typescript
import CircuitBreaker from "opossum";

const breaker = new CircuitBreaker(fetchFromApi, {
  timeout: 5000,
  errorThresholdPercentage: 50,
  resetTimeout: 30000,
});

breaker.on("open", () => console.log("Circuit opened"));
breaker.on("halfOpen", () => console.log("Circuit half-open"));
breaker.on("close", () => console.log("Circuit closed"));

server.registerTool("api_call", {}, async (params) => {
  try {
    const result = await breaker.fire(params);
    return { content: [{ type: "text", text: JSON.stringify(result) }] };
  } catch (error) {
    if (error.message === "Breaker is open") {
      return {
        content: [{ type: "text", text: "Service temporarily unavailable" }],
        isError: true,
      };
    }
    throw error;
  }
});
```

---

## Deployment

### Docker
```dockerfile
# Dockerfile
FROM node:20-alpine AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /app
COPY --from=builder /app/build ./build
COPY --from=builder /app/node_modules ./node_modules
COPY package*.json ./

USER node
EXPOSE 3000
CMD ["node", "build/index.js"]
```

```yaml
# docker-compose.yml
version: "3.8"
services:
  mcp-server:
    build: .
    ports:
      - "3000:3000"
    environment:
      - NODE_ENV=production
      - LOG_LEVEL=info
    env_file:
      - .env.production
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Kubernetes
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mcp-server
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mcp-server
  template:
    metadata:
      labels:
        app: mcp-server
    spec:
      containers:
        - name: mcp-server
          image: mcp-server:latest
          ports:
            - containerPort: 3000
          resources:
            requests:
              memory: "256Mi"
              cpu: "250m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          envFrom:
            - secretRef:
                name: mcp-server-secrets
          livenessProbe:
            httpGet:
              path: /health
              port: 3000
          readinessProbe:
            httpGet:
              path: /health
              port: 3000
---
apiVersion: v1
kind: Service
metadata:
  name: mcp-server
spec:
  selector:
    app: mcp-server
  ports:
    - port: 80
      targetPort: 3000
  type: ClusterIP
```

---

## Scaling

### Horizontal Scaling
- Stateless server design
- Session affinity or shared session store
- Load balancer configuration

### Connection Pooling
```typescript
import { Pool } from "pg";

const pool = new Pool({
  connectionString: process.env.DATABASE_URL,
  max: 20,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 2000,
});
```

### Caching
```typescript
import Redis from "ioredis";

const redis = new Redis(process.env.REDIS_URL);

async function cachedFetch<T>(
  key: string,
  fetch: () => Promise<T>,
  ttlSeconds: number = 300
): Promise<T> {
  const cached = await redis.get(key);
  if (cached) {
    return JSON.parse(cached);
  }

  const data = await fetch();
  await redis.setex(key, ttlSeconds, JSON.stringify(data));
  return data;
}
```

---

## Security Hardening

### Production Checklist
- [ ] HTTPS only (terminate at load balancer)
- [ ] Secrets in secret manager (not env vars)
- [ ] Rate limiting enabled
- [ ] Input validation on all endpoints
- [ ] Output sanitization
- [ ] Audit logging enabled
- [ ] Security headers configured
- [ ] Dependencies up to date
- [ ] Container runs as non-root
- [ ] Network policies in place
