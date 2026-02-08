# API Wrapper Patterns

Patterns for wrapping REST and GraphQL APIs as MCP servers.

## REST API Wrapper

### Basic Structure

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const API_BASE = process.env.API_BASE_URL || "https://api.example.com";
const API_KEY = process.env.API_KEY;

const server = new McpServer({
  name: "example-api",
  version: "1.0.0",
});

// Reusable HTTP client
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${API_BASE}${endpoint}`;

  const response = await fetch(url, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_KEY}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`API error ${response.status}: ${error}`);
  }

  return response.json();
}
```

### CRUD Operations

```typescript
// CREATE
server.registerTool(
  "create_item",
  {
    description: "Create a new item",
    inputSchema: {
      name: z.string().describe("Item name"),
      description: z.string().optional().describe("Item description"),
    },
  },
  async ({ name, description }) => {
    const item = await apiRequest("/items", {
      method: "POST",
      body: JSON.stringify({ name, description }),
    });

    return {
      content: [{ type: "text", text: JSON.stringify(item, null, 2) }],
    };
  }
);

// READ (single)
server.registerTool(
  "get_item",
  {
    description: "Get an item by ID",
    inputSchema: {
      id: z.string().describe("Item ID"),
    },
  },
  async ({ id }) => {
    const item = await apiRequest(`/items/${encodeURIComponent(id)}`);

    return {
      content: [{ type: "text", text: JSON.stringify(item, null, 2) }],
    };
  }
);

// READ (list with filters)
server.registerTool(
  "list_items",
  {
    description: "List items with optional filters",
    inputSchema: {
      status: z.enum(["active", "inactive", "all"]).optional(),
      limit: z.number().min(1).max(100).default(20),
      offset: z.number().min(0).default(0),
      search: z.string().optional().describe("Search query"),
    },
  },
  async ({ status, limit, offset, search }) => {
    const params = new URLSearchParams();
    if (status && status !== "all") params.set("status", status);
    params.set("limit", String(limit));
    params.set("offset", String(offset));
    if (search) params.set("q", search);

    const items = await apiRequest(`/items?${params}`);

    return {
      content: [{ type: "text", text: JSON.stringify(items, null, 2) }],
    };
  }
);

// UPDATE
server.registerTool(
  "update_item",
  {
    description: "Update an existing item",
    inputSchema: {
      id: z.string().describe("Item ID"),
      name: z.string().optional().describe("New name"),
      description: z.string().optional().describe("New description"),
    },
  },
  async ({ id, ...updates }) => {
    const item = await apiRequest(`/items/${encodeURIComponent(id)}`, {
      method: "PATCH",
      body: JSON.stringify(updates),
    });

    return {
      content: [{ type: "text", text: JSON.stringify(item, null, 2) }],
    };
  }
);

// DELETE
server.registerTool(
  "delete_item",
  {
    description: "Delete an item",
    inputSchema: {
      id: z.string().describe("Item ID"),
    },
  },
  async ({ id }) => {
    await apiRequest(`/items/${encodeURIComponent(id)}`, {
      method: "DELETE",
    });

    return {
      content: [{ type: "text", text: `Item ${id} deleted successfully` }],
    };
  }
);
```

### Python REST Wrapper

```python
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("example-api")

API_BASE = os.environ.get("API_BASE_URL", "https://api.example.com")
API_KEY = os.environ["API_KEY"]


async def api_request(
    endpoint: str,
    method: str = "GET",
    data: dict | None = None,
) -> dict:
    """Make authenticated API request."""
    async with httpx.AsyncClient() as client:
        response = await client.request(
            method,
            f"{API_BASE}{endpoint}",
            headers={
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
            },
            json=data,
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


@mcp.tool()
async def create_item(name: str, description: str = "") -> dict:
    """Create a new item.

    Args:
        name: Item name
        description: Optional description
    """
    return await api_request(
        "/items",
        method="POST",
        data={"name": name, "description": description},
    )


@mcp.tool()
async def get_item(item_id: str) -> dict:
    """Get item by ID.

    Args:
        item_id: The item identifier
    """
    return await api_request(f"/items/{item_id}")


@mcp.tool()
async def list_items(
    status: str = "all",
    limit: int = 20,
    search: str = "",
) -> dict:
    """List items with filters.

    Args:
        status: Filter by status (active, inactive, all)
        limit: Maximum results (1-100)
        search: Search query
    """
    params = f"?limit={limit}"
    if status != "all":
        params += f"&status={status}"
    if search:
        params += f"&q={search}"

    return await api_request(f"/items{params}")
```

---

## GraphQL API Wrapper

### TypeScript GraphQL Client

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";

const GRAPHQL_ENDPOINT = process.env.GRAPHQL_URL;
const API_KEY = process.env.API_KEY;

async function graphqlRequest<T>(
  query: string,
  variables?: Record<string, unknown>
): Promise<T> {
  const response = await fetch(GRAPHQL_ENDPOINT, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${API_KEY}`,
    },
    body: JSON.stringify({ query, variables }),
  });

  const result = await response.json();

  if (result.errors) {
    throw new Error(result.errors[0].message);
  }

  return result.data;
}

// Query tool
server.registerTool(
  "get_user",
  {
    description: "Get user details by ID",
    inputSchema: {
      userId: z.string().describe("User ID"),
    },
  },
  async ({ userId }) => {
    const query = `
      query GetUser($id: ID!) {
        user(id: $id) {
          id
          name
          email
          createdAt
          posts {
            id
            title
          }
        }
      }
    `;

    const data = await graphqlRequest(query, { id: userId });

    return {
      content: [{ type: "text", text: JSON.stringify(data.user, null, 2) }],
    };
  }
);

// Mutation tool
server.registerTool(
  "create_post",
  {
    description: "Create a new post",
    inputSchema: {
      title: z.string().describe("Post title"),
      content: z.string().describe("Post content"),
      authorId: z.string().describe("Author user ID"),
    },
  },
  async ({ title, content, authorId }) => {
    const mutation = `
      mutation CreatePost($input: CreatePostInput!) {
        createPost(input: $input) {
          id
          title
          content
          author {
            name
          }
          createdAt
        }
      }
    `;

    const data = await graphqlRequest(mutation, {
      input: { title, content, authorId },
    });

    return {
      content: [{ type: "text", text: JSON.stringify(data.createPost, null, 2) }],
    };
  }
);
```

---

## Error Handling Patterns

### Typed Error Responses

```typescript
interface ApiError {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

async function apiRequestWithErrorHandling<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<{ data?: T; error?: ApiError }> {
  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${API_KEY}`,
        ...options.headers,
      },
    });

    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));

      return {
        error: {
          code: `HTTP_${response.status}`,
          message: errorBody.message || response.statusText,
          details: errorBody,
        },
      };
    }

    return { data: await response.json() };
  } catch (error) {
    return {
      error: {
        code: "NETWORK_ERROR",
        message: error instanceof Error ? error.message : "Unknown error",
      },
    };
  }
}

// Usage in tool
server.registerTool("safe_get_item", {}, async ({ id }) => {
  const { data, error } = await apiRequestWithErrorHandling(`/items/${id}`);

  if (error) {
    return {
      content: [
        {
          type: "text",
          text: `Error: ${error.code} - ${error.message}`,
        },
      ],
      isError: true,
    };
  }

  return {
    content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
  };
});
```

### Retry Logic

```typescript
async function withRetry<T>(
  fn: () => Promise<T>,
  maxRetries: number = 3,
  delayMs: number = 1000
): Promise<T> {
  let lastError: Error;

  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await fn();
    } catch (error) {
      lastError = error instanceof Error ? error : new Error(String(error));

      // Don't retry client errors (4xx)
      if (lastError.message.includes("HTTP_4")) {
        throw lastError;
      }

      if (attempt < maxRetries - 1) {
        await new Promise((r) => setTimeout(r, delayMs * (attempt + 1)));
      }
    }
  }

  throw lastError!;
}
```

---

## Rate Limiting

### Client-Side Rate Limiting

```typescript
class RateLimiter {
  private queue: Array<() => void> = [];
  private running = 0;

  constructor(
    private maxConcurrent: number = 5,
    private minDelayMs: number = 100
  ) {}

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      const run = async () => {
        this.running++;
        try {
          const result = await fn();
          resolve(result);
        } catch (error) {
          reject(error);
        } finally {
          this.running--;
          setTimeout(() => this.processQueue(), this.minDelayMs);
        }
      };

      if (this.running < this.maxConcurrent) {
        run();
      } else {
        this.queue.push(run);
      }
    });
  }

  private processQueue() {
    if (this.queue.length > 0 && this.running < this.maxConcurrent) {
      const next = this.queue.shift();
      next?.();
    }
  }
}

const rateLimiter = new RateLimiter(5, 200);

// Use in tools
server.registerTool("rate_limited_call", {}, async (params) => {
  return rateLimiter.execute(() => apiRequest("/endpoint", params));
});
```

---

## Pagination Handling

### Cursor-Based Pagination

```typescript
server.registerTool(
  "list_all_items",
  {
    description: "List all items (handles pagination automatically)",
    inputSchema: {
      filter: z.string().optional(),
      maxItems: z.number().default(1000).describe("Maximum items to fetch"),
    },
  },
  async ({ filter, maxItems }) => {
    const allItems: unknown[] = [];
    let cursor: string | undefined;

    while (allItems.length < maxItems) {
      const params = new URLSearchParams();
      if (filter) params.set("filter", filter);
      if (cursor) params.set("cursor", cursor);
      params.set("limit", "100");

      const response = await apiRequest<{
        items: unknown[];
        nextCursor?: string;
      }>(`/items?${params}`);

      allItems.push(...response.items);

      if (!response.nextCursor || response.items.length === 0) {
        break;
      }

      cursor = response.nextCursor;
    }

    return {
      content: [
        {
          type: "text",
          text: JSON.stringify(
            { items: allItems.slice(0, maxItems), count: allItems.length },
            null,
            2
          ),
        },
      ],
    };
  }
);
```

---

## Caching

### Simple In-Memory Cache

```typescript
const cache = new Map<string, { data: unknown; expiresAt: number }>();

function getCached<T>(key: string): T | undefined {
  const entry = cache.get(key);
  if (entry && entry.expiresAt > Date.now()) {
    return entry.data as T;
  }
  cache.delete(key);
  return undefined;
}

function setCache(key: string, data: unknown, ttlSeconds: number) {
  cache.set(key, {
    data,
    expiresAt: Date.now() + ttlSeconds * 1000,
  });
}

server.registerTool("cached_get_item", {}, async ({ id }) => {
  const cacheKey = `item:${id}`;

  let item = getCached(cacheKey);
  if (!item) {
    item = await apiRequest(`/items/${id}`);
    setCache(cacheKey, item, 300); // 5 minute cache
  }

  return {
    content: [{ type: "text", text: JSON.stringify(item, null, 2) }],
  };
});
```

---

## Complete Example: GitHub API Wrapper

```typescript
const server = new McpServer({
  name: "github-api",
  version: "1.0.0",
});

const GITHUB_TOKEN = process.env.GITHUB_TOKEN;

async function github<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`https://api.github.com${endpoint}`, {
    ...options,
    headers: {
      Accept: "application/vnd.github.v3+json",
      Authorization: `Bearer ${GITHUB_TOKEN}`,
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`GitHub API error: ${response.status}`);
  }

  return response.json();
}

server.registerTool(
  "get_repo",
  {
    description: "Get GitHub repository information",
    inputSchema: {
      owner: z.string().describe("Repository owner"),
      repo: z.string().describe("Repository name"),
    },
  },
  async ({ owner, repo }) => {
    const data = await github(`/repos/${owner}/${repo}`);
    return {
      content: [{ type: "text", text: JSON.stringify(data, null, 2) }],
    };
  }
);

server.registerTool(
  "list_issues",
  {
    description: "List repository issues",
    inputSchema: {
      owner: z.string(),
      repo: z.string(),
      state: z.enum(["open", "closed", "all"]).default("open"),
      labels: z.string().optional().describe("Comma-separated labels"),
    },
  },
  async ({ owner, repo, state, labels }) => {
    const params = new URLSearchParams({ state });
    if (labels) params.set("labels", labels);

    const issues = await github(`/repos/${owner}/${repo}/issues?${params}`);
    return {
      content: [{ type: "text", text: JSON.stringify(issues, null, 2) }],
    };
  }
);

server.registerTool(
  "create_issue",
  {
    description: "Create a new issue",
    inputSchema: {
      owner: z.string(),
      repo: z.string(),
      title: z.string().describe("Issue title"),
      body: z.string().optional().describe("Issue body (markdown)"),
      labels: z.array(z.string()).optional(),
    },
  },
  async ({ owner, repo, title, body, labels }) => {
    const issue = await github(`/repos/${owner}/${repo}/issues`, {
      method: "POST",
      body: JSON.stringify({ title, body, labels }),
    });
    return {
      content: [{ type: "text", text: JSON.stringify(issue, null, 2) }],
    };
  }
);
```
