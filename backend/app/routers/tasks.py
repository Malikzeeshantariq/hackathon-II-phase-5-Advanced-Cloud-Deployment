"""
[Task]: T010, T011, T012, T013, T014
[From]: specs/002-advanced-features-dapr/tasks.md §Phase 3 (US1), §Phase 4 (US2)
[Description]: Extend task CRUD routes with Phase V fields (priority, tags, due_at,
is_recurring, recurrence_rule), implement filtering/sorting/search, wire event publishing

T010: Extend task CRUD routes with priority, tags fields
T011: Implement filter, sort, search query parameters
T012: Wire event publishing into all task CRUD operations
T013: Implement due date create, update, remove in task routes
T014: Implement due date filtering and sorting
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import case, cast, String, Text
from sqlalchemy.dialects.postgresql import ARRAY as PG_ARRAY
from sqlmodel import Session, select

from app.database import get_session
from app.middleware.auth import TokenPayload, get_current_user, verify_user_access
from app.models.task import Task
from app.models.reminder import Reminder
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskListResponse,
    VALID_PRIORITIES,
    VALID_SORT_FIELDS,
    VALID_SORT_ORDERS,
)
from app.services.event_publisher import get_event_publisher, EventPublisher

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/{user_id}/tasks", tags=["Tasks"])


async def _publish_events_fire_and_forget(
    event_publisher: EventPublisher,
    event_type: str,
    task: Task,
    user_id: str,
) -> None:
    """
    Fire-and-forget event publishing helper.

    Publishes both task event and task update event asynchronously.
    Logs errors but does not raise exceptions.
    """
    try:
        await event_publisher.publish_task_event(event_type, task, user_id)
    except Exception as e:
        logger.error(f"Failed to publish task event '{event_type}': {str(e)}")

    try:
        await event_publisher.publish_task_update_event(event_type, task.id, user_id)
    except Exception as e:
        logger.error(f"Failed to publish task update event '{event_type}': {str(e)}")


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Creates a new task for the authenticated user with Phase V fields.",
)
async def create_task(
    user_id: str,
    task_data: TaskCreate,
    session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> Task:
    """T010, T013: Create a new task with Phase V fields.

    Spec Reference: FR-001 to FR-004, FR-018, FR-014
    - FR-001: User provides title (required) and description (optional)
    - FR-002: Task is associated with user_id from JWT
    - FR-003: completed defaults to false
    - FR-004: created_at is set automatically
    - Phase V: priority, tags, due_at, is_recurring, recurrence_rule
    - FR-018: Publish task event after creation
    - FR-014: Publish task update event after creation

    Args:
        user_id: User ID from URL path
        task_data: Task creation payload (including Phase V fields)
        session: Database session
        current_user: Authenticated user from JWT

    Returns:
        Task: Created task with all fields

    Raises:
        HTTPException: 403 if user_id doesn't match JWT
        HTTPException: 422 if validation fails
    """
    # AR-005: Verify URL user_id matches JWT user
    verify_user_access(current_user.user_id, user_id)

    # Create task with user_id from JWT (not from request body)
    task = Task(
        user_id=current_user.user_id,
        title=task_data.title,
        description=task_data.description,
        completed=False,  # FR-003: Default to incomplete
        # Phase V fields
        priority=task_data.priority,
        tags=task_data.tags or [],
        due_at=task_data.due_at,
        is_recurring=task_data.is_recurring,
        recurrence_rule=task_data.recurrence_rule,
    )

    session.add(task)
    session.commit()
    session.refresh(task)

    # T012: Fire-and-forget event publishing
    event_publisher = await get_event_publisher()
    asyncio.create_task(
        _publish_events_fire_and_forget(event_publisher, "created", task, current_user.user_id)
    )

    return task


@router.get(
    "",
    response_model=TaskListResponse,
    summary="List all tasks",
    description="Returns all tasks belonging to the authenticated user with filtering, sorting, and search.",
)
async def list_tasks(
    user_id: str,
    session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
    # T011, T014: Filter parameters
    priority: Optional[str] = Query(None, description="Filter by priority"),
    tags: Optional[str] = Query(None, description="Comma-separated tags (AND filter)"),
    task_status: Optional[str] = Query("all", alias="status", description="completed, pending, or all"),
    due_before: Optional[datetime] = Query(None, description="Upper bound for due_at"),
    due_after: Optional[datetime] = Query(None, description="Lower bound for due_at"),
    search: Optional[str] = Query(None, description="ILIKE search on title and description"),
    # T011, T014: Sort parameters
    sort_by: Optional[str] = Query("created_at", description="Sort field"),
    sort_order: Optional[str] = Query("desc", description="asc or desc"),
) -> TaskListResponse:
    """T011, T014: List all user tasks with filtering, sorting, and search.

    Spec Reference: FR-005, FR-006, FR-007, FR-008, SC-001, SC-002
    - FR-005: Retrieve tasks owned by authenticated user
    - FR-006: Response includes all task fields
    - FR-007: Support priority and tags filtering
    - FR-008: Support sorting by multiple fields
    - SC-001: Priority, tags, search, filter, sort work via API
    - SC-002: Due dates filter and sort work

    Query Parameters:
        priority: Filter by priority value (low, medium, high, critical)
        tags: Comma-separated tags for AND filtering
        status: Filter by completion status (completed, pending, all)
        due_before: Upper bound for due_at
        due_after: Lower bound for due_at
        search: ILIKE search on title and description
        sort_by: Sort field (created_at, due_at, priority, title)
        sort_order: Sort order (asc, desc)

    Args:
        user_id: User ID from URL path
        session: Database session
        current_user: Authenticated user from JWT

    Returns:
        TaskListResponse: List of user's tasks

    Raises:
        HTTPException: 403 if user_id doesn't match JWT
        HTTPException: 422 if invalid query parameters
    """
    # AR-005: Verify URL user_id matches JWT user
    verify_user_access(current_user.user_id, user_id)

    # Validate sort parameters
    if sort_by not in VALID_SORT_FIELDS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort_by. Must be one of: {', '.join(VALID_SORT_FIELDS)}",
        )
    if sort_order not in VALID_SORT_ORDERS:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid sort_order. Must be one of: {', '.join(VALID_SORT_ORDERS)}",
        )

    # Validate priority if provided
    if priority and priority not in VALID_PRIORITIES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid priority. Must be one of: {', '.join(VALID_PRIORITIES)}",
        )

    # Validate task_status if provided
    if task_status not in ["completed", "pending", "all"]:
        raise HTTPException(
            status_code=422,
            detail="Invalid status. Must be one of: completed, pending, all",
        )

    # Base query with user isolation
    statement = select(Task).where(Task.user_id == current_user.user_id)

    # T011: Apply filters
    if priority:
        statement = statement.where(Task.priority == priority)

    if tags:
        # Parse comma-separated tags and filter using PostgreSQL array contains (@>)
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        if tag_list:
            # Explicit cast to text[] to match the column type (text[], not varchar[])
            statement = statement.where(
                Task.tags.contains(cast(tag_list, PG_ARRAY(Text)))
            )

    if task_status == "completed":
        statement = statement.where(Task.completed == True)
    elif task_status == "pending":
        statement = statement.where(Task.completed == False)
    # "all" means no filter

    # T014: Due date filtering
    if due_before:
        statement = statement.where(Task.due_at <= due_before)
    if due_after:
        statement = statement.where(Task.due_at >= due_after)

    # T011: Search
    if search:
        search_pattern = f"%{search}%"
        statement = statement.where(
            (Task.title.ilike(search_pattern)) | (Task.description.ilike(search_pattern))
        )

    # T011, T014: Sorting
    if sort_by == "priority":
        # Priority sort order: critical=1, high=2, medium=3, low=4, NULL=5
        priority_order = case(
            (Task.priority == "critical", 1),
            (Task.priority == "high", 2),
            (Task.priority == "medium", 3),
            (Task.priority == "low", 4),
            else_=5,
        )
        if sort_order == "asc":
            statement = statement.order_by(priority_order.asc())
        else:
            statement = statement.order_by(priority_order.desc())
    elif sort_by == "due_at":
        # Tasks without due_at sort to end (NULLS LAST)
        if sort_order == "asc":
            statement = statement.order_by(Task.due_at.asc().nulls_last())
        else:
            statement = statement.order_by(Task.due_at.desc().nulls_last())
    elif sort_by == "title":
        if sort_order == "asc":
            statement = statement.order_by(Task.title.asc())
        else:
            statement = statement.order_by(Task.title.desc())
    else:  # created_at (default)
        if sort_order == "asc":
            statement = statement.order_by(Task.created_at.asc())
        else:
            statement = statement.order_by(Task.created_at.desc())

    # Execute query
    tasks = session.exec(statement).all()

    return TaskListResponse(tasks=list(tasks))


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task details",
    description="Returns details of a specific task.",
)
async def get_task(
    user_id: str,
    task_id: UUID,
    session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> Task:
    """T020: Get a single task by ID.

    Spec Reference: FR-005

    Args:
        user_id: User ID from URL path
        task_id: Task UUID
        session: Database session
        current_user: Authenticated user from JWT

    Returns:
        Task: Task details

    Raises:
        HTTPException: 403 if user_id doesn't match JWT
        HTTPException: 404 if task not found or not owned by user
    """
    # AR-005: Verify URL user_id matches JWT user
    verify_user_access(current_user.user_id, user_id)

    # Query with user isolation
    statement = select(Task).where(Task.id == task_id, Task.user_id == current_user.user_id)
    task = session.exec(statement).first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    return task


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    description="Updates task fields including Phase V fields (priority, tags, due_at, etc.).",
)
async def update_task(
    user_id: str,
    task_id: UUID,
    task_data: TaskUpdate,
    session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> Task:
    """T010, T013: Update an existing task with Phase V fields.

    Spec Reference: FR-007, FR-008, FR-018, FR-014
    - FR-007: Update title and/or description
    - FR-008: updated_at is automatically updated
    - Phase V: priority, tags, due_at, is_recurring, recurrence_rule
    - FR-018: Publish task event after update
    - FR-014: Publish task update event after update

    Args:
        user_id: User ID from URL path
        task_id: Task UUID
        task_data: Update payload (partial, including Phase V fields)
        session: Database session
        current_user: Authenticated user from JWT

    Returns:
        Task: Updated task

    Raises:
        HTTPException: 403 if user_id doesn't match JWT
        HTTPException: 404 if task not found or not owned by user
        HTTPException: 422 if validation fails (e.g., is_recurring without recurrence_rule)
    """
    # AR-005: Verify URL user_id matches JWT user
    verify_user_access(current_user.user_id, user_id)

    # Query with user isolation
    statement = select(Task).where(Task.id == task_id, Task.user_id == current_user.user_id)
    task = session.exec(statement).first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Update only provided fields
    if task_data.title is not None:
        task.title = task_data.title
    if task_data.description is not None:
        task.description = task_data.description

    # T010: Phase V fields
    if task_data.priority is not None:
        task.priority = task_data.priority
    if task_data.tags is not None:
        task.tags = task_data.tags
    # T013: Due date (setting to None removes it)
    if task_data.due_at is not None:
        task.due_at = task_data.due_at
    # Handle the case where the field is explicitly provided as None in the request
    elif "due_at" in task_data.model_fields_set:
        task.due_at = None

    if task_data.is_recurring is not None:
        # Validate: if setting is_recurring to True, must have recurrence_rule
        if task_data.is_recurring:
            # Check if recurrence_rule is being set in this update
            if task_data.recurrence_rule is None and not task.recurrence_rule:
                raise HTTPException(
                    status_code=422,
                    detail="recurrence_rule is required when is_recurring is true",
                )
        task.is_recurring = task_data.is_recurring

    if task_data.recurrence_rule is not None:
        task.recurrence_rule = task_data.recurrence_rule
    elif "recurrence_rule" in task_data.model_fields_set:
        task.recurrence_rule = None

    # FR-008: Auto-update timestamp
    task.updated_at = datetime.now(timezone.utc)

    session.add(task)
    session.commit()
    session.refresh(task)

    # T012: Fire-and-forget event publishing
    event_publisher = await get_event_publisher()
    asyncio.create_task(
        _publish_events_fire_and_forget(event_publisher, "updated", task, current_user.user_id)
    )

    return task


@router.patch(
    "/{task_id}/complete",
    response_model=TaskResponse,
    summary="Toggle task completion",
    description="Marks a task as completed or incomplete.",
)
async def complete_task(
    user_id: str,
    task_id: UUID,
    session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> Task:
    """T028, T012: Toggle task completion status with event publishing.

    Spec Reference: FR-009, FR-018, FR-014

    Args:
        user_id: User ID from URL path
        task_id: Task UUID
        session: Database session
        current_user: Authenticated user from JWT

    Returns:
        Task: Task with updated completion status

    Raises:
        HTTPException: 403 if user_id doesn't match JWT
        HTTPException: 404 if task not found or not owned by user
    """
    # AR-005: Verify URL user_id matches JWT user
    verify_user_access(current_user.user_id, user_id)

    # Query with user isolation
    statement = select(Task).where(Task.id == task_id, Task.user_id == current_user.user_id)
    task = session.exec(statement).first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Toggle completion status
    task.completed = not task.completed
    task.updated_at = datetime.now(timezone.utc)

    session.add(task)
    session.commit()
    session.refresh(task)

    # T012: Fire-and-forget event publishing (use "completed" event type if completed, "updated" otherwise)
    event_type = "completed" if task.completed else "updated"
    event_publisher = await get_event_publisher()
    asyncio.create_task(
        _publish_events_fire_and_forget(event_publisher, event_type, task, current_user.user_id)
    )

    return task


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a task",
    description="Permanently removes a task and cancels all associated reminder jobs.",
)
async def delete_task(
    user_id: str,
    task_id: UUID,
    session: Session = Depends(get_session),
    current_user: TokenPayload = Depends(get_current_user),
) -> None:
    """T032, T012: Delete a task with event publishing and reminder job cancellation.

    Spec Reference: FR-010, FR-011, FR-018, FR-014
    - FR-010: Delete a specific task
    - FR-011: Task is permanently removed (hard delete)
    - FR-018: Publish task event after deletion
    - FR-014: Publish task update event after deletion
    - Cancel all Dapr reminder jobs for this task

    Args:
        user_id: User ID from URL path
        task_id: Task UUID
        session: Database session
        current_user: Authenticated user from JWT

    Raises:
        HTTPException: 403 if user_id doesn't match JWT
        HTTPException: 404 if task not found or not owned by user
    """
    # AR-005: Verify URL user_id matches JWT user
    verify_user_access(current_user.user_id, user_id)

    # Query with user isolation
    statement = select(Task).where(Task.id == task_id, Task.user_id == current_user.user_id)
    task = session.exec(statement).first()

    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Query all reminders for this task to cancel their Dapr jobs
    reminders_statement = select(Reminder).where(
        Reminder.task_id == task_id, Reminder.user_id == current_user.user_id
    )
    reminders = session.exec(reminders_statement).all()

    # Cancel all reminder Dapr jobs (fire-and-forget)
    event_publisher = await get_event_publisher()
    for reminder in reminders:
        job_name = f"reminder-{reminder.id}"
        asyncio.create_task(event_publisher.cancel_reminder_job(job_name))

    # T012: Fire-and-forget event publishing BEFORE deletion (task data needed)
    asyncio.create_task(
        _publish_events_fire_and_forget(event_publisher, "deleted", task, current_user.user_id)
    )

    # Delete task (CASCADE will delete reminders)
    session.delete(task)
    session.commit()
