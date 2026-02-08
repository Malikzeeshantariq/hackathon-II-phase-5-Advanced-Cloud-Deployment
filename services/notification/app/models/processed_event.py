"""ProcessedEvent model for Notification Service idempotency."""

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import SQLModel, Field


class ProcessedEvent(SQLModel, table=True):
    """Tracks processed event IDs for idempotent consumption."""

    __tablename__ = "processed_event"

    event_id: UUID = Field(primary_key=True)
    service_name: str = Field(max_length=50, nullable=False)
    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
