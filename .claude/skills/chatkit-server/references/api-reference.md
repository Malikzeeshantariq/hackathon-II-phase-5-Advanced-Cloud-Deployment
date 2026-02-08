# ChatKit Server API Reference

Complete reference for ChatKit Server Python SDK.

## Core Imports

```python
# Server
from chatkit.server import ChatKitServer, StreamingResult

# Types
from chatkit.types import (
    ThreadMetadata,
    UserMessageItem,
    ThreadStreamEvent,
    ThreadItem,
    Page,
)

# Agents Integration
from chatkit.agents import (
    AgentContext,
    stream_agent_response,
    ClientToolCall,
)

# Widgets
from chatkit.widgets import Card, Text, Image, Button

# Storage
from chatkit.store import Store, MemoryStore

# OpenAI Agents SDK
from agents import Agent, Runner, function_tool, RunContextWrapper
```

---

## ChatKitServer

Base class for building ChatKit backends.

### Class Definition
```python
class ChatKitServer(Generic[TContext]):
    def __init__(self, store: Store[TContext]) -> None: ...

    async def process(
        self,
        payload: bytes,
        context: TContext
    ) -> StreamingResult | dict: ...

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: TContext,
    ) -> AsyncIterator[ThreadStreamEvent]: ...

    async def _to_agent_input(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None
    ) -> list[dict] | None: ...
```

### Methods

#### `process(payload, context)`
Main entry point. Parses ChatKit protocol payload and routes to appropriate handler.

**Parameters:**
- `payload: bytes` - Raw request body from ChatKit client
- `context: TContext` - Request context (typically includes FastAPI Request)

**Returns:** `StreamingResult` for streaming responses, `dict` for JSON responses

#### `respond(thread, item, context)`
Override this method to implement custom response logic.

**Parameters:**
- `thread: ThreadMetadata` - Current conversation thread
- `item: UserMessageItem | None` - User's message (None for thread init)
- `context: TContext` - Request context

**Yields:** `ThreadStreamEvent` - Events streamed to client

#### `_to_agent_input(thread, item)`
Helper to convert ChatKit message format to OpenAI Agents SDK input format.

**Returns:** List of message dicts for agent, or None if no input

---

## ThreadMetadata

Represents a conversation thread.

```python
class ThreadMetadata:
    id: str                    # Unique thread identifier
    created_at: datetime       # Creation timestamp
    updated_at: datetime       # Last update timestamp
    metadata: dict[str, Any]   # Custom metadata
```

---

## UserMessageItem

Represents a user message in the thread.

```python
class UserMessageItem:
    id: str                    # Message ID
    type: Literal["user"]      # Always "user"
    content: str               # Message text content
    created_at: datetime       # Timestamp
    metadata: dict[str, Any]   # Custom metadata
```

---

## ThreadStreamEvent

Events yielded during streaming response.

```python
# Event types:
# - text_delta: Partial text content
# - widget: UI widget to render
# - client_tool: Trigger frontend action
# - done: Stream complete
```

---

## AgentContext

Context object passed to agent tools and stream handlers.

```python
class AgentContext:
    thread: ThreadMetadata           # Current thread
    store: Store                     # Storage backend
    request_context: dict            # Request-level context
    client_tool_call: ClientToolCall | None  # Set to trigger client tool

    async def stream_widget(
        self,
        widget: Widget,
        copy_text: str | None = None
    ) -> None: ...
```

### Methods

#### `stream_widget(widget, copy_text)`
Stream a widget to the ChatKit frontend.

**Parameters:**
- `widget: Widget` - Widget component (Card, Text, etc.)
- `copy_text: str | None` - Plain text for copy-to-clipboard

---

## ClientToolCall

Trigger a tool execution on the frontend.

```python
class ClientToolCall:
    name: str              # Tool name (registered in frontend)
    arguments: dict        # Arguments passed to frontend tool
```

### Usage
```python
ctx.context.client_tool_call = ClientToolCall(
    name="switch_theme",
    arguments={"theme": "dark"}
)
```

---

## Store

Abstract base class for thread/message persistence.

```python
class Store(ABC, Generic[TContext]):
    @abstractmethod
    async def save_thread(
        self,
        thread: ThreadMetadata,
        context: TContext
    ) -> None: ...

    @abstractmethod
    async def load_thread(
        self,
        thread_id: str,
        context: TContext
    ) -> ThreadMetadata | None: ...

    @abstractmethod
    async def save_item(
        self,
        thread_id: str,
        item: ThreadItem,
        context: TContext
    ) -> None: ...

    @abstractmethod
    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: Literal["asc", "desc"],
        context: TContext
    ) -> Page[ThreadItem]: ...
```

---

## MemoryStore

In-memory implementation of Store (development only).

```python
from chatkit.store import MemoryStore

store = MemoryStore()  # Thread-safe, non-persistent
```

---

## Page

Paginated response container.

```python
class Page(Generic[T]):
    data: list[T]          # Items in this page
    has_more: bool         # More items available
    after: str | None      # Cursor for next page
```

---

## Agent (OpenAI Agents SDK)

Create an AI agent with tools.

```python
from agents import Agent

agent = Agent[AgentContext](
    model="gpt-4.1-mini",        # or "gpt-4.1", "gpt-4o"
    name="Assistant",            # Display name
    instructions="...",          # System prompt
    tools=[tool1, tool2],        # List of @function_tool functions
)
```

### Models
- `gpt-4.1-mini` - Fast, cost-effective
- `gpt-4.1` - Balanced performance
- `gpt-4o` - Most capable

---

## Runner (OpenAI Agents SDK)

Execute agent with streaming.

```python
from agents import Runner

result = Runner.run_streamed(
    agent,           # Agent instance
    input_messages,  # List of message dicts
    context=ctx,     # AgentContext
)

# Iterate over streamed events
async for event in stream_agent_response(ctx, result):
    yield event
```

---

## @function_tool Decorator

Convert Python functions to agent-callable tools.

```python
from agents import function_tool, RunContextWrapper

@function_tool(
    description_override="Human-readable description for the agent"
)
async def my_tool(
    ctx: RunContextWrapper[AgentContext],
    param1: str,
    param2: int = 10
) -> dict | None:
    # Return dict on success, None on failure
    return {"result": "success"}
```

### Parameters
- `description_override: str` - Tool description shown to agent
- Function must accept `ctx: RunContextWrapper[AgentContext]` as first param
- Additional params become tool arguments
- Return `dict` for success, `None` for failure (agent sees tool failed)

### Type Hints
Use type hints for automatic validation:
- `str`, `int`, `float`, `bool` - Primitives
- `list[str]` - Arrays
- `Literal["a", "b"]` - Enums
- `Optional[str]` - Optional params (with default)

---

## stream_agent_response

Convert Agent SDK events to ChatKit stream events.

```python
from chatkit.agents import stream_agent_response

async for event in stream_agent_response(agent_context, runner_result):
    yield event  # ThreadStreamEvent
```

---

## StreamingResult

Wrapper for async generator that FastAPI can stream.

```python
from chatkit.server import StreamingResult

# Returned by server.process() for streaming responses
# Pass directly to FastAPI StreamingResponse
```

---

## Error Handling

### Tool Errors
```python
@function_tool(description_override="Risky operation")
async def risky_tool(ctx: RunContextWrapper[AgentContext], id: str) -> dict | None:
    try:
        result = await perform_operation(id)
        return {"status": "success", "data": result}
    except NotFoundError:
        return None  # Agent sees failure, can retry or inform user
    except Exception as e:
        logger.error(f"Tool failed: {e}")
        return None
```

### Server Errors
```python
@app.post("/chatkit")
async def chatkit_endpoint(request: Request) -> Response:
    try:
        payload = await request.body()
        result = await server.process(payload, {"request": request})
        # ... handle result
    except Exception as e:
        logger.exception("ChatKit error")
        return JSONResponse({"error": "Internal error"}, status_code=500)
```
