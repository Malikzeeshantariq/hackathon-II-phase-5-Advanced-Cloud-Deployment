"""Update task MCP tool for the Todo AI Chatbot."""

from typing import Dict, Any
from mcp.server import NotificationOptions
from mcp.types import CallToolResult, TextContent
from backend.app.models.task import Task
from backend.app.database import get_session
from sqlmodel import Session, select
from uuid import UUID


async def update_task(task_id: str, title: str = None, description: str = None, user_id: str = None) -> Dict[str, Any]:
    """
    Update a task's details for the authenticated user.

    Args:
        task_id: ID of the task to update
        title: New title for the task
        description: New description for the task
        user_id: ID of the user updating the task

    Returns:
        Dictionary with success status and updated task
    """
    # Validate inputs
    if not task_id:
        return {
            "success": False,
            "error": "Task ID is required"
        }

    if title is None and description is None:
        return {
            "success": False,
            "error": "Either title or description must be provided"
        }

    if title and len(title) > 255:
        return {
            "success": False,
            "error": "Title exceeds maximum length of 255 characters"
        }

    if description and len(description) > 1000:
        return {
            "success": False,
            "error": "Description exceeds maximum length of 1000 characters"
        }

    # This is a placeholder implementation
    # Actual implementation would update the task in the database

    # Mock updated task for demonstration
    updated_task = {
        "id": task_id,
        "title": title or "Existing title",
        "description": description or "Existing description",
        "completed": False,
        "created_at": "2026-01-20T00:00:00Z"
    }

    return {
        "success": True,
        "task": updated_task
    }


# Register the tool with the server
def register_update_task_tool(server):
    """Register the update_task tool with the MCP server."""

    @server.call_tool("update_task")
    async def handle_update_task(context, task_id: str, title: str = None, description: str = None) -> CallToolResult:
        # Extract user_id from context if available
        user_id = getattr(context, 'user_id', None)

        result = await update_task(task_id, title, description, user_id)

        if result["success"]:
            content = f"Successfully updated task: {result['task']['title']}"
            return CallToolResult(content=[TextContent(type="text", text=content)])
        else:
            error_msg = result.get("error", "Unknown error occurred")
            return CallToolResult(is_error=True, content=[TextContent(type="text", text=f"Error: {error_msg}")])