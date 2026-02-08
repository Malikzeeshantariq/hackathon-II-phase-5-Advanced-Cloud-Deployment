# Testing and Debugging MCP Servers

Strategies and tools for testing and debugging MCP servers.

## MCP Inspector

The official interactive testing tool for MCP servers.

### Installation
```bash
# Run directly with npx (no install needed)
npx @modelcontextprotocol/inspector <command>
```

### Testing Local Servers

**TypeScript:**
```bash
npx @modelcontextprotocol/inspector node build/index.js
```

**Python:**
```bash
npx @modelcontextprotocol/inspector uv run server.py
```

**With arguments:**
```bash
npx @modelcontextprotocol/inspector node build/index.js --config /path/to/config.json
```

### Testing npm/PyPI Packages

**npm package:**
```bash
npx @modelcontextprotocol/inspector npx @modelcontextprotocol/server-filesystem /Users/me/Desktop
```

**PyPI package:**
```bash
npx @modelcontextprotocol/inspector uvx mcp-server-git --repository ~/code/repo.git
```

### Inspector Features

| Tab | Purpose |
|-----|---------|
| **Server Connection** | Configure transport, args, env vars |
| **Resources** | List, read, subscribe to resources |
| **Prompts** | List, test prompts with arguments |
| **Tools** | List, execute tools with inputs |
| **Notifications** | View server logs and notifications |

### Testing Workflow

1. **Start development**
   - Launch Inspector with your server
   - Verify basic connectivity
   - Check capability negotiation

2. **Iterative testing**
   - Make server changes
   - Rebuild
   - Reconnect Inspector
   - Test affected features

3. **Edge case testing**
   - Invalid inputs
   - Missing arguments
   - Concurrent operations
   - Error responses

---

## Manual Testing

### Direct stdio Testing

Send JSON-RPC directly to your server:

```bash
# Initialize
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | node build/index.js

# List tools
echo '{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}' | node build/index.js

# Call a tool
echo '{"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"hello","arguments":{"name":"World"}}}' | node build/index.js
```

### HTTP Testing with curl

```bash
# Initialize session
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","capabilities":{},"clientInfo":{"name":"curl","version":"1.0"}}}'

# List tools (with session)
curl -X POST http://localhost:3000/mcp \
  -H "Content-Type: application/json" \
  -H "MCP-Session-Id: <session-id>" \
  -d '{"jsonrpc":"2.0","id":2,"method":"tools/list"}'
```

---

## Unit Testing

### TypeScript with Jest

```typescript
// server.test.ts
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";

describe("MCP Server", () => {
  let server: McpServer;
  let client: Client;

  beforeEach(async () => {
    server = new McpServer({ name: "test", version: "1.0.0" });

    // Register tools
    server.registerTool(
      "add",
      {
        inputSchema: { a: z.number(), b: z.number() },
      },
      async ({ a, b }) => ({
        content: [{ type: "text", text: String(a + b) }],
      })
    );

    // Create in-memory connection
    const [clientTransport, serverTransport] = InMemoryTransport.createLinkedPair();

    client = new Client({ name: "test-client", version: "1.0.0" });

    await Promise.all([
      client.connect(clientTransport),
      server.connect(serverTransport),
    ]);
  });

  afterEach(async () => {
    await client.close();
  });

  test("lists tools", async () => {
    const result = await client.listTools();
    expect(result.tools).toHaveLength(1);
    expect(result.tools[0].name).toBe("add");
  });

  test("calls tool successfully", async () => {
    const result = await client.callTool("add", { a: 2, b: 3 });
    expect(result.content[0].text).toBe("5");
  });

  test("handles invalid input", async () => {
    await expect(client.callTool("add", { a: "not a number" }))
      .rejects.toThrow();
  });
});
```

### Python with pytest

```python
# test_server.py
import pytest
from mcp.server.fastmcp import FastMCP
from mcp.client import Client
from mcp.client.stdio import stdio_client

@pytest.fixture
def mcp_server():
    mcp = FastMCP("test-server")

    @mcp.tool()
    async def add(a: int, b: int) -> int:
        """Add two numbers."""
        return a + b

    return mcp

@pytest.mark.asyncio
async def test_list_tools(mcp_server):
    # Test tool registration
    tools = mcp_server.list_tools()
    assert len(tools) == 1
    assert tools[0].name == "add"

@pytest.mark.asyncio
async def test_call_tool(mcp_server):
    # Test tool execution
    result = await mcp_server.call_tool("add", {"a": 2, "b": 3})
    assert result == 5

@pytest.mark.asyncio
async def test_invalid_input(mcp_server):
    # Test validation
    with pytest.raises(ValueError):
        await mcp_server.call_tool("add", {"a": "not a number"})
```

---

## Integration Testing

### Test with Real Client

```typescript
// integration.test.ts
import { spawn } from "child_process";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

describe("Integration Tests", () => {
  let client: Client;
  let serverProcess: ChildProcess;

  beforeAll(async () => {
    const transport = new StdioClientTransport({
      command: "node",
      args: ["./build/index.js"],
    });

    client = new Client({ name: "integration-test", version: "1.0.0" });
    await client.connect(transport);
  });

  afterAll(async () => {
    await client.close();
  });

  test("full workflow", async () => {
    // List tools
    const tools = await client.listTools();
    expect(tools.tools.length).toBeGreaterThan(0);

    // Call tool
    const result = await client.callTool(tools.tools[0].name, {
      /* args */
    });
    expect(result.isError).toBeFalsy();
  });
});
```

---

## Debugging

### Enable Debug Logging

**TypeScript:**
```typescript
// Set DEBUG environment variable
process.env.DEBUG = "mcp:*";

// Or use a logger
import debug from "debug";
const log = debug("mcp:server");
log("Processing request:", request);
```

**Python:**
```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("mcp")
logger.debug("Processing request: %s", request)
```

### Claude Desktop Logs

```bash
# macOS
tail -f ~/Library/Logs/Claude/mcp*.log

# Watch for errors
tail -f ~/Library/Logs/Claude/mcp*.log | grep -i error
```

### Common Issues

| Symptom | Likely Cause | Solution |
|---------|--------------|----------|
| Server not appearing | Config path wrong | Use absolute paths |
| No tools showing | Server crash on start | Check Claude logs |
| Broken communication | stdout pollution | Use stderr for logs |
| Tool returns error | Unhandled exception | Add try/catch |
| Timeout | Slow operation | Add progress reporting |

### Debug Checklist

1. **Server starts manually?**
   ```bash
   node build/index.js
   # Should see no output (good) or error (bad)
   ```

2. **JSON-RPC works?**
   ```bash
   echo '{"jsonrpc":"2.0","id":1,"method":"initialize",...}' | node build/index.js
   ```

3. **Logs clean?**
   ```bash
   tail -20 ~/Library/Logs/Claude/mcp*.log
   ```

4. **Config valid?**
   ```bash
   cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq .
   ```

---

## Performance Testing

### Load Testing
```typescript
import { performance } from "perf_hooks";

async function loadTest(iterations: number) {
  const times: number[] = [];

  for (let i = 0; i < iterations; i++) {
    const start = performance.now();
    await client.callTool("my_tool", { input: "test" });
    times.push(performance.now() - start);
  }

  const avg = times.reduce((a, b) => a + b) / times.length;
  const max = Math.max(...times);
  const min = Math.min(...times);

  console.log(`Iterations: ${iterations}`);
  console.log(`Avg: ${avg.toFixed(2)}ms`);
  console.log(`Min: ${min.toFixed(2)}ms`);
  console.log(`Max: ${max.toFixed(2)}ms`);
}
```

### Concurrent Testing
```typescript
async function concurrencyTest(concurrent: number) {
  const promises = Array(concurrent)
    .fill(null)
    .map(() => client.callTool("my_tool", { input: "test" }));

  const start = performance.now();
  await Promise.all(promises);
  const duration = performance.now() - start;

  console.log(`${concurrent} concurrent calls: ${duration.toFixed(2)}ms`);
}
```

---

## CI/CD Testing

### GitHub Actions Example

```yaml
name: Test MCP Server

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-node@v4
        with:
          node-version: "20"

      - name: Install dependencies
        run: npm ci

      - name: Build
        run: npm run build

      - name: Run tests
        run: npm test

      - name: Test with Inspector
        run: |
          timeout 30 npx @modelcontextprotocol/inspector \
            node build/index.js \
            --test || true
```
