"""Integration tests for CLI commands."""

import tempfile
from pathlib import Path

from that import test, suite, that, tag, integration, mock, replay
from todo_cli.src.commands import TodoCommands
from todo_cli.src.storage import FileStorage, MemoryStorage
from todo_cli.src.models import Todo, Priority, Status


with suite("Add Command"):
    
    @test("adds basic todo")
    @tag("integration", "commands")
    def test_add_basic():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        todo = commands.add("Buy milk")
        
        that(todo.title).equals("Buy milk")
        that(todo.priority).equals(Priority.MEDIUM)
        that(todo.tags).is_empty()
        
        # Verify it's in storage
        stored = storage.get(todo.id)
        that(stored.title).equals("Buy milk")
    
    @test("adds todo with all options")
    @tag("integration", "commands")
    def test_add_with_options():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        todo = commands.add(
            title="Urgent task",
            description="This is very important",
            priority="high",
            tags=["work", "urgent"]
        )
        
        that(todo.title).equals("Urgent task")
        that(todo.description).equals("This is very important")
        that(todo.priority).equals(Priority.HIGH)
        that(todo.tags).contains("work")
        that(todo.tags).contains("urgent")
    
    @test("validates priority values")
    @tag("integration", "commands", "validation")
    def test_add_invalid_priority():
        commands = TodoCommands(MemoryStorage())
        
        that(lambda: commands.add("Task", priority="invalid")).raises(ValueError)


with suite("List Command"):
    
    @test("lists all todos")
    @tag("integration", "commands")
    def test_list_all():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        # Add some todos
        commands.add("Task 1", priority="high")
        commands.add("Task 2", priority="low")
        commands.add("Task 3", tags=["work"])
        
        todos = commands.list_todos()
        
        that(todos).has_length(3)
        that([t.title for t in todos]).contains("Task 1")
        that([t.title for t in todos]).contains("Task 2")
        that([t.title for t in todos]).contains("Task 3")
    
    @test("filters by status")
    @tag("integration", "commands", "filtering")
    def test_list_by_status():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        # Add mixed status todos
        todo1 = commands.add("Pending 1")
        todo2 = commands.add("Pending 2")
        todo3 = commands.add("Completed")
        
        # Complete one
        commands.complete(todo3.id)
        
        # Test filters
        pending = commands.list_todos(status="pending")
        that(pending).has_length(2)
        
        completed = commands.list_todos(status="completed")
        that(completed).has_length(1)
        that(completed[0].title).equals("Completed")
    
    @test("filters by tag")
    @tag("integration", "commands", "filtering")
    def test_list_by_tag():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        commands.add("Work 1", tags=["work", "urgent"])
        commands.add("Work 2", tags=["work"])
        commands.add("Personal", tags=["personal"])
        
        work_todos = commands.list_todos(tag="work")
        that(work_todos).has_length(2)
        
        urgent_todos = commands.list_todos(tag="urgent")
        that(urgent_todos).has_length(1)
    
    @test("searches todos")
    @tag("integration", "commands", "search")
    def test_list_search():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        commands.add("Fix login bug", description="Users can't login")
        commands.add("Add logout feature")
        commands.add("Update documentation", tags=["docs"])
        
        # Search in title
        results = commands.list_todos(search="login")
        that(results).has_length(1)
        that(results[0].title).equals("Fix login bug")
        
        # Search in description
        results = commands.list_todos(search="users")
        that(results).has_length(1)
        
        # Search in tags
        results = commands.list_todos(search="docs")
        that(results).has_length(1)
        that(results[0].title).equals("Update documentation")


with suite("Complete and Reopen Commands"):
    
    @test("completes a todo")
    @tag("integration", "commands")
    @replay.time("2024-01-20T14:30:00Z")
    def test_complete_todo():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        todo = commands.add("Finish project")
        that(todo.status).equals(Status.PENDING)
        
        completed = commands.complete(todo.id)
        
        that(completed.status).equals(Status.COMPLETED)
        that(completed.completed_at).is_not_none()
        
        # Verify in storage
        stored = storage.get(todo.id)
        that(stored.status).equals(Status.COMPLETED)
    
    @test("reopens a todo")
    @tag("integration", "commands")
    def test_reopen_todo():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        todo = commands.add("Completed task")
        commands.complete(todo.id)
        
        reopened = commands.reopen(todo.id)
        
        that(reopened.status).equals(Status.PENDING)
        that(reopened.completed_at).is_none()
    
    @test("handles non-existent todo")
    @tag("integration", "commands", "error-handling")
    def test_complete_nonexistent():
        commands = TodoCommands(MemoryStorage())
        
        that(lambda: commands.complete("fake-id")).raises(Exception)


with suite("Update Command"):
    
    @test("updates todo properties")
    @tag("integration", "commands")
    def test_update_todo():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        todo = commands.add("Original title", description="Original desc")
        
        updated = commands.update(
            todo.id,
            title="New title",
            description="New description",
            priority="high"
        )
        
        that(updated.title).equals("New title")
        that(updated.description).equals("New description")
        that(updated.priority).equals(Priority.HIGH)
    
    @test("adds and removes tags")
    @tag("integration", "commands")
    def test_update_tags():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        todo = commands.add("Task", tags=["old", "remove"])
        
        updated = commands.update(
            todo.id,
            add_tags=["new", "added"],
            remove_tags=["remove"]
        )
        
        that(updated.tags).contains("old")
        that(updated.tags).contains("new")
        that(updated.tags).contains("added")
        that(updated.tags).does_not_contain("remove")
    
    @test("partial updates")
    @tag("integration", "commands")
    def test_partial_update():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        todo = commands.add(
            "Keep title",
            description="Keep description",
            priority="low"
        )
        
        # Only update priority
        updated = commands.update(todo.id, priority="high")
        
        that(updated.title).equals("Keep title")
        that(updated.description).equals("Keep description")
        that(updated.priority).equals(Priority.HIGH)


with suite("Delete and Clear Commands"):
    
    @test("deletes a todo")
    @tag("integration", "commands")
    def test_delete_todo():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        todo1 = commands.add("Keep this")
        todo2 = commands.add("Delete this")
        
        commands.delete(todo2.id)
        
        todos = commands.list_todos()
        that(todos).has_length(1)
        that(todos[0].title).equals("Keep this")
        
        that(lambda: storage.get(todo2.id)).raises(Exception)
    
    @test("clears completed todos")
    @tag("integration", "commands")
    def test_clear_completed():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        # Add mix of todos
        pending1 = commands.add("Pending 1")
        pending2 = commands.add("Pending 2")
        completed1 = commands.add("Completed 1")
        completed2 = commands.add("Completed 2")
        
        # Complete some
        commands.complete(completed1.id)
        commands.complete(completed2.id)
        
        # Clear completed
        count = commands.clear_completed()
        that(count).equals(2)
        
        # Verify only pending remain
        todos = commands.list_todos()
        that(todos).has_length(2)
        that(all(t.status == Status.PENDING for t in todos)).is_true()


with suite("Statistics"):
    
    @test("calculates todo statistics")
    @tag("integration", "commands")
    def test_get_stats():
        storage = MemoryStorage()
        commands = TodoCommands(storage)
        
        # Create diverse todos
        commands.add("High priority", priority="high", tags=["work"])
        commands.add("Medium 1", priority="medium", tags=["work", "urgent"])
        commands.add("Medium 2", priority="medium")
        commands.add("Low priority", priority="low", tags=["personal"])
        
        # Complete one
        todo = commands.add("Completed", priority="high")
        commands.complete(todo.id)
        
        stats = commands.get_stats()
        
        that(stats['total']).equals(5)
        that(stats['completed']).equals(1)
        that(stats['pending']).equals(4)
        that(stats['completion_rate']).equals(20.0)
        
        that(stats['by_priority']['high']).equals(2)
        that(stats['by_priority']['medium']).equals(2)
        that(stats['by_priority']['low']).equals(1)
        
        that(stats['tags']).contains("work")
        that(stats['tags']).contains("urgent")
        that(stats['tags']).contains("personal")
        that(stats['tags']).has_length(3)


with suite("File Storage Integration"):
    
    @test("persists todos to file")
    @tag("integration", "file-storage")
    def test_file_persistence():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            # First session - add todos
            storage1 = FileStorage(tmp.name)
            commands1 = TodoCommands(storage1)
            
            todo1 = commands1.add("Persistent todo 1")
            todo2 = commands1.add("Persistent todo 2", tags=["important"])
            commands1.complete(todo2.id)
            
            # Second session - read todos
            storage2 = FileStorage(tmp.name)
            commands2 = TodoCommands(storage2)
            
            todos = commands2.list_todos()
            that(todos).has_length(2)
            
            # Verify data integrity
            pending = commands2.list_todos(status="pending")
            that(pending).has_length(1)
            that(pending[0].title).equals("Persistent todo 1")
            
            completed = commands2.list_todos(status="completed")
            that(completed).has_length(1)
            that(completed[0].title).equals("Persistent todo 2")
            that(completed[0].tags).contains("important")
            
            # Cleanup
            Path(tmp.name).unlink()
    
    @test("handles concurrent modifications safely")
    @tag("integration", "file-storage", "concurrency")
    def test_concurrent_modifications():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            # Two command instances with same file
            commands1 = TodoCommands(FileStorage(tmp.name))
            commands2 = TodoCommands(FileStorage(tmp.name))
            
            # Both add todos
            todo1 = commands1.add("From session 1")
            todo2 = commands2.add("From session 2")
            
            # Both should see all todos (after reload)
            todos1 = commands1.list_todos()
            todos2 = commands2.list_todos()
            
            that(todos1).has_length(2)
            that(todos2).has_length(2)
            
            # Cleanup
            Path(tmp.name).unlink()