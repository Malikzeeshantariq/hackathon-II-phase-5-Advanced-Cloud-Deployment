"""Dapr Pub/Sub event publisher service.

Publishes task events to Dapr Pub/Sub using CloudEvents 1.0 specification.
No direct Kafka client imports (FR-021, Constitution Gate 5).
"""

import logging
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from uuid import UUID

import httpx
from pydantic import BaseModel

from ..schemas.events import TaskEventPayload, TaskUpdateEventPayload, ReminderEventPayload

logger = logging.getLogger(__name__)

# Dapr sidecar configuration
DAPR_SIDECAR_URL = "http://localhost:3500"
DAPR_API_VERSION = "v1.0"


class CloudEvent(BaseModel):
    """CloudEvents 1.0 envelope for Dapr Pub/Sub."""

    id: str
    source: str = "todo-backend"
    type: str
    data: Any
    datacontenttype: str = "application/json"
    specversion: str = "1.0"
    time: datetime


class EventPublisher:
    """Service for publishing events to Dapr Pub/Sub."""

    def __init__(self, dapr_sidecar_url: str = DAPR_SIDECAR_URL):
        self.dapr_sidecar_url = dapr_sidecar_url
        self.http_client = httpx.AsyncClient(timeout=10.0)

    async def close(self):
        """Close the HTTP client."""
        await self.http_client.aclose()

    async def publish_task_event(
        self, event_type: str, task: Any, user_id: str
    ) -> bool:
        """
        Publish a task event to the task-events topic.

        Args:
            event_type: created, updated, completed, deleted
            task: Task object with all required fields
            user_id: User ID from JWT

        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Create task data snapshot
            task_data = {
                "title": task.title,
                "description": task.description,
                "completed": task.completed,
                "priority": task.priority,
                "tags": task.tags,
                "due_at": task.due_at,
                "is_recurring": task.is_recurring,
                "recurrence_rule": task.recurrence_rule,
            }

            # Create event payload
            payload = TaskEventPayload(
                event_type=event_type,
                task_id=task.id,
                user_id=user_id,
                task_data=task_data,
                timestamp=datetime.now(timezone.utc),
            )

            # Create CloudEvent envelope
            cloud_event = CloudEvent(
                id=str(uuid.uuid4()),
                type=f"com.todo.task.{event_type}",
                data=payload.model_dump(mode="json"),
                time=datetime.now(timezone.utc),
            )

            # Publish to Dapr
            topic_name = "task-events"
            url = f"{self.dapr_sidecar_url}/{DAPR_API_VERSION}/publish/pubsub/{topic_name}"

            response = await self.http_client.post(
                url, json=cloud_event.model_dump(mode="json"), headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                logger.info(f"Task event '{event_type}' published successfully to {topic_name}")
                return True
            else:
                logger.error(
                    f"Failed to publish task event: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error publishing task event: {str(e)}")
            return False

    async def publish_task_update_event(
        self, change_type: str, task_id: UUID, user_id: str
    ) -> bool:
        """
        Publish a task update event to the task-updates topic.

        Args:
            change_type: created, updated, completed, deleted
            task_id: Task UUID
            user_id: User ID from JWT

        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Create event payload
            payload = TaskUpdateEventPayload(
                task_id=task_id,
                user_id=user_id,
                change_type=change_type,
                timestamp=datetime.now(timezone.utc),
            )

            # Create CloudEvent envelope
            cloud_event = CloudEvent(
                id=str(uuid.uuid4()),
                type=f"com.todo.task.update.{change_type}",
                data=payload.model_dump(mode="json"),
                time=datetime.now(timezone.utc),
            )

            # Publish to Dapr
            topic_name = "task-updates"
            url = f"{self.dapr_sidecar_url}/{DAPR_API_VERSION}/publish/pubsub/{topic_name}"

            response = await self.http_client.post(
                url, json=cloud_event.model_dump(mode="json"), headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                logger.info(f"Task update event '{change_type}' published successfully to {topic_name}")
                return True
            else:
                logger.error(
                    f"Failed to publish task update event: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error publishing task update event: {str(e)}")
            return False

    async def publish_reminder_event(
        self, reminder_id: UUID, task: Any, user_id: str, remind_at: datetime
    ) -> bool:
        """
        Publish a reminder event to the reminders topic.

        Args:
            reminder_id: Reminder UUID
            task: Task object
            user_id: User ID from JWT
            remind_at: When the reminder should fire

        Returns:
            True if published successfully, False otherwise
        """
        try:
            # Create event payload
            payload = ReminderEventPayload(
                reminder_id=reminder_id,
                task_id=task.id,
                title=task.title,
                user_id=user_id,
                due_at=task.due_at,
                remind_at=remind_at,
                timestamp=datetime.now(timezone.utc),
            )

            # Create CloudEvent envelope
            cloud_event = CloudEvent(
                id=str(uuid.uuid4()),
                type="com.todo.reminder.trigger",
                data=payload.model_dump(mode="json"),
                time=datetime.now(timezone.utc),
            )

            # Publish to Dapr
            topic_name = "reminders"
            url = f"{self.dapr_sidecar_url}/{DAPR_API_VERSION}/publish/pubsub/{topic_name}"

            response = await self.http_client.post(
                url, json=cloud_event.model_dump(mode="json"), headers={"Content-Type": "application/json"}
            )

            if response.status_code == 200:
                logger.info(f"Reminder event published successfully to {topic_name}")
                return True
            else:
                logger.error(
                    f"Failed to publish reminder event: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error publishing reminder event: {str(e)}")
            return False

    async def schedule_reminder_job(
        self, job_name: str, schedule_time: datetime, data: Dict[str, Any]
    ) -> bool:
        """
        Schedule a Dapr Job for a reminder.

        Args:
            job_name: Unique job identifier
            schedule_time: When the job should execute (ISO8601 format)
            data: Data to pass to the job callback

        Returns:
            True if scheduled successfully, False otherwise
        """
        try:
            # Format the time as ISO8601 string for cron expression
            # For precise scheduling, we'll use Dapr's one-time job feature
            job_payload = {
                "name": job_name,
                "schedule": schedule_time.isoformat(),  # Dapr supports ISO8601 for one-time jobs
                "data": data,
                "retries": 3,
                "retryDelay": 10
            }

            url = f"{self.dapr_sidecar_url}/{DAPR_API_VERSION}-alpha1/jobs/{job_name}"

            response = await self.http_client.post(
                url, json=job_payload, headers={"Content-Type": "application/json"}
            )

            if response.status_code in [200, 201]:
                logger.info(f"Dapr job '{job_name}' scheduled successfully")
                return True
            else:
                logger.error(
                    f"Failed to schedule Dapr job: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error scheduling Dapr job: {str(e)}")
            return False

    async def cancel_reminder_job(self, job_name: str) -> bool:
        """
        Cancel a scheduled Dapr Job.

        Args:
            job_name: Job identifier to cancel

        Returns:
            True if canceled successfully, False otherwise
        """
        try:
            url = f"{self.dapr_sidecar_url}/{DAPR_API_VERSION}-alpha1/jobs/{job_name}"

            response = await self.http_client.delete(url)

            if response.status_code == 204:
                logger.info(f"Dapr job '{job_name}' canceled successfully")
                return True
            elif response.status_code == 404:
                # Job doesn't exist, which is acceptable
                logger.info(f"Dapr job '{job_name}' not found (already canceled?)")
                return True
            else:
                logger.error(
                    f"Failed to cancel Dapr job: {response.status_code} - {response.text}"
                )
                return False

        except Exception as e:
            logger.error(f"Error canceling Dapr job: {str(e)}")
            return False


# Global event publisher instance
event_publisher = EventPublisher()


async def get_event_publisher() -> EventPublisher:
    """Get the global event publisher instance."""
    return event_publisher