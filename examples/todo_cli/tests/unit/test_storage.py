"""Unit tests for storage backends."""

import json
import tempfile
from pathlib import Path

from that import test, suite, that, tag, unit, mock, provide
from todo_cli.src.models import Todo, Priority, Status
from todo_cli.src.storage import (
    MemoryStorage, FileStorage, StorageError, 
    TodoNotFoundError, StorageBackend
)


# Shared test fixtures
@provide
def sample_todo():
    """Create a sample todo for testing."""
    return Todo(
        id="test-123",
        title="Test Todo",
        description="A test todo item",
        priority=Priority.HIGH,
        tags=["test", "sample"]
    )


@provide
def completed_todo():
    """Create a completed todo for testing."""
    todo = Todo(
        id="test-456",
        title="Completed Todo",
        status=Status.COMPLETED
    )
    return todo


with suite("MemoryStorage Tests"):
    
    @test("stores and retrieves todo")
    @tag("unit", "storage")
    def test_memory_save_and_get():
        storage = MemoryStorage()
        
        storage.save(sample_todo)
        retrieved = storage.get("test-123")
        
        that(retrieved.title).equals("Test Todo")
        that(retrieved.id).equals("test-123")
        that(retrieved.priority).equals(Priority.HIGH)
    
    @test("prevents duplicate IDs")
    @tag("unit", "storage", "validation")
    def test_memory_duplicate_id():
        storage = MemoryStorage()
        
        storage.save(sample_todo)
        duplicate = Todo(id="test-123", title="Duplicate")
        
        that(lambda: storage.save(duplicate)).raises(StorageError)
    
    @test("raises error for non-existent todo")
    @tag("unit", "storage", "error-handling")
    def test_memory_get_nonexistent():
        storage = MemoryStorage()
        
        that(lambda: storage.get("nonexistent")).raises(TodoNotFoundError)
    
    @test("lists all todos")
    @tag("unit", "storage")
    def test_memory_get_all():
        storage = MemoryStorage()
        
        todo1 = Todo(title="First")
        todo2 = Todo(title="Second")
        todo3 = Todo(title="Third")
        
        storage.save(todo1)
        storage.save(todo2)
        storage.save(todo3)
        
        todos = storage.get_all()
        that(todos).has_length(3)
        that([t.title for t in todos]).contains("First")
        that([t.title for t in todos]).contains("Second")
        that([t.title for t in todos]).contains("Third")
    
    @test("updates existing todo")
    @tag("unit", "storage")
    def test_memory_update():
        storage = MemoryStorage()
        
        storage.save(sample_todo)
        
        # Modify and update
        sample_todo.title = "Updated Title"
        sample_todo.complete()
        storage.update(sample_todo)
        
        retrieved = storage.get("test-123")
        that(retrieved.title).equals("Updated Title")
        that(retrieved.status).equals(Status.COMPLETED)
    
    @test("deletes todo")
    @tag("unit", "storage")
    def test_memory_delete():
        storage = MemoryStorage()
        
        storage.save(sample_todo)
        that(storage.get_all()).has_length(1)
        
        storage.delete("test-123")
        that(storage.get_all()).is_empty()
        that(lambda: storage.get("test-123")).raises(TodoNotFoundError)
    
    @test("clears all todos")
    @tag("unit", "storage")
    def test_memory_clear():
        storage = MemoryStorage()
        
        storage.save(Todo(title="Todo 1"))
        storage.save(Todo(title="Todo 2"))
        storage.save(Todo(title="Todo 3"))
        
        that(storage.get_all()).has_length(3)
        
        storage.clear()
        that(storage.get_all()).is_empty()


with suite("FileStorage Tests"):
    
    @test("creates storage file if not exists")
    @tag("unit", "storage", "file-io")
    def test_file_storage_init():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            tmp_path = tmp.name
        
        # File is deleted after context manager
        Path(tmp_path).unlink()
        that(Path(tmp_path).exists()).is_false()
        
        storage = FileStorage(tmp_path)
        that(Path(tmp_path).exists()).is_true()
        
        # Cleanup
        Path(tmp_path).unlink()
    
    @test("saves todo to file")
    @tag("unit", "storage", "file-io")
    def test_file_save():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            storage = FileStorage(tmp.name)
            
            storage.save(sample_todo)
            
            # Read file directly to verify
            data = json.loads(Path(tmp.name).read_text())
            that(data).has_length(1)
            that(data[0]['id']).equals("test-123")
            that(data[0]['title']).equals("Test Todo")
            
            # Cleanup
            Path(tmp.name).unlink()
    
    @test("loads todos from file")
    @tag("unit", "storage", "file-io")
    def test_file_load():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w') as tmp:
            # Write test data
            test_data = [{
                'id': 'loaded-123',
                'title': 'Loaded Todo',
                'description': 'From file',
                'priority': 'low',
                'status': 'pending',
                'tags': ['loaded'],
                'created_at': '2024-01-15T10:00:00',
                'completed_at': None
            }]
            json.dump(test_data, tmp)
            tmp.flush()
            
            storage = FileStorage(tmp.name)
            todos = storage.get_all()
            
            that(todos).has_length(1)
            that(todos[0].id).equals('loaded-123')
            that(todos[0].title).equals('Loaded Todo')
            
            # Cleanup
            Path(tmp.name).unlink()
    
    @test("handles corrupted file")
    @tag("unit", "storage", "error-handling")
    def test_file_corrupted():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json", mode='w') as tmp:
            tmp.write("{ invalid json ]")
            tmp.flush()
            
            storage = FileStorage(tmp.name)
            that(lambda: storage.get_all()).raises(StorageError)
            
            # Cleanup
            Path(tmp.name).unlink()
    
    @test("persists changes across instances")
    @tag("unit", "storage", "file-io")
    def test_file_persistence():
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            # First instance saves data
            storage1 = FileStorage(tmp.name)
            todo1 = Todo(title="Persistent Todo")
            storage1.save(todo1)
            
            # Second instance reads data
            storage2 = FileStorage(tmp.name)
            todos = storage2.get_all()
            
            that(todos).has_length(1)
            that(todos[0].title).equals("Persistent Todo")
            
            # Cleanup
            Path(tmp.name).unlink()


with suite("StorageBackend Common Features"):
    
    @provide
    def storage_backends():
        """Provide both storage backends for testing common features."""
        with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as tmp:
            return [
                ("memory", MemoryStorage()),
                ("file", FileStorage(tmp.name), tmp.name)
            ]
    
    @test("finds todos by status")
    @tag("unit", "storage", "filtering")
    def test_find_by_status():
        for backend_info in storage_backends:
            name = backend_info[0]
            storage = backend_info[1]
            
            # Add mixed status todos
            pending1 = Todo(title=f"Pending 1 ({name})")
            pending2 = Todo(title=f"Pending 2 ({name})")
            completed = Todo(title=f"Completed ({name})", status=Status.COMPLETED)
            
            storage.save(pending1)
            storage.save(pending2)
            storage.save(completed)
            
            # Test filtering
            pending_todos = storage.find_by_status(Status.PENDING)
            that(pending_todos).has_length(2)
            
            completed_todos = storage.find_by_status(Status.COMPLETED)
            that(completed_todos).has_length(1)
            that(completed_todos[0].title).contains("Completed")
            
            # Cleanup file storage
            if len(backend_info) > 2:
                Path(backend_info[2]).unlink()
    
    @test("finds todos by tag")
    @tag("unit", "storage", "filtering")
    def test_find_by_tag():
        for backend_info in storage_backends:
            name = backend_info[0]
            storage = backend_info[1]
            
            # Add todos with tags
            work1 = Todo(title=f"Work 1 ({name})", tags=["work", "urgent"])
            work2 = Todo(title=f"Work 2 ({name})", tags=["work"])
            personal = Todo(title=f"Personal ({name})", tags=["personal"])
            
            storage.save(work1)
            storage.save(work2)
            storage.save(personal)
            
            # Test filtering
            work_todos = storage.find_by_tag("work")
            that(work_todos).has_length(2)
            
            urgent_todos = storage.find_by_tag("urgent")
            that(urgent_todos).has_length(1)
            that(urgent_todos[0].title).contains("Work 1")
            
            # Cleanup file storage
            if len(backend_info) > 2:
                Path(backend_info[2]).unlink()
    
    @test("searches todos by query")
    @tag("unit", "storage", "search")
    def test_search():
        for backend_info in storage_backends:
            name = backend_info[0]
            storage = backend_info[1]
            
            # Add todos
            bug_todo = Todo(title=f"Fix login bug ({name})", 
                           description="Users cannot login with email")
            feature_todo = Todo(title=f"Add feature ({name})",
                              description="New dashboard",
                              tags=["feature", "ui"])
            
            storage.save(bug_todo)
            storage.save(feature_todo)
            
            # Test search
            bug_results = storage.search("bug")
            that(bug_results).has_length(1)
            that(bug_results[0].title).contains("Fix login bug")
            
            login_results = storage.search("login")
            that(login_results).has_length(1)
            
            ui_results = storage.search("ui")
            that(ui_results).has_length(1)
            that(ui_results[0].title).contains("Add feature")
            
            # Cleanup file storage
            if len(backend_info) > 2:
                Path(backend_info[2]).unlink()