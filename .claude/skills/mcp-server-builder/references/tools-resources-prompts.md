# Tools, Resources, and Prompts

Deep dive into MCP's three core capabilities.

## Tools

**Purpose:** Executable functions that AI can invoke to perform actions.

### When to Use Tools
- Querying external APIs
- Performing calculations
- Executing database queries
- File operations with side effects
- Any action that changes state

### Tool Definition Structure

```json
{
  "name": "tool_name",
  "title": "Human-Readable Title",
  "description": "Clear description for LLM understanding",
  "inputSchema": {
    "type": "object",
    "properties": {
      "param": {
        "type": "string",
        "description": "Parameter description"
      }
    },
    "required": ["param"]
  },
  "outputSchema": { /* optional */ }
}
```

### Tool Naming Conventions
```
✅ Good names:
- get_weather
- search_users
- create_document
- update_settings
- delete_record

❌ Bad names:
- doThing
- process
- handle
- execute
```

### Tool Response Format

```json
{
  "content": [
    {
      "type": "text",
      "text": "Result text or JSON"
    }
  ],
  "isError": false
}
```

**Content types:**
- `text` - Plain text or JSON string
- `image` - Base64-encoded image with mimeType
- `resource` - Embedded resource content
- `resource_link` - URI reference to a resource

### Error Responses

**Business logic errors** (recoverable):
```json
{
  "content": [{ "type": "text", "text": "User not found" }],
  "isError": true
}
```

**Infrastructure errors** (throw exception):
```typescript
throw new Error("Database connection failed");
```

### Output Schema (Optional)

Enable structured responses:
```typescript
server.registerTool(
  "get_user",
  {
    description: "Get user details",
    inputSchema: { id: z.string() },
    outputSchema: {
      type: "object",
      properties: {
        id: { type: "string" },
        name: { type: "string" },
        email: { type: "string" },
      },
      required: ["id", "name", "email"],
    },
  },
  async ({ id }) => {
    const user = await db.getUser(id);
    return {
      content: [{ type: "text", text: JSON.stringify(user) }],
      structuredContent: user,
    };
  }
);
```

---

## Resources

**Purpose:** Read-only data sources that provide context to AI.

### When to Use Resources
- File contents
- Database schemas
- Configuration files
- API documentation
- Any read-only data

### Resource Definition Structure

```json
{
  "uri": "scheme://path/to/resource",
  "name": "Resource Name",
  "title": "Human-Readable Title",
  "description": "What this resource contains",
  "mimeType": "application/json",
  "size": 1024,
  "annotations": {
    "audience": ["user", "assistant"],
    "priority": 0.8,
    "lastModified": "2025-01-18T12:00:00Z"
  }
}
```

### URI Schemes

| Scheme | Use Case | Example |
|--------|----------|---------|
| `file://` | File system | `file:///project/README.md` |
| `config://` | Configuration | `config://app/settings` |
| `db://` | Database | `db://users/123` |
| `https://` | Web resources | `https://api.example.com/docs` |
| Custom | Domain-specific | `myapp://dashboard/metrics` |

### Resource Templates

Dynamic resources with URI parameters:

```json
{
  "uriTemplate": "db://users/{id}",
  "name": "User Record",
  "description": "Fetch user by ID"
}
```

### Resource Content Types

**Text content:**
```json
{
  "uri": "file:///example.txt",
  "mimeType": "text/plain",
  "text": "File contents here"
}
```

**Binary content:**
```json
{
  "uri": "file:///image.png",
  "mimeType": "image/png",
  "blob": "base64-encoded-data"
}
```

### Resource Subscriptions

Clients can subscribe to resource changes:

```typescript
// Server notifies when resource changes
server.notifyResourceUpdated("config://app/settings");
```

---

## Prompts

**Purpose:** Reusable interaction templates for specific tasks.

### When to Use Prompts
- Code review templates
- Analysis frameworks
- Writing assistance
- Debugging guides
- Any structured interaction pattern

### Prompt Definition Structure

```json
{
  "name": "prompt_name",
  "title": "Human-Readable Title",
  "description": "What this prompt helps with",
  "arguments": [
    {
      "name": "arg_name",
      "description": "Argument description",
      "required": true
    }
  ]
}
```

### Prompt Response Format

```json
{
  "description": "Generated prompt description",
  "messages": [
    {
      "role": "user",
      "content": {
        "type": "text",
        "text": "The prompt content"
      }
    }
  ]
}
```

### Multi-Message Prompts

```typescript
server.registerPromptGet(async (name, args) => {
  return {
    messages: [
      {
        role: "user",
        content: {
          type: "text",
          text: "Here's the code to review:",
        },
      },
      {
        role: "user",
        content: {
          type: "resource",
          resource: {
            uri: `file:///${args?.file}`,
            mimeType: "text/plain",
            text: await readFile(args?.file),
          },
        },
      },
      {
        role: "assistant",
        content: {
          type: "text",
          text: "I'll review this code for quality and issues.",
        },
      },
    ],
  };
});
```

### Prompts with Embedded Resources

```typescript
{
  role: "user",
  content: {
    type: "resource",
    resource: {
      uri: "config://app/guidelines",
      mimeType: "text/markdown",
      text: codeGuidelines
    }
  }
}
```

---

## Capability Declaration

Servers declare which capabilities they support:

```json
{
  "capabilities": {
    "tools": {
      "listChanged": true
    },
    "resources": {
      "subscribe": true,
      "listChanged": true
    },
    "prompts": {
      "listChanged": true
    }
  }
}
```

### Capability Flags

| Capability | Flag | Meaning |
|------------|------|---------|
| tools | `listChanged` | Server notifies when tools change |
| resources | `subscribe` | Clients can subscribe to updates |
| resources | `listChanged` | Server notifies when list changes |
| prompts | `listChanged` | Server notifies when prompts change |

---

## Annotations

Optional metadata for resources, tools, and content:

```json
{
  "annotations": {
    "audience": ["user"],
    "priority": 0.9,
    "lastModified": "2025-01-18T12:00:00Z"
  }
}
```

| Field | Type | Description |
|-------|------|-------------|
| `audience` | `["user", "assistant"]` | Who should see this |
| `priority` | `0.0 - 1.0` | Importance (1.0 = must include) |
| `lastModified` | ISO 8601 | When content was last updated |

---

## Notifications

Servers notify clients of changes:

```typescript
// Tools changed
server.notify("notifications/tools/list_changed");

// Resources changed
server.notify("notifications/resources/list_changed");

// Specific resource updated
server.notify("notifications/resources/updated", {
  uri: "config://app/settings"
});

// Prompts changed
server.notify("notifications/prompts/list_changed");
```

---

## Pagination

For large lists, use cursor-based pagination:

**Request:**
```json
{
  "method": "tools/list",
  "params": { "cursor": "abc123" }
}
```

**Response:**
```json
{
  "tools": [...],
  "nextCursor": "def456"
}
```

When `nextCursor` is absent, no more pages exist.
