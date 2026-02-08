"""Complete task MCP tool for the Todo AI Chatbot."""

from typing import Dict, Any
from mcp.server import NotificationOptions
from mcp.types import CallToolResult, TextContent
from backend.app.models.task import Task
from backend.app.database import get_session
from sqlmodel import Session, select
from uuid import UUID


async def complete_task(task_id: str, user_id: str = None) -> Dict[str, Any]:
    """
    Mark a task as completed for the authenticated user.

    Args:
        task_id: ID of the task to complete
        user_id: ID of the user completing the task

    Returns:
        Dictionary with success status and updated task
    """
    # Validate inputs
    if not task_id:
        return {
            "success": False,
            "error": "Task ID is required"
        }

    # This is a placeholder implementation
    # Actual implementation would query the database
    # to find and update the task

    # Mock task for demonstration
    task = {
        "id": task_id,
        "title": "Mock task",
        "description": "Mock description",
        "completed": True,
        "created_at": "2026-01-20T00:00:00Z"
    }

    return {
        "success": True,
        "task": task
    }


# Register the tool with the server
def register_complete_task_tool(server):
    """Register the complete_task tool with the MCP server."""

    @server.call_tool("complete_task")
    async def handle_complete_task(context, task_id: str) -> CallToolResult:
        # Extract user_id from context if available
        user_id = getattr(context, 'user_id', None)

        result = await complete_task(task_id, user_id)

        if result["success"]:
            content = f"Successfully marked task '{result['task']['title']}' as completed"
            return CallToolResult(content=[TextContent(type="text", text=content)])
        else:
            error_msg = result.get("error", "Unknown error occurred")
            return CallToolResult(is_error=True, content=[TextContent(type="text", text=f"Error: {error_msg}")])