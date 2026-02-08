"""ProcessedEvent SQLModel definition — idempotency tracking.

Spec Reference: data-model.md Section 4 - ProcessedEvent Entity
Functional Requirements: FR-020, R-010
"""

from datetime import datetime, timezone
from uuid import UUID

from sqlmodel import SQLModel, Field


class ProcessedEvent(SQLModel, table=True):
    """Tracks processed event IDs for idempotent consumption.

    Before processing any event, consumers check if event_id exists.
    If it does, the event is skipped (dedup).
    """

    __tablename__ = "processed_event"

    event_id: UUID = Field(
        primary_key=True,
        description="CloudEvents event ID"
    )
    service_name: str = Field(
        max_length=50,
        nullable=False,
        description="Service that processed this event"
    )
    processed_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="When the event was processed"
    )
