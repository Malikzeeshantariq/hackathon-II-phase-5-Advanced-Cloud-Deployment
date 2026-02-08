# ChatKit Persistence with PostgreSQL/Neon

Production-grade thread and message storage using PostgreSQL (Neon Serverless).

## Overview

ChatKit requires a `Store` implementation for:
- Saving/loading conversation threads
- Persisting messages within threads
- Pagination for message history

---

## Database Schema

```sql
-- threads table
CREATE TABLE IF NOT EXISTS chatkit_threads (
    id VARCHAR(255) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_threads_user_id ON chatkit_threads(user_id);
CREATE INDEX idx_threads_updated_at ON chatkit_threads(updated_at DESC);

-- thread_items table (messages, assistant responses, tool calls)
CREATE TABLE IF NOT EXISTS chatkit_thread_items (
    id VARCHAR(255) PRIMARY KEY,
    thread_id VARCHAR(255) NOT NULL REFERENCES chatkit_threads(id) ON DELETE CASCADE,
    type VARCHAR(50) NOT NULL,  -- 'user', 'assistant', 'tool_call', 'tool_result'
    content TEXT,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_items_thread_id ON chatkit_thread_items(thread_id);
CREATE INDEX idx_items_created_at ON chatkit_thread_items(thread_id, created_at);
```

---

## SQLModel Models

```python
# app/models/chatkit.py
from sqlmodel import SQLModel, Field, Relationship
from datetime import datetime
from typing import Optional
import json

class ChatKitThread(SQLModel, table=True):
    __tablename__ = "chatkit_threads"

    id: str = Field(primary_key=True)
    user_id: str = Field(index=True)
    metadata_json: str = Field(default="{}", sa_column_kwargs={"name": "metadata"})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    items: list["ChatKitThreadItem"] = Relationship(back_populates="thread")

    @property
    def metadata(self) -> dict:
        return json.loads(self.metadata_json)

    @metadata.setter
    def metadata(self, value: dict):
        self.metadata_json = json.dumps(value)


class ChatKitThreadItem(SQLModel, table=True):
    __tablename__ = "chatkit_thread_items"

    id: str = Field(primary_key=True)
    thread_id: str = Field(foreign_key="chatkit_threads.id", index=True)
    type: str  # 'user', 'assistant', 'tool_call', 'tool_result'
    content: Optional[str] = None
    metadata_json: str = Field(default="{}", sa_column_kwargs={"name": "metadata"})
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Relationship
    thread: Optional[ChatKitThread] = Relationship(back_populates="items")

    @property
    def metadata(self) -> dict:
        return json.loads(self.metadata_json)

    @metadata.setter
    def metadata(self, value: dict):
        self.metadata_json = json.dumps(value)
```

---

## Database Connection (Neon)

```python
# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlmodel import SQLModel
from app.config import settings
from contextlib import asynccontextmanager

# Neon connection string: postgresql+asyncpg://user:pass@host/db?sslmode=require
DATABASE_URL = settings.database_url.replace(
    "postgresql://", "postgresql+asyncpg://"
)

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
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
    """Create tables on startup."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
```

---

## PostgreSQL Store Implementation

```python
# app/store/postgres.py
from chatkit.store import Store
from chatkit.types import (
    ThreadMetadata,
    ThreadItem,
    UserMessageItem,
    AssistantMessageItem,
    Page,
)
from sqlalchemy import select, desc, asc
from sqlalchemy.dialects.postgresql import insert
from datetime import datetime
from typing import Literal
from app.database import get_session
from app.models.chatkit import ChatKitThread, ChatKitThreadItem
import json

class PostgresStore(Store[dict]):
    """PostgreSQL/Neon implementation of ChatKit Store."""

    async def save_thread(
        self,
        thread: ThreadMetadata,
        context: dict
    ) -> None:
        """Save or update a thread."""
        user_id = context.get("user_id", "anonymous")

        async with get_session() as session:
            # Upsert thread
            stmt = insert(ChatKitThread).values(
                id=thread.id,
                user_id=user_id,
                metadata_json=json.dumps(thread.metadata or {}),
                created_at=thread.created_at,
                updated_at=datetime.utcnow(),
            ).on_conflict_do_update(
                index_elements=["id"],
                set_={
                    "metadata_json": json.dumps(thread.metadata or {}),
                    "updated_at": datetime.utcnow(),
                }
            )
            await session.execute(stmt)

    async def load_thread(
        self,
        thread_id: str,
        context: dict
    ) -> ThreadMetadata | None:
        """Load a thread by ID."""
        user_id = context.get("user_id")

        async with get_session() as session:
            stmt = select(ChatKitThread).where(ChatKitThread.id == thread_id)

            # Enforce user isolation if user_id provided
            if user_id:
                stmt = stmt.where(ChatKitThread.user_id == user_id)

            result = await session.execute(stmt)
            thread = result.scalar_one_or_none()

            if thread is None:
                return None

            return ThreadMetadata(
                id=thread.id,
                created_at=thread.created_at,
                updated_at=thread.updated_at,
                metadata=thread.metadata,
            )

    async def save_item(
        self,
        thread_id: str,
        item: ThreadItem,
        context: dict
    ) -> None:
        """Save a thread item (message)."""
        async with get_session() as session:
            # Determine content based on item type
            content = None
            if hasattr(item, "content"):
                content = item.content
            elif hasattr(item, "text"):
                content = item.text

            db_item = ChatKitThreadItem(
                id=item.id,
                thread_id=thread_id,
                type=item.type,
                content=content,
                metadata_json=json.dumps(getattr(item, "metadata", {}) or {}),
                created_at=getattr(item, "created_at", datetime.utcnow()),
            )
            session.add(db_item)

    async def load_thread_items(
        self,
        thread_id: str,
        after: str | None,
        limit: int,
        order: Literal["asc", "desc"],
        context: dict
    ) -> Page[ThreadItem]:
        """Load paginated thread items."""
        async with get_session() as session:
            # Base query
            stmt = select(ChatKitThreadItem).where(
                ChatKitThreadItem.thread_id == thread_id
            )

            # Cursor-based pagination
            if after:
                # Get the cursor item's created_at
                cursor_stmt = select(ChatKitThreadItem.created_at).where(
                    ChatKitThreadItem.id == after
                )
                cursor_result = await session.execute(cursor_stmt)
                cursor_time = cursor_result.scalar_one_or_none()

                if cursor_time:
                    if order == "asc":
                        stmt = stmt.where(ChatKitThreadItem.created_at > cursor_time)
                    else:
                        stmt = stmt.where(ChatKitThreadItem.created_at < cursor_time)

            # Order
            if order == "asc":
                stmt = stmt.order_by(asc(ChatKitThreadItem.created_at))
            else:
                stmt = stmt.order_by(desc(ChatKitThreadItem.created_at))

            # Limit + 1 to check for more
            stmt = stmt.limit(limit + 1)

            result = await session.execute(stmt)
            items = list(result.scalars().all())

            # Check if there are more items
            has_more = len(items) > limit
            if has_more:
                items = items[:limit]

            # Convert to ChatKit types
            thread_items = [self._to_thread_item(item) for item in items]

            return Page(
                data=thread_items,
                has_more=has_more,
                after=items[-1].id if items and has_more else None,
            )

    def _to_thread_item(self, db_item: ChatKitThreadItem) -> ThreadItem:
        """Convert database item to ChatKit ThreadItem."""
        base = {
            "id": db_item.id,
            "type": db_item.type,
            "created_at": db_item.created_at,
            "metadata": db_item.metadata,
        }

        if db_item.type == "user":
            return UserMessageItem(
                **base,
                content=db_item.content or "",
            )
        elif db_item.type == "assistant":
            return AssistantMessageItem(
                **base,
                content=db_item.content or "",
            )
        else:
            # Generic ThreadItem for other types
            return ThreadItem(**base)

    async def delete_thread(
        self,
        thread_id: str,
        context: dict
    ) -> bool:
        """Delete a thread and all its items."""
        user_id = context.get("user_id")

        async with get_session() as session:
            stmt = select(ChatKitThread).where(ChatKitThread.id == thread_id)

            # Enforce user isolation
            if user_id:
                stmt = stmt.where(ChatKitThread.user_id == user_id)

            result = await session.execute(stmt)
            thread = result.scalar_one_or_none()

            if thread is None:
                return False

            await session.delete(thread)  # Cascades to items
            return True

    async def list_user_threads(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0
    ) -> list[ThreadMetadata]:
        """List threads for a user (custom method)."""
        async with get_session() as session:
            stmt = (
                select(ChatKitThread)
                .where(ChatKitThread.user_id == user_id)
                .order_by(desc(ChatKitThread.updated_at))
                .limit(limit)
                .offset(offset)
            )

            result = await session.execute(stmt)
            threads = result.scalars().all()

            return [
                ThreadMetadata(
                    id=t.id,
                    created_at=t.created_at,
                    updated_at=t.updated_at,
                    metadata=t.metadata,
                )
                for t in threads
            ]
```

---

## Integration with Server

```python
# app/server.py
from chatkit.server import ChatKitServer
from chatkit.types import ThreadMetadata, UserMessageItem, ThreadStreamEvent
from chatkit.agents import AgentContext, stream_agent_response
from agents import Runner
from typing import AsyncIterator
from app.store.postgres import PostgresStore
from app.agents.assistant import assistant

class ProductionServer(ChatKitServer[dict]):
    def __init__(self):
        self.pg_store = PostgresStore()
        super().__init__(store=self.pg_store)
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

# Export
server = ProductionServer()
```

---

## FastAPI Lifecycle

```python
# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.database import init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(title="ChatKit API", lifespan=lifespan)
```

---

## Environment Configuration

```bash
# .env
DATABASE_URL=postgresql://user:password@ep-xxx.region.aws.neon.tech/neondb?sslmode=require
OPENAI_API_KEY=sk-proj-...
```

```python
# app/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str
    openai_api_key: str
    debug: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

---

## Neon-Specific Considerations

### Connection Pooling
Neon provides built-in connection pooling. Use the pooled connection string:
```
postgresql://user:pass@ep-xxx-pooler.region.aws.neon.tech/neondb?sslmode=require
```

### Cold Starts
Neon scales to zero. First request may have latency. Mitigations:
- Use connection pooler endpoint
- Set `pool_pre_ping=True` in SQLAlchemy

### Branching for Development
```bash
# Create dev branch
neon branch create --name dev

# Get dev branch connection string
neon connection-string --branch dev
```

---

## Additional API Endpoints

```python
# app/main.py (additional routes)

@app.get("/threads")
async def list_threads(user: dict = Depends(verify_jwt)):
    """List user's conversation threads."""
    threads = await server.pg_store.list_user_threads(user["user_id"])
    return {"threads": [{"id": t.id, "updated_at": t.updated_at} for t in threads]}

@app.delete("/threads/{thread_id}")
async def delete_thread(
    thread_id: str,
    user: dict = Depends(verify_jwt)
):
    """Delete a conversation thread."""
    deleted = await server.pg_store.delete_thread(
        thread_id,
        {"user_id": user["user_id"]}
    )
    if not deleted:
        raise HTTPException(404, "Thread not found")
    return {"status": "deleted"}

@app.get("/threads/{thread_id}/messages")
async def get_messages(
    thread_id: str,
    limit: int = 50,
    after: str | None = None,
    user: dict = Depends(verify_jwt)
):
    """Get messages in a thread."""
    page = await server.pg_store.load_thread_items(
        thread_id,
        after=after,
        limit=limit,
        order="desc",
        context={"user_id": user["user_id"]}
    )
    return {
        "messages": [{"id": m.id, "type": m.type, "content": getattr(m, "content", None)} for m in page.data],
        "has_more": page.has_more,
        "next_cursor": page.after,
    }
```

---

## Migration Script

```python
# scripts/migrate.py
import asyncio
from app.database import init_db

async def main():
    print("Creating database tables...")
    await init_db()
    print("Done!")

if __name__ == "__main__":
    asyncio.run(main())
```

Run with:
```bash
uv run python scripts/migrate.py
```
