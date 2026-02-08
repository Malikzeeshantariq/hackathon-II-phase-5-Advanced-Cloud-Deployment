#!/bin/bash
# ChatKit Server Project Setup Script
# Usage: ./setup-project.sh [project-name] [--with-postgres]

set -e

PROJECT_NAME="${1:-chatkit-backend}"
WITH_POSTGRES=false

# Parse flags
for arg in "$@"; do
    case $arg in
        --with-postgres)
            WITH_POSTGRES=true
            shift
            ;;
    esac
done

echo "Creating ChatKit Server project: $PROJECT_NAME"

# Create project directory
mkdir -p "$PROJECT_NAME"
cd "$PROJECT_NAME"

# Initialize with uv
echo "Initializing Python project..."
uv init

# Add dependencies
echo "Adding dependencies..."
uv add chatkit openai-agents fastapi uvicorn pydantic-settings

if [ "$WITH_POSTGRES" = true ]; then
    echo "Adding PostgreSQL dependencies..."
    uv add sqlmodel sqlalchemy asyncpg
fi

# Create directory structure
echo "Creating project structure..."
mkdir -p app/{agents,store,middleware}
mkdir -p scripts
mkdir -p tests

# Create __init__.py files
touch app/__init__.py
touch app/agents/__init__.py
touch app/store/__init__.py
touch app/middleware/__init__.py
touch tests/__init__.py

# Create config.py
cat > app/config.py << 'EOF'
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    cors_origins: list[str] = ["http://localhost:3000"]
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
EOF

# Create basic agent
cat > app/agents/assistant.py << 'EOF'
from agents import Agent, function_tool, RunContextWrapper
from chatkit.agents import AgentContext

INSTRUCTIONS = """
You are a helpful AI assistant. Be concise and helpful.
"""

@function_tool(description_override="Echo the user's message back")
async def echo(
    ctx: RunContextWrapper[AgentContext],
    message: str
) -> dict:
    return {"echoed": message}

assistant = Agent[AgentContext](
    model="gpt-4.1-mini",
    name="Assistant",
    instructions=INSTRUCTIONS,
    tools=[echo],
)
EOF

# Create server.py
cat > app/server.py << 'EOF'
from chatkit.server import ChatKitServer
from chatkit.store import MemoryStore
from chatkit.types import ThreadMetadata, UserMessageItem, ThreadStreamEvent
from chatkit.agents import AgentContext, stream_agent_response
from agents import Runner
from typing import AsyncIterator
from app.agents.assistant import assistant

class AssistantServer(ChatKitServer[dict]):
    def __init__(self, store=None):
        super().__init__(store=store or MemoryStore())
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

server = AssistantServer()
EOF

# Create main.py
cat > app/main.py << 'EOF'
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, Response, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from chatkit.server import StreamingResult
from app.server import server
from app.config import settings

app = FastAPI(title="ChatKit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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

@app.get("/health")
async def health():
    return {"status": "ok"}
EOF

# Create .env.example
cat > .env.example << 'EOF'
OPENAI_API_KEY=sk-proj-your-key-here
CORS_ORIGINS=["http://localhost:3000"]
DEBUG=false
EOF

# Create .gitignore
cat > .gitignore << 'EOF'
__pycache__/
*.py[cod]
*$py.class
.env
.venv/
*.egg-info/
dist/
build/
.pytest_cache/
.coverage
EOF

# Add PostgreSQL files if requested
if [ "$WITH_POSTGRES" = true ]; then
    # Update config.py
    cat > app/config.py << 'EOF'
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openai_api_key: str
    database_url: str
    cors_origins: list[str] = ["http://localhost:3000"]
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
EOF

    # Create database.py
    cat > app/database.py << 'EOF'
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from app.config import settings
from contextlib import asynccontextmanager

DATABASE_URL = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    pool_pre_ping=True,
)

async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

@asynccontextmanager
async def get_session():
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
EOF

    # Update .env.example
    cat > .env.example << 'EOF'
OPENAI_API_KEY=sk-proj-your-key-here
DATABASE_URL=postgresql://user:pass@host/db?sslmode=require
CORS_ORIGINS=["http://localhost:3000"]
DEBUG=false
EOF

    echo "PostgreSQL support added. See references/persistence.md for Store implementation."
fi

echo ""
echo "Project created successfully!"
echo ""
echo "Next steps:"
echo "  1. cd $PROJECT_NAME"
echo "  2. cp .env.example .env"
echo "  3. Edit .env with your OPENAI_API_KEY"
echo "  4. uv run uvicorn app.main:app --reload --port 8000"
echo ""
echo "API will be available at http://localhost:8000/chatkit"
