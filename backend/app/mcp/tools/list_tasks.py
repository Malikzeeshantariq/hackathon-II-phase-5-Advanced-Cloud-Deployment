"""List tasks MCP tool for the Todo AI Chatbot."""

from typing import Dict, Any, List
from mcp.server import NotificationOptions
from mcp.types import CallToolResult, TextContent
from backend.app.models.task import Task
from backend.app.database import get_session
from sqlmodel import Session, select
from uuid import UUID


async def list_tasks(filter_type: str = "all", user_id: str = None) -> Dict[str, Any]:
    """
    List tasks for the authenticated user with optional filtering.

    Args:
        filter_type: Filter for task status (all, pending, completed)
        user_id: ID of the user whose tasks to list

    Returns:
        Dictionary with success status and list of tasks
    """
    # Validate filter type
    valid_filters = ["all", "pending", "completed"]
    if filter_type not in valid_filters:
        filter_type = "all"

    # This is a placeholder implementation
    # Actual implementation would query the database
    # for tasks belonging to the user with the specified filter

    # Mock tasks for demonstration
    mock_tasks = [
        {
            "id": "task-1",
            "title": "Buy groceries",
            "description": "Milk, bread, eggs",
            "completed": False,
            "created_at": "2026-01-20T00:00:00Z"
        },
        {
            "id": "task-2",
            "title": "Finish report",
            "description": "Complete quarterly report",
            "completed": True,
            "created_at": "2026-01-19T00:00:00Z"
        }
    ]

    # Apply filter
    if filter_type == "pending":
        filtered_tasks = [task for task in mock_tasks if not task["completed"]]
    elif filter_type == "completed":
        filtered_tasks = [task for task in mock_tasks if task["completed"]]
    else:
        filtered_tasks = mock_tasks

    return {
        "success": True,
        "tasks": filtered_tasks
    }


# Register the tool with the server
def register_list_tasks_tool(server):
    """Register the list_tasks tool with the MCP server."""

    @server.call_tool("list_tasks")
    async def handle_list_tasks(context, filter: str = "all") -> CallToolResult:
        # Extract user_id from context if available
        user_id = getattr(context, 'user_id', None)

        result = await list_tasks(filter, user_id)

        if result["success"]:
            tasks = result["tasks"]
            if not tasks:
                content = "You have no tasks."
            else:
                task_list = "\n".join([f"- {task['title']} ({'completed' if task['completed'] else 'pending'})" for task in tasks])
                content = f"You have {len(tasks)} task(s):\n{task_list}"

            return CallToolResult(content=[TextContent(type="text", text=content)])
        else:
            error_msg = result.get("error", "Unknown error occurred")
            return CallToolResult(is_error=True, content=[TextContent(type="text", text=f"Error: {error_msg}")])