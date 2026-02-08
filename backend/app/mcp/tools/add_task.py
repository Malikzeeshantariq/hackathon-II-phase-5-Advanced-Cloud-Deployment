"""Add task MCP tool for the Todo AI Chatbot."""

from typing import Dict, Any
from mcp.server import NotificationOptions
from mcp.types import CallToolResult, TextContent
from backend.app.models.task import Task
from backend.app.database import get_session
from sqlmodel import Session, select
from uuid import UUID


async def add_task(title: str, description: str = None, user_id: str = None) -> Dict[str, Any]:
    """
    Create a new task for the authenticated user.

    Args:
        title: Title of the task
        description: Optional description of the task
        user_id: ID of the user creating the task

    Returns:
        Dictionary with success status and created task
    """
    # This is a placeholder implementation
    # Actual implementation will connect to the database
    # and create the task using SQLModel

    # Validate inputs
    if not title or len(title.strip()) == 0:
        return {
            "success": False,
            "error": "Title is required"
        }

    if len(title) > 255:
        return {
            "success": False,
            "error": "Title exceeds maximum length of 255 characters"
        }

    if description and len(description) > 1000:
        return {
            "success": False,
            "error": "Description exceeds maximum length of 1000 characters"
        }

    # In a real implementation, this would create a task in the database
    # For now, return a mock task
    task = {
        "id": "mock-task-id",
        "title": title,
        "description": description,
        "completed": False,
        "created_at": "2026-01-20T00:00:00Z"
    }

    return {
        "success": True,
        "task": task
    }


# Register the tool with the server
def register_add_task_tool(server):
    """Register the add_task tool with the MCP server."""

    @server.call_tool("add_task")
    async def handle_add_task(context, title: str, description: str = None) -> CallToolResult:
        # Extract user_id from context if available
        user_id = getattr(context, 'user_id', None)

        result = await add_task(title, description, user_id)

        if result["success"]:
            content = f"Successfully created task: {result['task']['title']}"
            return CallToolResult(content=[TextContent(type="text", text=content)])
        else:
            error_msg = result.get("error", "Unknown error occurred")
            return CallToolResult(is_error=True, content=[TextContent(type="text", text=f"Error: {error_msg}")])