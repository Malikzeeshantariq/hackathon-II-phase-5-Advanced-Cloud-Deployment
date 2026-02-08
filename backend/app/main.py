"""T012: FastAPI application entry point.

Spec Reference: plan.md - Component Responsibilities
"""
import logging
import json
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).resolve().parent.parent.parent / ".env")

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware


from app.config import get_settings


# T038: Structured JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": self.formatTime(record),
            "service": "todo-backend",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }
        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JSONFormatter())
logging.root.handlers = [handler]
logging.root.setLevel(logging.INFO)
from app.database import create_db_and_tables
from app.routers import tasks
from app.routers import reminders
from app.routers import internal
from app.routers import audit
from app.routers import chat

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Creates database tables on startup.
    """
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (cleanup if needed)


app = FastAPI(
    title="Todo CRUD API",
    description="RESTful API for task management with JWT authentication",
    version="1.0.0",
    lifespan=lifespan,
)

# Configure CORS
# Spec Reference: plan.md - CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# T021: Register task router
app.include_router(tasks.router)

# T015: Register reminder router
app.include_router(reminders.router)

# T017: Register internal Dapr callback router
app.include_router(internal.router)

# T022: Register audit router
app.include_router(audit.router)

# Register chat router for Phase 3 AI Chatbot
app.include_router(chat.router)


@app.get("/health")
async def health_check():
    """Health check endpoint (liveness probe).

    Returns:
        dict: Status information
    """
    return {"status": "ok"}


@app.get("/readyz")
async def readiness_check():
    """Readiness probe endpoint — checks database connectivity.

    Returns 200 if the service can reach the database, 503 otherwise.
    """
    from sqlmodel import text
    from app.database import engine

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception:
        from fastapi.responses import JSONResponse
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "reason": "database unreachable"},
        )
