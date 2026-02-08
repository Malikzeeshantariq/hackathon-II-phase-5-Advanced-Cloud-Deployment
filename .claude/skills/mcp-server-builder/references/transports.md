# MCP Transports

Configuration and patterns for stdio and HTTP transports.

## Transport Overview

| Transport | Use Case | Clients | Auth | Complexity |
|-----------|----------|---------|------|------------|
| **stdio** | Local servers | Single | None | Simple |
| **HTTP** | Remote servers | Multiple | Required | Complex |

---

## stdio Transport

Standard input/output communication for local servers.

### How It Works
1. Client spawns server as subprocess
2. Server reads JSON-RPC from stdin
3. Server writes JSON-RPC to stdout
4. stderr for logging/debug output

### TypeScript Implementation

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new McpServer({
  name: "my-server",
  version: "1.0.0",
});

// Register tools, resources, prompts...

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);

  // Log to stderr, NOT stdout!
  console.error("Server running on stdio");
}

main();
```

### Python Implementation

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

# Register tools, resources, prompts...

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

### Critical Rules for stdio

**NEVER write to stdout except JSON-RPC messages!**

```typescript
// ❌ BREAKS PROTOCOL
console.log("Debug message");
process.stdout.write("Hello");

// ✅ SAFE
console.error("Debug message");
process.stderr.write("Hello");
```

```python
# ❌ BREAKS PROTOCOL
print("Debug message")

# ✅ SAFE
import sys
print("Debug message", file=sys.stderr)

import logging
logging.info("Debug message")
```

### Claude Desktop Configuration

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/absolute/path/to/build/index.js"],
      "env": {
        "API_KEY": "your-key"
      }
    }
  }
}
```

**Python server:**
```json
{
  "mcpServers": {
    "my-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/server",
        "run",
        "server.py"
      ]
    }
  }
}
```

**Important:**
- Always use absolute paths
- Restart Claude Desktop completely after changes
- Check logs: `tail -f ~/Library/Logs/Claude/mcp*.log`

---

## HTTP Transport (Streamable HTTP)

For remote servers supporting multiple clients.

### How It Works
1. Server exposes HTTP endpoint (e.g., `/mcp`)
2. Clients send POST requests with JSON-RPC
3. Server responds with JSON or SSE stream
4. Optional GET for server-to-client notifications

### TypeScript Implementation

```typescript
import express from "express";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";

const app = express();
app.use(express.json());

const server = new McpServer({
  name: "http-server",
  version: "1.0.0",
});

// Register tools, resources, prompts...

// Session management
const sessions = new Map<string, StreamableHTTPServerTransport>();

app.all("/mcp", async (req, res) => {
  // Validate Origin header (security!)
  const origin = req.headers.origin;
  if (origin && !isAllowedOrigin(origin)) {
    return res.status(403).json({ error: "Forbidden" });
  }

  let sessionId = req.headers["mcp-session-id"] as string;
  let transport = sessions.get(sessionId);

  if (!transport) {
    sessionId = crypto.randomUUID();
    transport = new StreamableHTTPServerTransport({
      sessionId,
    });
    sessions.set(sessionId, transport);
    await server.connect(transport);
  }

  res.setHeader("MCP-Session-Id", sessionId);
  await transport.handleRequest(req, res);
});

app.listen(3000, () => {
  console.log("MCP HTTP server on http://localhost:3000/mcp");
});
```

### Python Implementation

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("http-server")

# Register tools, resources, prompts...

if __name__ == "__main__":
    mcp.run(
        transport="streamable-http",
        host="0.0.0.0",
        port=3000,
    )
```

### Security Requirements

**Origin Validation (CRITICAL):**
```typescript
function isAllowedOrigin(origin: string): boolean {
  const allowed = [
    "https://claude.ai",
    "http://localhost:3000",
  ];
  return allowed.includes(origin);
}

// Return 403 for invalid origins
if (!isAllowedOrigin(origin)) {
  return res.status(403).json({ error: "Forbidden" });
}
```

**Bind to localhost:**
```typescript
// ✅ SAFE - localhost only
app.listen(3000, "127.0.0.1");

// ❌ DANGEROUS - all interfaces
app.listen(3000, "0.0.0.0");
```

### Session Management

**Session ID Header:**
```
MCP-Session-Id: <uuid>
```

**Protocol Version Header:**
```
MCP-Protocol-Version: 2025-11-25
```

**Session termination:**
```http
DELETE /mcp HTTP/1.1
MCP-Session-Id: <session-id>
```

### SSE Streaming

For long-running operations or server-initiated messages:

**Client request:**
```http
POST /mcp HTTP/1.1
Accept: application/json, text/event-stream
Content-Type: application/json
```

**Server response (streaming):**
```http
HTTP/1.1 200 OK
Content-Type: text/event-stream

id: 1
data: {"jsonrpc":"2.0","id":1,"result":{...}}

id: 2
data: {"jsonrpc":"2.0","method":"notification",...}
```

### Resumability

Servers can support reconnection:

```http
GET /mcp HTTP/1.1
Accept: text/event-stream
Last-Event-ID: <previous-id>
```

Server replays messages after the last event ID.

---

## Transport Selection Guide

| Requirement | Recommendation |
|-------------|----------------|
| Claude Desktop integration | stdio |
| Single user, local | stdio |
| Multiple clients | HTTP |
| Remote access needed | HTTP |
| Simple prototype | stdio |
| Production deployment | HTTP with auth |

---

## Connection Configuration

### Claude Code CLI

```bash
# Add HTTP server
claude mcp add --transport http my-server http://localhost:3000/mcp

# Add stdio server
claude mcp add my-server node /path/to/server.js
```

### Programmatic Connection

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const transport = new StdioClientTransport({
  command: "node",
  args: ["/path/to/server.js"],
});

const client = new Client({ name: "my-client", version: "1.0.0" });
await client.connect(transport);

// List tools
const tools = await client.listTools();
```

---

## Troubleshooting

### stdio Issues

| Problem | Solution |
|---------|----------|
| Server not found | Check absolute path |
| No tools showing | Verify server starts without errors |
| Broken communication | Check for stdout pollution |
| Crashes on start | Check Claude logs for errors |

### HTTP Issues

| Problem | Solution |
|---------|----------|
| 403 Forbidden | Check Origin validation |
| Connection refused | Verify port and host binding |
| Session errors | Check session ID handling |
| Timeout | Increase client timeout |

### Debug Commands

```bash
# Check Claude Desktop logs (macOS)
tail -f ~/Library/Logs/Claude/mcp*.log

# Test server manually
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | node build/index.js

# Test HTTP endpoint
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```
