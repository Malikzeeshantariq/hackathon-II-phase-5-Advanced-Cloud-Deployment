---
name: chatkit-server
description: |
  Build conversational AI backends using OpenAI ChatKit Server with FastAPI.
  This skill should be used when users need to create chatbots, AI assistants,
  or conversational interfaces - from hello world demos to production systems.
  Covers agent creation, tool integration, widget streaming, thread management,
  and PostgreSQL/Neon persistence.
allowed-tools: Read, Write, Edit, Glob, Grep, Bash
---

# ChatKit Server Builder

Build production-grade conversational AI backends with OpenAI ChatKit Server + FastAPI.

## Before Implementation

| Source | Gather |
|--------|--------|
| **Codebase** | Existing FastAPI structure, database models, auth patterns |
| **Conversation** | User's assistant purpose, required tools, UI needs |
| **Skill References** | API patterns from `references/`, widget examples, persistence patterns |
| **User Guidelines** | Project conventions, deployment requirements |

Only ask user for THEIR requirements (domain expertise is in this skill).

---

## Quick Start Decision Tree

```
What do you need?
├─ "Hello World" demo → Level 1: Basic Server
├─ Agent with tools → Level 2: Agent + Tools
├─ Rich UI widgets → Level 3: Widget Streaming
├─ Production system → Level 4: Full Stack
└─ Specific feature → See references/
```

---

## Level 1: Basic Server (5 min)

Minimal ChatKit server that echoes messages.

### Setup
```bash
# Create project
mkdir chatkit-backend && cd chatkit-backend
uv init && uv add chatkit openai-agents fastapi uvicorn

# Set API key
export OPENAI_API_KEY="sk-proj-..."
```

### Code: `app/main.py`
```python
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from chatkit.server import ChatKitServer, StreamingResult
from chatkit.store import MemoryStore

app = FastAPI(title="ChatKit API")

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize server with in-memory store
store = MemoryStore()
server = ChatKitServer(store=store)

@app.post("/chatkit")
async def chatkit_endpoint(request: Request) -> Response:
    payload = await request.body()
    result = await server.process(payload, {"request": request})

    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)
```

### Run
```bash
uv run uvicorn app.main:app --reload --port 8000
```

---

## Level 2: Agent with Tools

Add an AI agent with custom capabilities.

### Code: `app/server.py`
```python
from chatkit.server import ChatKitServer
from chatkit.store import MemoryStore
from chatkit.types import ThreadMetadata, UserMessageItem, ThreadStreamEvent
from chatkit.agents import AgentContext, stream_agent_response
from agents import Agent, Runner, function_tool, RunContextWrapper
from typing import AsyncIterator

# Define tools
@function_tool(description_override="Get current weather for a location")
async def get_weather(
    ctx: RunContextWrapper[AgentContext],
    location: str,
    unit: str = "celsius"
) -> dict:
    # Replace with real API call
    return {
        "location": location,
        "temperature": 22,
        "unit": unit,
        "condition": "sunny"
    }

@function_tool(description_override="Search knowledge base")
async def search_knowledge(
    ctx: RunContextWrapper[AgentContext],
    query: str
) -> dict:
    # Replace with real search (vector DB, etc.)
    return {"results": [f"Found info about: {query}"], "count": 1}

# Create agent
INSTRUCTIONS = """
You are a helpful AI assistant. You can:
- Check weather for any location
- Search the knowledge base for information
Be concise and helpful.
"""

assistant = Agent[AgentContext](
    model="gpt-4.1-mini",
    name="Assistant",
    instructions=INSTRUCTIONS,
    tools=[get_weather, search_knowledge],
)

# Custom server
class AssistantServer(ChatKitServer[dict]):
    def __init__(self):
        super().__init__(store=MemoryStore())
        self.assistant = assistant

    async def respond(
        self,
        thread: ThreadMetadata,
        item: UserMessageItem | None,
        context: dict,
    ) -> AsyncIterator[ThreadStreamEvent]:
        agent_context = AgentContext(
            thread=thread,
            store=self.store,
            request_context=context,
        )

        agent_input = await self._to_agent_input(thread, item)
        if agent_input is None:
            return

        result = Runner.run_streamed(
            self.assistant,
            agent_input,
            context=agent_context,
        )

        async for event in stream_agent_response(agent_context, result):
            yield event

# Export server instance
server = AssistantServer()
```

### Update `app/main.py`
```python
from fastapi import FastAPI, Request, Depends
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from chatkit.server import StreamingResult
from app.server import server

app = FastAPI(title="ChatKit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chatkit")
async def chatkit_endpoint(request: Request) -> Response:
    payload = await request.body()
    result = await server.process(payload, {"request": request})

    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)
```

---

## Level 3: Widget Streaming

Send rich UI components to the frontend.

```python
from chatkit.widgets import Card, Text, Image
from chatkit.agents import ClientToolCall

@function_tool(description_override="Display weather with rich UI")
async def get_weather_widget(
    ctx: RunContextWrapper[AgentContext],
    location: str,
    unit: str = "celsius"
) -> dict:
    # Fetch weather data
    data = {"location": location, "temp": 22, "condition": "Sunny", "icon": "sun"}

    # Build widget
    widget = Card(children=[
        Text(value=data["location"], size="xl", weight="bold"),
        Text(value=f"{data['temp']}°{unit[0].upper()}", size="3xl", weight="bold"),
        Text(value=data["condition"], size="md", color="secondary"),
        Image(src=f"/icons/{data['icon']}.svg", alt=data["condition"], width=64, height=64)
    ])

    # Stream to frontend
    copy_text = f"{data['location']}: {data['temp']}°, {data['condition']}"
    await ctx.context.stream_widget(widget, copy_text=copy_text)

    return {"location": location, "temperature": data["temp"]}
```

### Client Tools (Frontend ↔ Backend)

Trigger actions on the frontend from server tools:

```python
@function_tool(description_override="Switch UI theme")
async def switch_theme(
    ctx: RunContextWrapper[AgentContext],
    theme: str  # "light" or "dark"
) -> dict:
    # Trigger client-side tool
    ctx.context.client_tool_call = ClientToolCall(
        name="switch_theme",
        arguments={"theme": theme}
    )
    return {"theme": theme, "status": "requested"}
```

Frontend handles via `onClientTool` callback. See `references/patterns.md`.

---

## Level 4: Production Stack

### Project Structure
```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app + endpoint
│   ├── server.py         # ChatKitServer subclass
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── assistant.py  # Agent definition
│   │   └── tools.py      # Tool functions
│   ├── store/
│   │   ├── __init__.py
│   │   └── postgres.py   # PostgreSQL store
│   ├── config.py         # Settings
│   └── middleware/
│       └── auth.py       # JWT verification
├── pyproject.toml
└── .env
```

### PostgreSQL Store

See `references/persistence.md` for complete implementation.

```python
# app/store/postgres.py
from chatkit.store import Store
from chatkit.types import ThreadMetadata, ThreadItem, Page
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_session

class PostgresStore(Store[dict]):
    async def save_thread(self, thread: ThreadMetadata, context: dict) -> None:
        async with get_session() as session:
            # Upsert thread to database
            ...

    async def load_thread_items(
        self, thread_id: str, after: str | None,
        limit: int, order: str, context: dict
    ) -> Page[ThreadItem]:
        async with get_session() as session:
            # Query items with pagination
            ...
```

### Configuration

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str  # postgresql://user:pass@host/db
    cors_origins: list[str] = ["http://localhost:3000"]
    jwt_secret: str

    class Config:
        env_file = ".env"

settings = Settings()
```

### Authentication Middleware

```python
# app/middleware/auth.py
from fastapi import Request, HTTPException
from jose import jwt, JWTError
from app.config import settings

async def verify_jwt(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Missing token")

    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        return {"user_id": payload["sub"]}
    except JWTError:
        raise HTTPException(401, "Invalid token")
```

### Production Main

```python
# app/main.py
from fastapi import FastAPI, Request, Depends
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from chatkit.server import StreamingResult
from app.server import create_server
from app.config import settings
from app.middleware.auth import verify_jwt

app = FastAPI(title="ChatKit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chatkit")
async def chatkit_endpoint(
    request: Request,
    user: dict = Depends(verify_jwt)
) -> Response:
    server = await create_server(user["user_id"])
    payload = await request.body()
    result = await server.process(payload, {"request": request, "user": user})

    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)

@app.get("/health")
async def health():
    return {"status": "ok"}
```

---

## Common Patterns

### Multi-Agent Routing
```python
agents = {
    "support": support_agent,
    "sales": sales_agent,
    "general": general_agent,
}

async def route_to_agent(message: str) -> str:
    # Use classifier or keywords
    if "order" in message.lower() or "refund" in message.lower():
        return "support"
    if "pricing" in message.lower() or "demo" in message.lower():
        return "sales"
    return "general"
```

### Error Handling in Tools
```python
@function_tool(description_override="Fetch user data")
async def get_user_data(ctx: RunContextWrapper[AgentContext], user_id: str) -> dict | None:
    try:
        user = await user_service.get(user_id)
        return {"name": user.name, "email": user.email}
    except NotFoundError:
        return None  # Signals failure to agent
    except Exception as e:
        logger.error(f"User fetch failed: {e}")
        return None
```

### Streaming Progress
```python
@function_tool(description_override="Process large dataset")
async def process_data(ctx: RunContextWrapper[AgentContext], dataset_id: str) -> dict:
    total = 100
    for i in range(total):
        await process_chunk(i)
        if i % 10 == 0:
            progress = Card(children=[
                Text(value=f"Processing: {i}/{total}", size="md")
            ])
            await ctx.context.stream_widget(progress)

    return {"status": "complete", "processed": total}
```

---

## Checklist

### Basic Setup
- [ ] Python 3.11+ installed
- [ ] Dependencies: `chatkit`, `openai-agents`, `fastapi`, `uvicorn`
- [ ] `OPENAI_API_KEY` environment variable set
- [ ] CORS configured for frontend origin

### Agent Configuration
- [ ] Agent has clear `instructions`
- [ ] Tools have `description_override` for clarity
- [ ] Tools return `dict` or `None` (for failure)
- [ ] Error handling in all tools

### Production Readiness
- [ ] PostgreSQL store implemented (not MemoryStore)
- [ ] JWT authentication middleware
- [ ] Health check endpoint
- [ ] Structured logging
- [ ] Environment-based configuration
- [ ] Rate limiting considered

### Frontend Integration
- [ ] `/chatkit` endpoint returns `StreamingResponse`
- [ ] Client tools registered in frontend `onClientTool`
- [ ] Error handling via `onError` callback

---

## References

| File | Content |
|------|---------|
| `references/api-reference.md` | Complete API documentation |
| `references/patterns.md` | Code patterns and examples |
| `references/widgets.md` | Widget components reference |
| `references/persistence.md` | PostgreSQL/Neon implementation |

## What This Skill Does NOT Cover

- Frontend ChatKit Web Component (use official @openai/chatkit-react docs)
- Deployment to specific cloud providers
- Vector database integration (varies by provider)
- Fine-tuning OpenAI models
