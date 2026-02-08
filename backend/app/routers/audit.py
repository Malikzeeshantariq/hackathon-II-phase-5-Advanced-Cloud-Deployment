"""
[Task]: T022
[From]: specs/002-advanced-features-dapr/tasks.md §Phase 7 (US5)
[Description]: Audit query route — GET /api/{user_id}/audit

Queries audit_entry table filtered by user_id (user isolation).
Supports filtering by task_id, event_type, with pagination.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session, select

from app.database import get_session
from app.middleware.auth import TokenPayload, get_current_user, verify_user_access

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/{user_id}/audit", tags=["Audit"])


# We import the AuditEntry model from the audit service models
# Since audit_entry table is in the same database, we can query it directly
from sqlalchemy import Column, Index, JSON, text
from sqlmodel import SQLModel, Field
from datetime import datetime
from typing import Any, Dict


class AuditEntryRead(SQLModel, table=True):
    """Read-only view of audit_entry table for querying."""

    __tablename__ = "audit_entry"
    __table_args__ = {"extend_existing": True}

    id: UUID = Field(primary_key=True)
    event_type: str = Field(max_length=20)
    task_id: UUID
    user_id: str
    event_data: Dict[str, Any] = Field(sa_column=Column(JSON, nullable=False))
    timestamp: datetime


from pydantic import BaseModel


class AuditEntryResponse(BaseModel):
    """Response schema for audit entries."""

    id: UUID
    event_type: str
    task_id: UUID
    user_id: str
    event_data: dict
    timestamp: datetime

    class Config:
        from_attributes = True


VALID_EVENT_TYPES = {"created", "updated", "completed", "deleted"}


@router.get(
    "",
    response_model=List[AuditEntryResponse],
    summary="List audit entries for user",
)
async def list_audit_entries(
    user_id: str,
    session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
    task_id: Optional[UUID] = Query(None, description="Filter by task ID"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    limit: int = Query(50, ge=1, le=200, description="Max entries"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> List[AuditEntryRead]:
    """T022: List audit entries with filtering and pagination.

    Queries audit_entry table filtered by user_id for data isolation.
    """
    verify_user_access(current_user.user_id, user_id)

    if event_type and event_type not in VALID_EVENT_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid event_type. Must be one of: {', '.join(VALID_EVENT_TYPES)}",
        )

    stmt = select(AuditEntryRead).where(AuditEntryRead.user_id == current_user.user_id)

    if task_id:
        stmt = stmt.where(AuditEntryRead.task_id == task_id)
    if event_type:
        stmt = stmt.where(AuditEntryRead.event_type == event_type)

    stmt = stmt.order_by(AuditEntryRead.timestamp.desc()).offset(offset).limit(limit)
    entries = session.exec(stmt).all()

    return list(entries)
