# Research: Todo AI Chatbot (Phase 3)

**Branch**: `001-todo-ai-chatbot` | **Date**: 2026-01-19 | **Spec**: [spec.md](./spec.md)

## Phase 0 Research Summary

This document captures research findings and technology validations for the AI chatbot feature.

---

## 1. OpenAI Agents SDK

### Selected Technology
**OpenAI Agents SDK** - Official Python SDK for building AI agents with tool execution.

### Key Features Used
- `Agent[AgentContext]` - Agent definition with typed context
- `@function_tool` decorator - Define callable tools
- `Runner.run()` - Execute agent with conversation history
- `stream_agent_response()` - Stream responses for real-time UI

### Integration Pattern
```python
from agents import Agent, Runner, function_tool

agent = Agent[AgentContext](
    model="gpt-4o",
    name="TaskAssistant",
    instructions="Help users manage tasks...",
    tools=[add_task, list_tasks, complete_task, delete_task, update_task]
)
```

### Validation
- Supports tool-only execution (Constitutional requirement)
- Provides structured tool call results for logging
- Compatible with ChatKit streaming

---

## 2. MCP (Model Context Protocol) Tools

### Architecture Decision
Use **function tools** (OpenAI Agents SDK native) rather than MCP server protocol for this feature.

**Rationale**:
- Simpler integration with OpenAI Agents SDK
- Direct database access within tool functions
- No additional protocol overhead
- Tools still follow MCP principles (deterministic, single operation, validated inputs)

### Tool Definitions

| Tool | Input Schema | Output | Side Effect |
|------|--------------|--------|-------------|
| `add_task` | `{title: str, description?: str}` | Task object | CREATE task |
| `list_tasks` | `{filter?: "all"\|"pending"\|"completed"}` | Task[] | READ tasks |
| `complete_task` | `{task_id: str}` | Task object | UPDATE task.completed |
| `delete_task` | `{task_id: str}` | Success message | DELETE task |
| `update_task` | `{task_id: str, title?: str, description?: str}` | Task object | UPDATE task |

### Validation Rules
- All tools require `user_id` from context (not user input)
- `task_id` must be valid UUID owned by user
- Ownership enforced at tool level

---

## 3. ChatKit Integration

### Selected Library
**OpenAI ChatKit** - UI components and server SDK for conversational interfaces.

### Server Components Used
- `ChatKitServer` - Base class for request handling
- `StreamingResult` - Response type for streaming
- `ThreadMetadata` - Conversation metadata
- `AgentContext` - Request context with streaming

### Frontend Components
- ChatKit React components (message list, input, widgets)
- Streaming message display
- Tool result visualization

### Thread Management
- PostgreSQL-backed `Store` implementation
- Thread = Conversation in our domain model
- Messages stored with tool call references

---

## 4. Conversation Persistence

### Database Schema Additions

**conversations** table:
- `id` (UUID, PK)
- `user_id` (UUID, FK)
- `created_at` (timestamp)
- `updated_at` (timestamp)

**messages** table:
- `id` (UUID, PK)
- `conversation_id` (UUID, FK)
- `role` (enum: user, assistant)
- `content` (text)
- `created_at` (timestamp)

**tool_calls** table:
- `id` (UUID, PK)
- `message_id` (UUID, FK)
- `tool_name` (string)
- `parameters` (JSONB)
- `result` (JSONB)
- `created_at` (timestamp)

### Data Isolation
- Conversations filtered by `user_id` from JWT
- Tool calls inherit user scope through message relationship

---

## 5. Authentication Flow

### Existing Infrastructure (Phase 2)
- Better Auth for frontend session management
- JWT tokens with user claims
- FastAPI middleware for JWT verification

### Chat Endpoint Security
```
POST /api/{user_id}/chat
Authorization: Bearer <jwt>
```

1. JWT middleware extracts user_id from token
2. Path user_id validated against token user_id
3. Conversation loaded/created for verified user
4. All tool calls execute with verified user_id

---

## 6. Stateless Architecture

### Request Lifecycle
1. Request arrives with JWT + conversation_id
2. Load conversation history from PostgreSQL
3. Build agent context with history
4. Execute agent (may call tools)
5. Store assistant message + tool calls
6. Return streaming response

### No Server State
- No in-memory conversation cache
- No session affinity required
- Context reconstructed per request
- Horizontal scaling supported

---

## 7. Performance Considerations

### Latency Budget
- Database round-trip: ~50ms (Neon Serverless)
- OpenAI API call: ~2-5s (streaming mitigates perceived latency)
- Total target: <10s for task creation

### Optimizations
- Connection pooling for database
- Stream response to frontend immediately
- Index on `conversation_id` for message lookups
- Index on `user_id` for conversation lookups

---

## 8. Error Handling Strategy

### Tool Execution Errors
- Catch at tool level
- Return structured error in tool result
- Agent explains error to user naturally

### Database Errors
- Transaction rollback on failure
- Generic error message to user
- Detailed logging for debugging

### Authentication Errors
- 401 for invalid/expired JWT
- 403 for user_id mismatch
- Clear error messages in response

---

## 9. Research Conclusions

| Question | Resolution |
|----------|------------|
| Which AI SDK? | OpenAI Agents SDK |
| MCP protocol or function tools? | Function tools (MCP principles, simpler integration) |
| Conversation storage? | PostgreSQL with conversations, messages, tool_calls tables |
| Frontend framework? | ChatKit React components |
| Streaming support? | Yes, via ChatKit StreamingResult |

**All NEEDS CLARIFICATION items resolved. Ready for Phase 1.**
