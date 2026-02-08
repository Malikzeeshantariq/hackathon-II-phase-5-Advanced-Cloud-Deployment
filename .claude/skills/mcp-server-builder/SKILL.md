---
name: mcp-server-builder
description: |
  Build MCP (Model Context Protocol) servers from hello world to production systems.
  This skill should be used when users want to create MCP servers that expose tools,
  resources, or prompts to AI applications like Claude. Covers TypeScript and Python
  implementations, stdio and HTTP transports, OAuth 2.1 security, and production patterns.
---

# MCP Server Builder

Build Model Context Protocol servers that connect AI applications to external systems.

## What is MCP?

MCP is an open standard (like "USB-C for AI") enabling AI apps to access:
- **Tools**: Executable functions (query APIs, run code, perform actions)
- **Resources**: Data sources (files, databases, API responses)
- **Prompts**: Reusable interaction templates

## Before Implementation

| Source | Gather |
|--------|--------|
| **Codebase** | Existing patterns, dependencies, project structure |
| **Conversation** | User's specific API/data to wrap, auth requirements |
| **Skill References** | Implementation patterns from `references/` |
| **User Guidelines** | Project conventions, team standards |

Only ask user for THEIR requirements. Domain expertise is embedded in this skill.

## Clarifications

Before building, clarify:

| Question | Why |
|----------|-----|
| What external API/data source to expose? | Determines tool/resource design |
| TypeScript or Python? | SDK and syntax differences |
| Transport: stdio or HTTP? | Local vs remote deployment |
| Auth required? | OAuth 2.1 implementation needed |
| Production or prototype? | Testing, monitoring, error handling depth |

## Implementation Workflow

```
1. Setup Project → 2. Define Capabilities → 3. Implement Handlers → 4. Configure Transport → 5. Test with Inspector → 6. Deploy
```

### Step 1: Project Setup

**TypeScript:**
```bash
mkdir my-mcp-server && cd my-mcp-server
npm init -y
npm install @modelcontextprotocol/sdk zod
npm install -D typescript @types/node
```

**Python:**
```bash
uv init my-mcp-server && cd my-mcp-server
uv add "mcp[cli]" httpx
```

See `references/project-setup.md` for complete templates.

### Step 2: Define Server Capabilities

Decide what to expose:

| Capability | Use When | Example |
|------------|----------|---------|
| **Tools** | Actions with side effects | API calls, calculations, mutations |
| **Resources** | Read-only data access | Files, database records, configs |
| **Prompts** | Reusable templates | Code review prompt, analysis prompt |

### Step 3: Implement Handlers

**TypeScript Pattern:**
```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "my-server",
  version: "1.0.0",
});

// Register a tool
server.registerTool(
  "tool_name",
  {
    description: "What this tool does",
    inputSchema: {
      param: z.string().describe("Parameter description"),
    },
  },
  async ({ param }) => {
    // Implementation
    return {
      content: [{ type: "text", text: "Result" }],
    };
  }
);

// Start server
const transport = new StdioServerTransport();
await server.connect(transport);
```

**Python Pattern:**
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-server")

@mcp.tool()
async def tool_name(param: str) -> str:
    """What this tool does.

    Args:
        param: Parameter description
    """
    # Implementation
    return "Result"

if __name__ == "__main__":
    mcp.run(transport="stdio")
```

See `references/typescript-guide.md` and `references/python-guide.md` for complete patterns.

### Step 4: Configure Transport

| Transport | Use Case | Config |
|-----------|----------|--------|
| **stdio** | Local servers, Claude Desktop | Default, subprocess-based |
| **HTTP** | Remote servers, multi-client | Requires auth, session management |

See `references/transports.md` for transport configuration.

### Step 5: Test with Inspector

```bash
# Test any server
npx @modelcontextprotocol/inspector node build/index.js

# Test Python server
npx @modelcontextprotocol/inspector uv run server.py
```

See `references/testing-debugging.md` for testing strategies.

### Step 6: Deploy

**Claude Desktop config** (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "my-server": {
      "command": "node",
      "args": ["/absolute/path/to/build/index.js"]
    }
  }
}
```

See `references/production-patterns.md` for deployment best practices.

## Tool Design Guidelines

### Good Tool Design
```typescript
server.registerTool(
  "search_users",  // Clear, action-oriented name
  {
    description: "Search for users by name or email in the database",
    inputSchema: {
      query: z.string().min(1).describe("Search term"),
      limit: z.number().optional().default(10).describe("Max results"),
    },
  },
  async ({ query, limit }) => { /* ... */ }
);
```

### Tool Schema Best Practices
- Use descriptive names (verb_noun pattern)
- Write clear descriptions for LLM understanding
- Add `.describe()` to all parameters
- Set sensible defaults with `.default()`
- Validate inputs with Zod/type hints

## Resource Design Guidelines

```typescript
// List resources
server.registerResourceList(async () => ({
  resources: [
    {
      uri: "config://app/settings",
      name: "App Settings",
      mimeType: "application/json",
    },
  ],
}));

// Read resource
server.registerResourceRead(async (uri) => ({
  contents: [
    {
      uri,
      mimeType: "application/json",
      text: JSON.stringify(settings),
    },
  ],
}));
```

## Error Handling

```typescript
// Tool execution errors (business logic)
return {
  content: [{ type: "text", text: "API rate limit exceeded" }],
  isError: true,
};

// Protocol errors (throw for infrastructure issues)
throw new Error("Unknown tool: invalid_name");
```

## Security Checklist

- [ ] Never write to stdout in stdio servers (breaks protocol)
- [ ] Validate all inputs against schemas
- [ ] Implement rate limiting for API calls
- [ ] Use environment variables for secrets
- [ ] Add human-in-the-loop for sensitive operations
- [ ] Sanitize outputs before returning

See `references/security-auth.md` for OAuth 2.1 and security patterns.

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| Monolithic server | Hard to maintain, single failure point | One server per domain/API |
| Token passthrough | Security bypass, audit issues | Validate tokens are for your server |
| stdout logging (stdio) | Breaks JSON-RPC protocol | Use stderr or logging framework |
| Missing error handling | Poor UX, debugging difficulty | Classify and handle all errors |
| Hardcoded secrets | Security risk | Use env vars or secret managers |

## Reference Files

| File | Content |
|------|---------|
| `references/project-setup.md` | Complete project templates |
| `references/typescript-guide.md` | TypeScript SDK patterns |
| `references/python-guide.md` | Python FastMCP patterns |
| `references/tools-resources-prompts.md` | Capability implementation details |
| `references/transports.md` | stdio and HTTP transport config |
| `references/security-auth.md` | OAuth 2.1, security best practices |
| `references/testing-debugging.md` | Inspector, testing strategies |
| `references/production-patterns.md` | Deployment, monitoring, enterprise |
| `references/api-wrapper-patterns.md` | Patterns for wrapping REST/GraphQL APIs |

## Quick Reference

### Message Flow
```
Client → initialize → Server (capabilities)
Client → tools/list → Server (available tools)
Client → tools/call → Server (execute, return result)
```

### JSON-RPC Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": { "name": "tool", "arguments": {...} }
}
```

### Capability Declaration
```json
{
  "capabilities": {
    "tools": { "listChanged": true },
    "resources": { "subscribe": true },
    "prompts": { "listChanged": true }
  }
}
```
