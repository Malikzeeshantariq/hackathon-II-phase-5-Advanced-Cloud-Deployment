"""
[Task]: T024
[From]: specs/002-advanced-features-dapr/tasks.md §Phase 8
[Description]: MCP Server — Extended tool schemas with Phase V fields + new tools registered
"""

import asyncio
from typing import Dict, Any
from mcp.server import Server
from mcp.types import CallToolResult, TextContent, Tool, ArgumentsSchema


# Initialize MCP server
server = Server("todo-ai-chatbot-server")


@server.list_tools()
def list_tools() -> list[Tool]:
    """List all available tools."""
    return [
        Tool(
            name="add_task",
            description="Create a new task. Supports priority (low/medium/high/critical), tags, due dates, and recurring rules.",
            inputSchema={
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title of the task",
                        "minLength": 1,
                        "maxLength": 255
                    },
                    "description": {
                        "type": "string",
                        "description": "Optional description of the task",
                        "maxLength": 1000
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Task priority level"
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of tags for categorization"
                    },
                    "due_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Due date in ISO8601 format"
                    },
                    "is_recurring": {
                        "type": "boolean",
                        "description": "Whether the task recurs on completion",
                        "default": False
                    },
                    "recurrence_rule": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly"],
                        "description": "Recurrence rule (required if is_recurring=true)"
                    }
                },
                "required": ["title"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="list_tasks",
            description="List tasks with optional filtering by status/priority/tags, search by keyword, and sorting.",
            inputSchema={
                "type": "object",
                "properties": {
                    "filter_type": {
                        "type": "string",
                        "enum": ["all", "pending", "completed"],
                        "description": "Filter by task status",
                        "default": "all"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "Filter by priority level"
                    },
                    "tags": {
                        "type": "string",
                        "description": "Comma-separated tags to filter by (AND match)"
                    },
                    "search": {
                        "type": "string",
                        "description": "Search keyword (matches title and description)"
                    },
                    "sort_by": {
                        "type": "string",
                        "enum": ["created_at", "due_at", "priority", "title"],
                        "description": "Field to sort by",
                        "default": "created_at"
                    },
                    "sort_order": {
                        "type": "string",
                        "enum": ["asc", "desc"],
                        "description": "Sort direction",
                        "default": "desc"
                    }
                },
                "additionalProperties": False
            }
        ),
        Tool(
            name="complete_task",
            description="Mark a task as completed by title or partial title match.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_title": {
                        "type": "string",
                        "description": "Title or partial title of the task to complete"
                    }
                },
                "required": ["task_title"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="delete_task",
            description="Delete a task by title or partial title match.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_title": {
                        "type": "string",
                        "description": "Title or partial title of the task to delete"
                    }
                },
                "required": ["task_title"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="update_task",
            description="Update a task's fields including title, description, priority, tags, due date, and recurring settings.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_title": {
                        "type": "string",
                        "description": "Title or partial title of the task to update"
                    },
                    "new_title": {
                        "type": "string",
                        "description": "New title for the task",
                        "minLength": 1,
                        "maxLength": 255
                    },
                    "new_description": {
                        "type": "string",
                        "description": "New description for the task",
                        "maxLength": 1000
                    },
                    "new_priority": {
                        "type": "string",
                        "enum": ["low", "medium", "high", "critical"],
                        "description": "New priority level"
                    },
                    "new_tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "New list of tags"
                    },
                    "new_due_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "New due date in ISO8601 format"
                    },
                    "new_is_recurring": {
                        "type": "boolean",
                        "description": "Set whether task recurs"
                    },
                    "new_recurrence_rule": {
                        "type": "string",
                        "enum": ["daily", "weekly", "monthly"],
                        "description": "New recurrence rule"
                    }
                },
                "required": ["task_title"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="set_reminder",
            description="Set a reminder for a task at a specific time.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_title": {
                        "type": "string",
                        "description": "Title or partial title of the task to set a reminder for"
                    },
                    "remind_at": {
                        "type": "string",
                        "format": "date-time",
                        "description": "When to trigger the reminder (ISO8601 format, must be in the future)"
                    }
                },
                "required": ["task_title", "remind_at"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="list_reminders",
            description="List all reminders for a specific task.",
            inputSchema={
                "type": "object",
                "properties": {
                    "task_title": {
                        "type": "string",
                        "description": "Title or partial title of the task"
                    }
                },
                "required": ["task_title"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="delete_reminder",
            description="Delete a specific reminder by its UUID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "reminder_id": {
                        "type": "string",
                        "format": "uuid",
                        "description": "UUID of the reminder to delete"
                    }
                },
                "required": ["reminder_id"],
                "additionalProperties": False
            }
        ),
        Tool(
            name="search_tasks",
            description="Search tasks by keyword in title and description.",
            inputSchema={
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Search keyword to match against task titles and descriptions"
                    }
                },
                "required": ["keyword"],
                "additionalProperties": False
            }
        ),
    ]


async def run_server():
    """Run the MCP server."""
    async with server.serve_process():
        await asyncio.Future()  # Run forever


if __name__ == "__main__":
    asyncio.run(run_server())
