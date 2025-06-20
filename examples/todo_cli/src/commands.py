"""Command implementations for todo operations."""

from typing import List, Optional

from .formatters import TodoFormatter
from .models import Priority, Status, Todo
from .storage import StorageBackend


class TodoCommands:
    """Business logic for todo operations."""

    def __init__(self, storage: StorageBackend):
        self.storage = storage
        self.formatter = TodoFormatter()

    def add(self, title: str, description: str = "",
            priority: str = "medium", tags: Optional[List[str]] = None) -> Todo:
        """Add a new todo."""
        # Convert priority string to enum
        priority_map = {
            "low": Priority.LOW,
            "medium": Priority.MEDIUM,
            "high": Priority.HIGH
        }

        if priority not in priority_map:
            raise ValueError(f"Invalid priority: {priority}. Must be one of: low, medium, high")

        todo = Todo(
            title=title,
            description=description,
            priority=priority_map[priority],
            tags=tags or []
        )

        self.storage.save(todo)
        return todo

    def list_todos(self, status: Optional[str] = None,
                   tag: Optional[str] = None,
                   search: Optional[str] = None) -> List[Todo]:
        """List todos with optional filters."""
        todos = self.storage.get_all()

        # Apply filters
        if status:
            status_map = {
                "pending": Status.PENDING,
                "completed": Status.COMPLETED
            }
            if status not in status_map:
                raise ValueError(f"Invalid status: {status}. Must be one of: pending, completed")
            todos = [t for t in todos if t.status == status_map[status]]

        if tag:
            todos = [t for t in todos if t.has_tag(tag)]

        if search:
            todos = [t for t in todos if t.matches_search(search)]

        return todos

    def complete(self, todo_id: str) -> Todo:
        """Mark a todo as completed."""
        todo = self.storage.get(todo_id)
        todo.complete()
        self.storage.update(todo)
        return todo

    def reopen(self, todo_id: str) -> Todo:
        """Reopen a completed todo."""
        todo = self.storage.get(todo_id)
        todo.reopen()
        self.storage.update(todo)
        return todo

    def delete(self, todo_id: str) -> None:
        """Delete a todo."""
        self.storage.delete(todo_id)

    def update(self, todo_id: str, title: Optional[str] = None,
               description: Optional[str] = None,
               priority: Optional[str] = None,
               add_tags: Optional[List[str]] = None,
               remove_tags: Optional[List[str]] = None) -> Todo:
        """Update a todo's properties."""
        todo = self.storage.get(todo_id)

        if title is not None:
            todo.title = title

        if description is not None:
            todo.description = description

        if priority is not None:
            priority_map = {
                "low": Priority.LOW,
                "medium": Priority.MEDIUM,
                "high": Priority.HIGH
            }
            if priority not in priority_map:
                raise ValueError(f"Invalid priority: {priority}")
            todo.priority = priority_map[priority]

        if add_tags:
            for tag in add_tags:
                todo.add_tag(tag)

        if remove_tags:
            for tag in remove_tags:
                todo.remove_tag(tag)

        # Validate the updated todo
        todo.__post_init__()

        self.storage.update(todo)
        return todo

    def clear_completed(self) -> int:
        """Delete all completed todos."""
        completed = self.storage.find_by_status(Status.COMPLETED)
        for todo in completed:
            self.storage.delete(todo.id)
        return len(completed)

    def get_stats(self) -> dict:
        """Get statistics about todos."""
        todos = self.storage.get_all()
        total = len(todos)
        completed = sum(1 for t in todos if t.status == Status.COMPLETED)

        return {
            'total': total,
            'completed': completed,
            'pending': total - completed,
            'completion_rate': (completed / total * 100) if total > 0 else 0,
            'by_priority': {
                'high': sum(1 for t in todos if t.priority == Priority.HIGH),
                'medium': sum(1 for t in todos if t.priority == Priority.MEDIUM),
                'low': sum(1 for t in todos if t.priority == Priority.LOW),
            },
            'tags': list(set(tag for t in todos for tag in t.tags))
        }
