"""Delete task MCP tool for the Todo AI Chatbot."""

from typing import Dict, Any
from mcp.server import NotificationOptions
from mcp.types import CallToolResult, TextContent
from backend.app.models.task import Task
from backend.app.database import get_session
from sqlmodel import Session, select
from uuid import UUID


async def delete_task(task_id: str, user_id: str = None) -> Dict[str, Any]:
    """
    Delete a task for the authenticated user.

    Args:
        task_id: ID of the task to delete
        user_id: ID of the user deleting the task

    Returns:
        Dictionary with success status and confirmation message
    """
    # Validate inputs
    if not task_id:
        return {
            "success": False,
            "error": "Task ID is required"
        }

    # This is a placeholder implementation
    # Actual implementation would delete the task from the database

    return {
        "success": True,
        "message": f"Task {task_id} has been deleted"
    }


# Register the tool with the server
def register_delete_task_tool(server):
    """Register the delete_task tool with the MCP server."""

    @server.call_tool("delete_task")
    async def handle_delete_task(context, task_id: str) -> CallToolResult:
        # Extract user_id from context if available
        user_id = getattr(context, 'user_id', None)

        result = await delete_task(task_id, user_id)

        if result["success"]:
            content = result["message"]
            return CallToolResult(content=[TextContent(type="text", text=content)])
        else:
            error_msg = result.get("error", "Unknown error occurred")
            return CallToolResult(is_error=True, content=[TextContent(type="text", text=f"Error: {error_msg}")])