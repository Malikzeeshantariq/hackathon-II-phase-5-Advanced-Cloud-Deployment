# Security and Authentication

Comprehensive security patterns and OAuth 2.1 implementation for MCP servers.

## Security Principles

### Defense in Depth
Layer security controls:
1. **Network** - Bind to localhost, use HTTPS
2. **Authentication** - Verify identity
3. **Authorization** - Check permissions
4. **Input validation** - Sanitize all inputs
5. **Output sanitization** - Clean all responses

### Least Privilege
- Request minimal scopes
- Grant minimal permissions
- Limit tool capabilities

---

## Input Validation

**Always validate all inputs!**

### TypeScript with Zod
```typescript
import { z } from "zod";

server.registerTool(
  "query_database",
  {
    inputSchema: {
      // String validation
      query: z.string()
        .min(1)
        .max(1000)
        .describe("SQL query"),

      // Number validation
      limit: z.number()
        .int()
        .min(1)
        .max(100)
        .default(10),

      // Enum validation
      format: z.enum(["json", "csv", "xml"]),

      // URL validation
      endpoint: z.string().url(),

      // Email validation
      email: z.string().email(),

      // Custom validation
      username: z.string()
        .regex(/^[a-zA-Z0-9_]+$/, "Invalid username format"),
    },
  },
  async (params) => { /* ... */ }
);
```

### Python with Pydantic
```python
from pydantic import BaseModel, Field, validator
from typing import Literal


class QueryParams(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    limit: int = Field(10, ge=1, le=100)
    format: Literal["json", "csv", "xml"]

    @validator("query")
    def validate_query(cls, v):
        # Prevent SQL injection
        forbidden = ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT"]
        if any(word in v.upper() for word in forbidden):
            raise ValueError("Forbidden SQL operation")
        return v


@mcp.tool()
async def query_database(params: QueryParams) -> str:
    # params is validated
    ...
```

### Path Traversal Prevention
```typescript
import path from "path";

function validatePath(userPath: string, allowedRoot: string): string {
  const resolved = path.resolve(allowedRoot, userPath);

  // Ensure path stays within allowed directory
  if (!resolved.startsWith(allowedRoot)) {
    throw new Error("Access denied: path outside allowed directory");
  }

  return resolved;
}
```

```python
from pathlib import Path

def validate_path(user_path: str, allowed_root: Path) -> Path:
    resolved = (allowed_root / user_path).resolve()

    if not resolved.is_relative_to(allowed_root):
        raise ValueError("Access denied: path outside allowed directory")

    return resolved
```

---

## Anti-Patterns

### Token Passthrough (FORBIDDEN)
```typescript
// ❌ NEVER DO THIS
server.registerTool("call_api", {}, async ({ token }) => {
  // Passing through user's token without validation
  return await fetch(api, { headers: { Authorization: token } });
});

// ✅ CORRECT - Use server's own credentials
server.registerTool("call_api", {}, async () => {
  const serverToken = process.env.API_TOKEN;
  return await fetch(api, { headers: { Authorization: serverToken } });
});
```

### Hardcoded Secrets (FORBIDDEN)
```typescript
// ❌ NEVER DO THIS
const API_KEY = "sk-1234567890abcdef";

// ✅ CORRECT - Use environment variables
const API_KEY = process.env.API_KEY;
if (!API_KEY) throw new Error("API_KEY required");
```

---

## OAuth 2.1 Implementation

For HTTP transport servers requiring authentication.

### Authorization Flow

```
1. Client → Server (unauthenticated request)
2. Server → 401 + WWW-Authenticate header
3. Client → Fetch resource metadata
4. Client → Fetch authorization server metadata
5. Client → Register dynamically (DCR)
6. Client → User authorization
7. Client → Exchange code for tokens
8. Client → Server (with access token)
```

### Server Setup (TypeScript)

```typescript
import express from "express";
import { requireBearerAuth } from "@modelcontextprotocol/sdk/server/auth/middleware/bearerAuth.js";
import { mcpAuthMetadataRouter } from "@modelcontextprotocol/sdk/server/auth/router.js";

const app = express();

// OAuth metadata endpoints
app.use(mcpAuthMetadataRouter({
  oauthMetadata: {
    issuer: "https://auth.example.com/",
    authorization_endpoint: "https://auth.example.com/authorize",
    token_endpoint: "https://auth.example.com/token",
    introspection_endpoint: "https://auth.example.com/introspect",
    response_types_supported: ["code"],
  },
  resourceServerUrl: new URL("https://mcp.example.com"),
  scopesSupported: ["mcp:tools", "mcp:resources"],
  resourceName: "My MCP Server",
}));

// Token verification
const tokenVerifier = {
  verifyAccessToken: async (token: string) => {
    const response = await fetch("https://auth.example.com/introspect", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: new URLSearchParams({
        token,
        client_id: process.env.OAUTH_CLIENT_ID!,
        client_secret: process.env.OAUTH_CLIENT_SECRET!,
      }),
    });

    const data = await response.json();

    if (!data.active) {
      throw new Error("Token is not active");
    }

    return {
      token,
      clientId: data.client_id,
      scopes: data.scope?.split(" ") || [],
      expiresAt: data.exp,
    };
  },
};

// Apply auth middleware
const authMiddleware = requireBearerAuth({
  verifier: tokenVerifier,
  requiredScopes: ["mcp:tools"],
});

app.post("/mcp", authMiddleware, async (req, res) => {
  // Handle authenticated MCP requests
});
```

### Server Setup (Python)

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.auth.settings import AuthSettings
from pydantic import AnyHttpUrl

mcp = FastMCP(
    name="secure-server",
    host="localhost",
    port=3000,
    auth=AuthSettings(
        issuer_url=AnyHttpUrl("https://auth.example.com/"),
        required_scopes=["mcp:tools"],
        resource_server_url=AnyHttpUrl("https://mcp.example.com"),
    ),
)
```

### Keycloak Setup

```bash
# Start Keycloak
docker run -p 8080:8080 \
  -e KC_BOOTSTRAP_ADMIN_USERNAME=admin \
  -e KC_BOOTSTRAP_ADMIN_PASSWORD=admin \
  quay.io/keycloak/keycloak start-dev
```

1. Create realm
2. Create client (confidential)
3. Add `mcp:tools` scope
4. Configure audience mapper

---

## Session Security

### Secure Session IDs
```typescript
import crypto from "crypto";

// ✅ Cryptographically secure
const sessionId = crypto.randomUUID();

// ❌ Predictable - NEVER use
const sessionId = `session-${Date.now()}`;
const sessionId = `user-${userId}`;
```

### Session Binding
```typescript
// Bind session to user
const sessionId = `${userId}:${crypto.randomUUID()}`;

// Extract user from token, not from client
const userId = verifiedToken.sub; // From JWT
```

### Session Expiration
```typescript
const sessions = new Map<string, { transport: Transport; expiresAt: number }>();

function createSession(transport: Transport): string {
  const sessionId = crypto.randomUUID();
  const expiresAt = Date.now() + 3600 * 1000; // 1 hour

  sessions.set(sessionId, { transport, expiresAt });
  return sessionId;
}

// Cleanup expired sessions
setInterval(() => {
  const now = Date.now();
  for (const [id, session] of sessions) {
    if (session.expiresAt < now) {
      sessions.delete(id);
    }
  }
}, 60 * 1000);
```

---

## Rate Limiting

```typescript
import rateLimit from "express-rate-limit";

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: { error: "Too many requests" },
});

app.use("/mcp", limiter);
```

### Per-Tool Rate Limiting
```typescript
const toolLimits = new Map<string, number>();

server.registerTool("expensive_operation", {}, async (params, context) => {
  const clientId = context.clientId;
  const key = `${clientId}:expensive_operation`;

  const count = toolLimits.get(key) || 0;
  if (count >= 10) {
    return {
      content: [{ type: "text", text: "Rate limit exceeded" }],
      isError: true,
    };
  }

  toolLimits.set(key, count + 1);
  // Reset after 1 hour
  setTimeout(() => toolLimits.delete(key), 3600 * 1000);

  // Execute tool...
});
```

---

## Security Checklist

### Server Configuration
- [ ] Bind to localhost for local servers
- [ ] Use HTTPS for remote servers
- [ ] Validate Origin header
- [ ] Implement proper CORS

### Authentication
- [ ] Use OAuth 2.1 for HTTP transport
- [ ] Validate tokens on every request
- [ ] Use short-lived access tokens
- [ ] Implement token refresh

### Authorization
- [ ] Check scopes before operations
- [ ] Implement per-tool permissions
- [ ] Use least privilege principle

### Input Handling
- [ ] Validate all inputs with schemas
- [ ] Prevent path traversal
- [ ] Sanitize SQL queries
- [ ] Escape special characters

### Secrets Management
- [ ] Use environment variables
- [ ] Never commit secrets to git
- [ ] Rotate credentials regularly
- [ ] Use secret managers in production

### Logging
- [ ] Never log tokens or secrets
- [ ] Log security events
- [ ] Implement audit trails
- [ ] Redact sensitive data

---

## Common Vulnerabilities

| Vulnerability | Prevention |
|---------------|------------|
| SQL Injection | Parameterized queries, ORM |
| Path Traversal | Validate paths against allowed roots |
| Command Injection | Never use shell with user input |
| XSS | Escape output in prompts |
| SSRF | Validate URLs, use allowlists |
| Token Theft | HTTPS, secure storage, short expiry |
