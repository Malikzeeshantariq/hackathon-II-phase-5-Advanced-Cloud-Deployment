"""
[Task]: T018
[From]: specs/002-advanced-features-dapr/tasks.md §Phase 5 (US3)
[Description]: Notification Service — Consumes reminder events from Dapr Pub/Sub

Dapr Subscription: topic=reminders, route=/events/reminders
Processes ReminderEvents with idempotency check.
"""

import logging
import json
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Request


# T039: Structured JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "service": "notification-service",
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
from app.handlers.reminder_handler import handle_reminder_event


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="Notification Service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    return {"status": "ok", "service": "notification-service"}


@app.get("/readyz")
async def readiness_check():
    """Readiness probe — checks database connectivity."""
    from sqlmodel import text
    from app.database import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready", "service": "notification-service"}
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "service": "notification-service"},
        )


@app.get("/dapr/subscribe")
async def subscribe():
    """Dapr programmatic subscription declaration."""
    return [
        {
            "pubsubname": "pubsub",
            "topic": "reminders",
            "route": "/events/reminders",
        }
    ]


@app.post("/events/reminders")
async def handle_reminders(
    request: Request,
    session: Session = Depends(get_session),
):
    """Dapr Pub/Sub handler for reminder events."""
    event_data = await request.json()
    return await handle_reminder_event(event_data, session)
