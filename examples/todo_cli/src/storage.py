"""Storage backends for todo items."""

import json
import os
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Dict

from .models import Todo, Status, Priority


class StorageError(Exception):
    """Base exception for storage operations."""
    pass


class TodoNotFoundError(StorageError):
    """Raised when a todo is not found."""
    pass


class StorageBackend(ABC):
    """Abstract base class for todo storage."""
    
    @abstractmethod
    def save(self, todo: Todo) -> None:
        """Save a todo item."""
        pass
    
    @abstractmethod
    def get(self, todo_id: str) -> Todo:
        """Get a todo by ID."""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Todo]:
        """Get all todos."""
        pass
    
    @abstractmethod
    def update(self, todo: Todo) -> None:
        """Update an existing todo."""
        pass
    
    @abstractmethod
    def delete(self, todo_id: str) -> None:
        """Delete a todo by ID."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all todos."""
        pass
    
    def find_by_status(self, status: Status) -> List[Todo]:
        """Find todos by status."""
        return [t for t in self.get_all() if t.status == status]
    
    def find_by_tag(self, tag: str) -> List[Todo]:
        """Find todos by tag."""
        return [t for t in self.get_all() if t.has_tag(tag)]
    
    def search(self, query: str) -> List[Todo]:
        """Search todos by query."""
        return [t for t in self.get_all() if t.matches_search(query)]


class MemoryStorage(StorageBackend):
    """In-memory storage for todos."""
    
    def __init__(self):
        self._todos: Dict[str, Todo] = {}
    
    def save(self, todo: Todo) -> None:
        """Save a todo to memory."""
        if todo.id in self._todos:
            raise StorageError(f"Todo with ID {todo.id} already exists")
        self._todos[todo.id] = todo
    
    def get(self, todo_id: str) -> Todo:
        """Get a todo from memory."""
        if todo_id not in self._todos:
            raise TodoNotFoundError(f"Todo with ID {todo_id} not found")
        return self._todos[todo_id]
    
    def get_all(self) -> List[Todo]:
        """Get all todos from memory."""
        return list(self._todos.values())
    
    def update(self, todo: Todo) -> None:
        """Update a todo in memory."""
        if todo.id not in self._todos:
            raise TodoNotFoundError(f"Todo with ID {todo.id} not found")
        self._todos[todo.id] = todo
    
    def delete(self, todo_id: str) -> None:
        """Delete a todo from memory."""
        if todo_id not in self._todos:
            raise TodoNotFoundError(f"Todo with ID {todo_id} not found")
        del self._todos[todo_id]
    
    def clear(self) -> None:
        """Clear all todos from memory."""
        self._todos.clear()


class FileStorage(StorageBackend):
    """File-based storage for todos using JSON."""
    
    def __init__(self, file_path: str = "todos.json"):
        self.file_path = Path(file_path)
        self._ensure_file_exists()
    
    def _ensure_file_exists(self) -> None:
        """Ensure the storage file exists."""
        if not self.file_path.exists():
            self.file_path.write_text("[]")
    
    def _load_todos(self) -> Dict[str, Todo]:
        """Load todos from file."""
        try:
            data = json.loads(self.file_path.read_text())
            return {
                item['id']: Todo.from_dict(item) 
                for item in data
            }
        except (json.JSONDecodeError, KeyError) as e:
            raise StorageError(f"Failed to load todos: {e}")
    
    def _save_todos(self, todos: Dict[str, Todo]) -> None:
        """Save todos to file."""
        try:
            data = [todo.to_dict() for todo in todos.values()]
            self.file_path.write_text(json.dumps(data, indent=2))
        except (TypeError, IOError) as e:
            raise StorageError(f"Failed to save todos: {e}")
    
    def save(self, todo: Todo) -> None:
        """Save a todo to file."""
        todos = self._load_todos()
        if todo.id in todos:
            raise StorageError(f"Todo with ID {todo.id} already exists")
        todos[todo.id] = todo
        self._save_todos(todos)
    
    def get(self, todo_id: str) -> Todo:
        """Get a todo from file."""
        todos = self._load_todos()
        if todo_id not in todos:
            raise TodoNotFoundError(f"Todo with ID {todo_id} not found")
        return todos[todo_id]
    
    def get_all(self) -> List[Todo]:
        """Get all todos from file."""
        return list(self._load_todos().values())
    
    def update(self, todo: Todo) -> None:
        """Update a todo in file."""
        todos = self._load_todos()
        if todo.id not in todos:
            raise TodoNotFoundError(f"Todo with ID {todo.id} not found")
        todos[todo.id] = todo
        self._save_todos(todos)
    
    def delete(self, todo_id: str) -> None:
        """Delete a todo from file."""
        todos = self._load_todos()
        if todo_id not in todos:
            raise TodoNotFoundError(f"Todo with ID {todo_id} not found")
        del todos[todo_id]
        self._save_todos(todos)
    
    def clear(self) -> None:
        """Clear all todos from file."""
        self._save_todos({})