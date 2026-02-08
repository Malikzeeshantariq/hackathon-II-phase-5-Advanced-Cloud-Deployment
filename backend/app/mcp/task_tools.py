"""
[Task]: T023, T024
[From]: specs/002-advanced-features-dapr/tasks.md §Phase 8
[Description]: MCP Task Tools — Extended with Phase V fields + new reminder/search tools

T023: Extend existing tools (add_task, list_tasks, update_task) with priority, tags, due_at, etc.
T024: Add new tools (set_reminder, list_reminders, delete_reminder, search_tasks)
"""

from typing import List, Optional
from datetime import datetime, timezone
from uuid import UUID, uuid4
from sqlalchemy import case
from sqlmodel import Session, select
from app.models.task import Task
from app.models.reminder import Reminder
from agents import function_tool


class TaskTools:
    """Task management tools for the AI Agent."""

    def __init__(self, db_session: Session, user_id: str):
        self.db_session = db_session
        self.user_id = user_id

    def _task_to_dict(self, task: Task) -> dict:
        """Convert task to response dict with all Phase V fields."""
        return {
            "id": str(task.id),
            "title": task.title,
            "description": task.description,
            "completed": task.completed,
            "priority": task.priority,
            "tags": task.tags or [],
            "due_at": task.due_at.isoformat() if task.due_at else None,
            "is_recurring": task.is_recurring,
            "recurrence_rule": task.recurrence_rule,
            "created_at": task.created_at.isoformat(),
        }

    def add_task(
        self,
        title: str,
        description: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[List[str]] = None,
        due_at: Optional[str] = None,
        is_recurring: bool = False,
        recurrence_rule: Optional[str] = None,
    ) -> dict:
        """Add a new task with Phase V fields."""
        parsed_due_at = None
        if due_at:
            try:
                parsed_due_at = datetime.fromisoformat(due_at.replace("Z", "+00:00"))
            except ValueError:
                return {"success": False, "error": f"Invalid due_at format: {due_at}"}

        task = Task(
            id=uuid4(),
            user_id=self.user_id,
            title=title,
            description=description,
            completed=False,
            priority=priority,
            tags=tags or [],
            due_at=parsed_due_at,
            is_recurring=is_recurring,
            recurrence_rule=recurrence_rule,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self.db_session.add(task)
        self.db_session.commit()
        self.db_session.refresh(task)

        return {"success": True, "task": self._task_to_dict(task)}

    def list_tasks(
        self,
        filter_type: str = "all",
        priority: Optional[str] = None,
        tags: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict:
        """List tasks with filtering, sorting, and search."""
        statement = select(Task).where(Task.user_id == self.user_id)

        if filter_type == "completed":
            statement = statement.where(Task.completed == True)
        elif filter_type == "pending":
            statement = statement.where(Task.completed == False)

        if priority:
            statement = statement.where(Task.priority == priority)

        if tags:
            tag_list = [t.strip() for t in tags.split(",") if t.strip()]
            if tag_list:
                statement = statement.where(Task.tags.contains(tag_list))

        if search:
            pattern = f"%{search}%"
            statement = statement.where(
                (Task.title.ilike(pattern)) | (Task.description.ilike(pattern))
            )

        # Sorting
        if sort_by == "priority":
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
            if sort_order == "asc":
                statement = statement.order_by(Task.due_at.asc().nulls_last())
            else:
                statement = statement.order_by(Task.due_at.desc().nulls_last())
        elif sort_by == "title":
            if sort_order == "asc":
                statement = statement.order_by(Task.title.asc())
            else:
                statement = statement.order_by(Task.title.desc())
        else:
            if sort_order == "asc":
                statement = statement.order_by(Task.created_at.asc())
            else:
                statement = statement.order_by(Task.created_at.desc())

        tasks = self.db_session.exec(statement).all()

        return {
            "success": True,
            "tasks": [self._task_to_dict(t) for t in tasks],
            "count": len(tasks),
        }

    def complete_task(self, task_title: str) -> dict:
        """Mark a task as completed by title."""
        statement = select(Task).where(
            Task.user_id == self.user_id,
            Task.title.ilike(f"%{task_title}%"),
        )
        task = self.db_session.exec(statement).first()

        if not task:
            return {"success": False, "error": f"No task found matching '{task_title}'"}

        task.completed = True
        task.updated_at = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(task)

        return {
            "success": True,
            "task": self._task_to_dict(task),
            "message": f"Task '{task.title}' marked as completed",
        }

    def delete_task(self, task_title: str) -> dict:
        """Delete a task by title."""
        statement = select(Task).where(
            Task.user_id == self.user_id,
            Task.title.ilike(f"%{task_title}%"),
        )
        task = self.db_session.exec(statement).first()

        if not task:
            return {"success": False, "error": f"No task found matching '{task_title}'"}

        title_saved = task.title
        self.db_session.delete(task)
        self.db_session.commit()

        return {"success": True, "message": f"Task '{title_saved}' has been deleted"}

    def update_task(
        self,
        task_title: str,
        new_title: Optional[str] = None,
        new_description: Optional[str] = None,
        new_priority: Optional[str] = None,
        new_tags: Optional[List[str]] = None,
        new_due_at: Optional[str] = None,
        new_is_recurring: Optional[bool] = None,
        new_recurrence_rule: Optional[str] = None,
    ) -> dict:
        """Update a task by title with Phase V fields."""
        statement = select(Task).where(
            Task.user_id == self.user_id,
            Task.title.ilike(f"%{task_title}%"),
        )
        task = self.db_session.exec(statement).first()

        if not task:
            return {"success": False, "error": f"No task found matching '{task_title}'"}

        if new_title:
            task.title = new_title
        if new_description is not None:
            task.description = new_description
        if new_priority is not None:
            task.priority = new_priority
        if new_tags is not None:
            task.tags = new_tags
        if new_due_at is not None:
            try:
                task.due_at = datetime.fromisoformat(new_due_at.replace("Z", "+00:00"))
            except ValueError:
                return {"success": False, "error": f"Invalid due_at format: {new_due_at}"}
        if new_is_recurring is not None:
            task.is_recurring = new_is_recurring
        if new_recurrence_rule is not None:
            task.recurrence_rule = new_recurrence_rule

        task.updated_at = datetime.now(timezone.utc)
        self.db_session.commit()
        self.db_session.refresh(task)

        return {"success": True, "task": self._task_to_dict(task), "message": "Task updated successfully"}

    # --- T024: New tools ---

    def set_reminder(self, task_title: str, remind_at: str) -> dict:
        """Create a reminder for a task."""
        statement = select(Task).where(
            Task.user_id == self.user_id,
            Task.title.ilike(f"%{task_title}%"),
        )
        task = self.db_session.exec(statement).first()

        if not task:
            return {"success": False, "error": f"No task found matching '{task_title}'"}

        try:
            parsed_remind_at = datetime.fromisoformat(remind_at.replace("Z", "+00:00"))
        except ValueError:
            return {"success": False, "error": f"Invalid remind_at format: {remind_at}"}

        reminder = Reminder(
            id=uuid4(),
            task_id=task.id,
            user_id=self.user_id,
            remind_at=parsed_remind_at,
        )
        self.db_session.add(reminder)
        self.db_session.commit()
        self.db_session.refresh(reminder)

        return {
            "success": True,
            "reminder": {
                "id": str(reminder.id),
                "task_id": str(reminder.task_id),
                "task_title": task.title,
                "remind_at": reminder.remind_at.isoformat(),
            },
            "message": f"Reminder set for '{task.title}' at {remind_at}",
        }

    def list_reminders(self, task_title: str) -> dict:
        """List reminders for a task."""
        statement = select(Task).where(
            Task.user_id == self.user_id,
            Task.title.ilike(f"%{task_title}%"),
        )
        task = self.db_session.exec(statement).first()

        if not task:
            return {"success": False, "error": f"No task found matching '{task_title}'"}

        reminders_stmt = select(Reminder).where(
            Reminder.task_id == task.id,
            Reminder.user_id == self.user_id,
        ).order_by(Reminder.remind_at)
        reminders = self.db_session.exec(reminders_stmt).all()

        return {
            "success": True,
            "task_title": task.title,
            "reminders": [
                {
                    "id": str(r.id),
                    "remind_at": r.remind_at.isoformat(),
                    "created_at": r.created_at.isoformat(),
                }
                for r in reminders
            ],
            "count": len(reminders),
        }

    def delete_reminder(self, reminder_id: str) -> dict:
        """Delete a reminder by ID."""
        try:
            rid = UUID(reminder_id)
        except ValueError:
            return {"success": False, "error": f"Invalid reminder_id: {reminder_id}"}

        statement = select(Reminder).where(
            Reminder.id == rid,
            Reminder.user_id == self.user_id,
        )
        reminder = self.db_session.exec(statement).first()

        if not reminder:
            return {"success": False, "error": f"Reminder {reminder_id} not found"}

        self.db_session.delete(reminder)
        self.db_session.commit()

        return {"success": True, "message": f"Reminder {reminder_id} deleted"}

    def search_tasks(self, keyword: str) -> dict:
        """Search tasks by keyword (ILIKE on title and description)."""
        pattern = f"%{keyword}%"
        statement = select(Task).where(
            Task.user_id == self.user_id,
            (Task.title.ilike(pattern)) | (Task.description.ilike(pattern)),
        ).order_by(Task.created_at.desc())

        tasks = self.db_session.exec(statement).all()

        return {
            "success": True,
            "tasks": [self._task_to_dict(t) for t in tasks],
            "count": len(tasks),
            "keyword": keyword,
        }


def create_task_tools(db_session: Session, user_id: str) -> List:
    """Create function tools for the AI Agent."""
    task_tools = TaskTools(db_session, user_id)

    @function_tool
    def add_task(
        title: str,
        description: str = None,
        priority: str = None,
        tags: list[str] = None,
        due_at: str = None,
        is_recurring: bool = False,
        recurrence_rule: str = None,
    ) -> dict:
        """Add a new task. Supports priority (low/medium/high/critical), tags, due_at (ISO8601), recurring rules."""
        return task_tools.add_task(title, description, priority, tags, due_at, is_recurring, recurrence_rule)

    @function_tool
    def list_tasks(
        filter_type: str = "all",
        priority: str = None,
        tags: str = None,
        search: str = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> dict:
        """List tasks with optional filtering by status/priority/tags, search, and sorting."""
        return task_tools.list_tasks(filter_type, priority, tags, search, sort_by, sort_order)

    @function_tool
    def complete_task(task_title: str) -> dict:
        """Mark a task as completed by title or partial title match."""
        return task_tools.complete_task(task_title)

    @function_tool
    def delete_task(task_title: str) -> dict:
        """Delete a task by title or partial title match."""
        return task_tools.delete_task(task_title)

    @function_tool
    def update_task(
        task_title: str,
        new_title: str = None,
        new_description: str = None,
        new_priority: str = None,
        new_tags: list[str] = None,
        new_due_at: str = None,
        new_is_recurring: bool = None,
        new_recurrence_rule: str = None,
    ) -> dict:
        """Update a task's fields including priority, tags, due_at, recurring settings."""
        return task_tools.update_task(
            task_title, new_title, new_description, new_priority, new_tags,
            new_due_at, new_is_recurring, new_recurrence_rule,
        )

    @function_tool
    def set_reminder(task_title: str, remind_at: str) -> dict:
        """Set a reminder for a task at a specific time (ISO8601 format)."""
        return task_tools.set_reminder(task_title, remind_at)

    @function_tool
    def list_reminders(task_title: str) -> dict:
        """List all reminders for a task."""
        return task_tools.list_reminders(task_title)

    @function_tool
    def delete_reminder(reminder_id: str) -> dict:
        """Delete a specific reminder by its UUID."""
        return task_tools.delete_reminder(reminder_id)

    @function_tool
    def search_tasks(keyword: str) -> dict:
        """Search tasks by keyword in title and description."""
        return task_tools.search_tasks(keyword)

    return [
        add_task, list_tasks, complete_task, delete_task, update_task,
        set_reminder, list_reminders, delete_reminder, search_tasks,
    ]
