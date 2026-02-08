# TypeScript MCP Server Guide

Complete patterns for building MCP servers with the TypeScript SDK.

## SDK Installation

```bash
npm install @modelcontextprotocol/sdk zod
```

**Key packages:**
- `@modelcontextprotocol/sdk` - Core MCP functionality
- `zod` - Schema validation (peer dependency)

## Server Initialization

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const server = new McpServer({
  name: "server-name",
  version: "1.0.0",
});

// Connect with stdio transport
const transport = new StdioServerTransport();
await server.connect(transport);
```

## Registering Tools

### Basic Tool
```typescript
import { z } from "zod";

server.registerTool(
  "tool_name",
  {
    description: "Clear description of what this tool does",
    inputSchema: {
      param1: z.string().describe("What this parameter is for"),
      param2: z.number().optional().describe("Optional numeric param"),
    },
  },
  async ({ param1, param2 }) => {
    // Tool implementation
    const result = await doSomething(param1, param2);

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(result, null, 2),
        },
      ],
    };
  }
);
```

### Tool with Complex Schema
```typescript
server.registerTool(
  "search_records",
  {
    description: "Search database records with filters",
    inputSchema: {
      query: z.string().min(1).describe("Search query"),
      filters: z
        .object({
          status: z.enum(["active", "inactive", "all"]).optional(),
          dateFrom: z.string().optional().describe("ISO date string"),
          dateTo: z.string().optional().describe("ISO date string"),
        })
        .optional()
        .describe("Optional filters"),
      limit: z.number().min(1).max(100).default(20).describe("Results limit"),
      offset: z.number().min(0).default(0).describe("Pagination offset"),
    },
  },
  async ({ query, filters, limit, offset }) => {
    const results = await searchDatabase(query, filters, limit, offset);
    return {
      content: [{ type: "text", text: JSON.stringify(results) }],
    };
  }
);
```

### Tool with Error Handling
```typescript
server.registerTool(
  "fetch_data",
  {
    description: "Fetch data from external API",
    inputSchema: {
      endpoint: z.string().url().describe("API endpoint URL"),
    },
  },
  async ({ endpoint }) => {
    try {
      const response = await fetch(endpoint);

      if (!response.ok) {
        return {
          content: [
            {
              type: "text",
              text: `API error: ${response.status} ${response.statusText}`,
            },
          ],
          isError: true,
        };
      }

      const data = await response.json();
      return {
        content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
      };
    } catch (error) {
      return {
        content: [
          {
            type: "text",
            text: `Failed to fetch: ${error instanceof Error ? error.message : "Unknown error"}`,
          },
        ],
        isError: true,
      };
    }
  }
);
```

## Registering Resources

### Static Resource List
```typescript
server.registerResourceList(async () => ({
  resources: [
    {
      uri: "config://app/settings",
      name: "Application Settings",
      description: "Current application configuration",
      mimeType: "application/json",
    },
    {
      uri: "file://logs/latest",
      name: "Latest Logs",
      description: "Most recent application logs",
      mimeType: "text/plain",
    },
  ],
}));
```

### Resource Read Handler
```typescript
server.registerResourceRead(async (uri) => {
  if (uri === "config://app/settings") {
    const settings = await loadSettings();
    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify(settings, null, 2),
        },
      ],
    };
  }

  if (uri === "file://logs/latest") {
    const logs = await readLatestLogs();
    return {
      contents: [
        {
          uri,
          mimeType: "text/plain",
          text: logs,
        },
      ],
    };
  }

  throw new Error(`Unknown resource: ${uri}`);
});
```

### Resource Templates
```typescript
server.registerResourceTemplateList(async () => ({
  resourceTemplates: [
    {
      uriTemplate: "file:///{path}",
      name: "Project Files",
      description: "Access files in the project directory",
      mimeType: "application/octet-stream",
    },
    {
      uriTemplate: "db://users/{id}",
      name: "User Record",
      description: "Fetch user by ID",
      mimeType: "application/json",
    },
  ],
}));
```

## Registering Prompts

```typescript
server.registerPromptList(async () => ({
  prompts: [
    {
      name: "code_review",
      title: "Code Review",
      description: "Review code for quality and best practices",
      arguments: [
        {
          name: "code",
          description: "The code to review",
          required: true,
        },
        {
          name: "language",
          description: "Programming language",
          required: false,
        },
      ],
    },
  ],
}));

server.registerPromptGet(async (name, args) => {
  if (name === "code_review") {
    const code = args?.code || "";
    const language = args?.language || "unknown";

    return {
      description: "Code review prompt",
      messages: [
        {
          role: "user",
          content: {
            type: "text",
            text: `Please review this ${language} code for quality, best practices, and potential issues:\n\n\`\`\`${language}\n${code}\n\`\`\``,
          },
        },
      ],
    };
  }

  throw new Error(`Unknown prompt: ${name}`);
});
```

## HTTP Transport

For remote servers with multiple clients:

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

// Register tools/resources here...

const transport = new StreamableHTTPServerTransport({
  sessionIdGenerator: () => crypto.randomUUID(),
});

app.all("/mcp", async (req, res) => {
  await transport.handleRequest(req, res, server);
});

app.listen(3000, () => {
  console.log("MCP HTTP server running on port 3000");
});
```

## Logging Best Practices

**CRITICAL: Never use console.log() in stdio servers!**

```typescript
// ❌ BAD - Breaks JSON-RPC protocol
console.log("Processing request");

// ✅ GOOD - stderr is safe
console.error("Processing request");

// ✅ BETTER - Use a logging library
import pino from "pino";
const logger = pino({ transport: { target: "pino-pretty" } });
logger.info("Processing request");
```

## Type Definitions

### Tool Result Content Types
```typescript
type TextContent = {
  type: "text";
  text: string;
};

type ImageContent = {
  type: "image";
  data: string; // base64
  mimeType: string;
};

type ResourceContent = {
  type: "resource";
  resource: {
    uri: string;
    mimeType?: string;
    text?: string;
    blob?: string; // base64 for binary
  };
};

type ToolResult = {
  content: (TextContent | ImageContent | ResourceContent)[];
  isError?: boolean;
};
```

## Complete Server Example

```typescript
#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "complete-example",
  version: "1.0.0",
});

// Tool: Calculator
server.registerTool(
  "calculate",
  {
    description: "Perform mathematical calculations",
    inputSchema: {
      expression: z.string().describe("Math expression to evaluate"),
    },
  },
  async ({ expression }) => {
    try {
      // Safe evaluation (use a proper math library in production)
      const result = Function(`"use strict"; return (${expression})`)();
      return {
        content: [{ type: "text", text: `Result: ${result}` }],
      };
    } catch {
      return {
        content: [{ type: "text", text: "Invalid expression" }],
        isError: true,
      };
    }
  }
);

// Resource: Server info
server.registerResourceList(async () => ({
  resources: [
    {
      uri: "info://server",
      name: "Server Info",
      mimeType: "application/json",
    },
  ],
}));

server.registerResourceRead(async (uri) => {
  if (uri === "info://server") {
    return {
      contents: [
        {
          uri,
          mimeType: "application/json",
          text: JSON.stringify({
            name: "complete-example",
            version: "1.0.0",
            uptime: process.uptime(),
          }),
        },
      ],
    };
  }
  throw new Error(`Unknown resource: ${uri}`);
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("Server running");
}

main().catch((e) => {
  console.error("Fatal:", e);
  process.exit(1);
});
```
