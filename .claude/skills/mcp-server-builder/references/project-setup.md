# MCP Server Project Setup

Complete templates for TypeScript and Python MCP server projects.

## TypeScript Project

### Directory Structure
```
my-mcp-server/
├── src/
│   └── index.ts
├── package.json
├── tsconfig.json
└── .env (optional)
```

### package.json
```json
{
  "name": "my-mcp-server",
  "version": "1.0.0",
  "type": "module",
  "bin": {
    "my-mcp-server": "./build/index.js"
  },
  "scripts": {
    "build": "tsc && chmod 755 build/index.js",
    "dev": "tsc --watch",
    "start": "node build/index.js",
    "inspect": "npx @modelcontextprotocol/inspector node build/index.js"
  },
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "zod": "^3.23.0"
  },
  "devDependencies": {
    "@types/node": "^20.0.0",
    "typescript": "^5.0.0"
  }
}
```

### tsconfig.json
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "module": "Node16",
    "moduleResolution": "Node16",
    "outDir": "./build",
    "rootDir": "./src",
    "strict": true,
    "esModuleInterop": true,
    "skipLibCheck": true,
    "forceConsistentCasingInFileNames": true,
    "declaration": true,
    "declarationMap": true,
    "sourceMap": true
  },
  "include": ["src/**/*"],
  "exclude": ["node_modules", "build"]
}
```

### src/index.ts (Hello World)
```typescript
#!/usr/bin/env node
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({
  name: "my-mcp-server",
  version: "1.0.0",
});

// Register a simple tool
server.registerTool(
  "hello",
  {
    description: "Say hello to someone",
    inputSchema: {
      name: z.string().describe("Name to greet"),
    },
  },
  async ({ name }) => {
    return {
      content: [
        {
          type: "text",
          text: `Hello, ${name}! Welcome to MCP.`,
        },
      ],
    };
  }
);

async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("MCP Server running on stdio");
}

main().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
```

### Build and Run
```bash
npm install
npm run build
npm run inspect  # Test with Inspector
```

---

## Python Project

### Directory Structure
```
my-mcp-server/
├── src/
│   └── server.py
├── pyproject.toml
└── .env (optional)
```

### pyproject.toml
```toml
[project]
name = "my-mcp-server"
version = "1.0.0"
description = "An MCP server"
requires-python = ">=3.10"
dependencies = [
    "mcp[cli]>=1.2.0",
    "httpx>=0.27.0",
]

[project.scripts]
my-mcp-server = "src.server:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src"]
```

### src/server.py (Hello World)
```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("my-mcp-server")


@mcp.tool()
async def hello(name: str) -> str:
    """Say hello to someone.

    Args:
        name: Name to greet
    """
    return f"Hello, {name}! Welcome to MCP."


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
```

### Setup and Run
```bash
# Using uv (recommended)
uv init my-mcp-server
cd my-mcp-server
uv add "mcp[cli]" httpx
uv run src/server.py

# Test with Inspector
npx @modelcontextprotocol/inspector uv run src/server.py
```

---

## Environment Variables

Create `.env` for configuration:
```bash
# API Keys
API_KEY=your-api-key-here
API_BASE_URL=https://api.example.com

# Server Config
SERVER_NAME=my-mcp-server
LOG_LEVEL=info

# Auth (for HTTP transport)
OAUTH_CLIENT_ID=your-client-id
OAUTH_CLIENT_SECRET=your-client-secret
```

### Loading Environment Variables

**TypeScript:**
```typescript
import "dotenv/config";

const API_KEY = process.env.API_KEY;
if (!API_KEY) {
  throw new Error("API_KEY environment variable required");
}
```

**Python:**
```python
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    raise ValueError("API_KEY environment variable required")
```

---

## Claude Desktop Configuration

After building, add to `claude_desktop_config.json`:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "my-mcp-server": {
      "command": "node",
      "args": ["/absolute/path/to/my-mcp-server/build/index.js"],
      "env": {
        "API_KEY": "your-api-key"
      }
    }
  }
}
```

**Python server:**
```json
{
  "mcpServers": {
    "my-mcp-server": {
      "command": "uv",
      "args": [
        "--directory",
        "/absolute/path/to/my-mcp-server",
        "run",
        "src/server.py"
      ]
    }
  }
}
```

**Important:** Always use absolute paths. Restart Claude Desktop completely after changes.
