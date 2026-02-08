"""
[Task]: T021
[From]: specs/002-advanced-features-dapr/tasks.md §Phase 7 (US5)
[Description]: Audit Service — Consumes task-events from Dapr Pub/Sub

Dapr Subscription: topic=task-events, route=/events/task-events
Records all task lifecycle events as immutable audit entries.
"""

import logging
import json
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request


# T041: Structured JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "service": "audit-service",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


_handler = logging.StreamHandler(sys.stdout)
_handler.setFormatter(JSONFormatter())
logging.root.handlers = [_handler]
logging.root.setLevel(logging.INFO)
from sqlmodel import Session

from app.database import create_db_and_tables, get_session
from app.handlers.audit_handler import handle_task_event


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Audit Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "audit-service"}


@app.get("/readyz")
async def readiness_check():
    """Readiness probe — checks database connectivity."""
    from sqlmodel import text
    from app.database import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "service": "audit-service"}
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "service": "audit-service"},
        )


@app.get("/dapr/subscribe")
async def subscribe():
    """Dapr programmatic subscription declaration."""
    return [
        {
            "pubsubname": "pubsub",
            "topic": "task-events",
            "route": "/events/task-events",
        }
    ]


@app.post("/events/task-events")
async def handle_events(
    request: Request,
    session: Session = Depends(get_session),
):
    """Dapr Pub/Sub handler for task lifecycle events."""
    event_data = await request.json()
    return await handle_task_event(event_data, session)
