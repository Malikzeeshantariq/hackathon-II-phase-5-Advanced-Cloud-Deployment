"""Database connection for Recurring Task Service."""

from sqlmodel import SQLModel, Session, create_engine
from typing import Generator

from app.config import get_settings
from app.models.processed_event import ProcessedEvent  # noqa: F401

settings = get_settings()

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)


def create_db_and_tables() -> None:
    SQLModel.metadata.create_all(engine)


def get_session() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session
