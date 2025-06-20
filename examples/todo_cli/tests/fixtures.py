"""Shared test fixtures for todo CLI tests."""

import tempfile
from pathlib import Path

from test_that import provide
from todo_cli.src.models import Todo, Priority, Status
from todo_cli.src.storage import MemoryStorage, FileStorage
from todo_cli.src.commands import TodoCommands


@provide
def temp_storage_file():
    """Create a temporary storage file for testing."""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
        yield tmp.name
    # Cleanup after test
    Path(tmp.name).unlink(missing_ok=True)


@provide  
def memory_storage():
    """Provide a fresh memory storage instance."""
    return MemoryStorage()


@provide
def file_storage():
    """Provide a file storage instance with temp file."""
    return FileStorage(temp_storage_file)


@provide
def todo_commands_memory():
    """Provide TodoCommands with memory storage."""
    return TodoCommands(memory_storage)


@provide
def todo_commands_file():
    """Provide TodoCommands with file storage."""
    return TodoCommands(file_storage)


@provide
def sample_todos():
    """Create a set of sample todos for testing."""
    return [
        Todo(
            id="work-1",
            title="Complete quarterly report",
            description="Q4 financial report for stakeholders",
            priority=Priority.HIGH,
            tags=["work", "urgent", "finance"]
        ),
        Todo(
            id="work-2", 
            title="Review pull requests",
            description="Review team's PRs from this week",
            priority=Priority.MEDIUM,
            tags=["work", "code-review"]
        ),
        Todo(
            id="personal-1",
            title="Buy groceries",
            description="Milk, bread, eggs, vegetables",
            priority=Priority.MEDIUM,
            tags=["personal", "shopping"]
        ),
        Todo(
            id="personal-2",
            title="Exercise",
            description="30 min cardio + weights",
            priority=Priority.LOW,
            tags=["personal", "health"],
            status=Status.COMPLETED
        ),
        Todo(
            id="learning-1",
            title="Learn Rust",
            description="Complete Rust book chapters 1-5",
            priority=Priority.LOW,
            tags=["learning", "programming"]
        )
    ]


@provide
def populated_storage():
    """Provide a storage backend populated with sample todos."""
    storage = MemoryStorage()
    for todo in sample_todos:
        storage.save(todo)
    return storage


@provide
def cli_runner():
    """Helper to run CLI commands and capture output."""
    import subprocess
    import sys
    
    def run_command(args, storage_file=None):
        """Run todo CLI command and return output."""
        cmd = [sys.executable, "-m", "todo_cli.src.cli"]
        
        if storage_file:
            cmd.extend(["--storage-file", storage_file])
        
        cmd.extend(args)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )
        
        return {
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    
    return run_command