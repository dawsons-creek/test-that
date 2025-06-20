"""Unit tests for Todo model."""

from datetime import datetime

from that import test, suite, that, replay
from todo_cli.src.models import Todo, Priority, Status


with suite("Todo Model Creation"):
    
    @test("creates todo with required fields")
    def test_create_minimal_todo():
        todo = Todo(title="Buy groceries")
        
        that(todo.title).equals("Buy groceries")
        that(todo.description).equals("")
        that(todo.priority).equals(Priority.MEDIUM)
        that(todo.status).equals(Status.PENDING)
        that(todo.tags).is_empty()
        that(todo.id).is_not_none()
        that(todo.created_at).is_instance_of(datetime)
        that(todo.completed_at).is_none()
    
    @test("creates todo with all fields")
    def test_create_full_todo():
        todo = Todo(
            title="Complete project",
            description="Finish the Q4 project deliverables",
            priority=Priority.HIGH,
            tags=["work", "urgent", "Q4"]
        )
        
        that(todo.title).equals("Complete project")
        that(todo.description).equals("Finish the Q4 project deliverables")
        that(todo.priority).equals(Priority.HIGH)
        that(todo.tags).contains("work")
        that(todo.tags).has_length(3)
    
    @test("validates empty title")
    def test_empty_title_validation():
        that(lambda: Todo(title="")).raises(ValueError)
        that(lambda: Todo(title="   ")).raises(ValueError)
    
    @test("validates title length")
    def test_title_length_validation():
        long_title = "x" * 201
        that(lambda: Todo(title=long_title)).raises(ValueError)
    
    @test("normalizes tags to lowercase and unique")
    def test_tag_normalization():
        todo = Todo(
            title="Test todo",
            tags=["Python", "PYTHON", "python", " Django ", "django"]
        )
        
        that(todo.tags).has_length(2)
        that(todo.tags).contains("python")
        that(todo.tags).contains("django")
        that(todo.tags).does_not_contain("Python")
        that(todo.tags).does_not_contain("PYTHON")


with suite("Todo Status Management"):
    
    @test("completes a pending todo")
    def test_complete_todo():
        todo = Todo(title="Write tests")
        that(todo.status).equals(Status.PENDING)
        that(todo.completed_at).is_none()
        
        todo.complete()
        
        that(todo.status).equals(Status.COMPLETED)
        that(todo.completed_at).is_not_none()
    
    @test("cannot complete already completed todo")
    def test_complete_already_completed():
        todo = Todo(title="Done task", status=Status.COMPLETED)
        
        that(lambda: todo.complete()).raises(ValueError)
    
    @test("reopens a completed todo")
    def test_reopen_todo():
        todo = Todo(title="Finished task", status=Status.COMPLETED)
        todo.completed_at = datetime.now()
        
        todo.reopen()
        
        that(todo.status).equals(Status.PENDING)
        that(todo.completed_at).is_none()
    
    @test("cannot reopen pending todo")
    def test_reopen_already_pending():
        todo = Todo(title="Pending task")
        
        that(lambda: todo.reopen()).raises(ValueError)


with suite("Todo Tag Management"):
    
    @test("adds tags to todo")
    def test_add_tags():
        todo = Todo(title="Learn Python")
        
        todo.add_tag("programming")
        that(todo.tags).contains("programming")
        
        todo.add_tag("EDUCATION")
        that(todo.tags).contains("education")
        that(todo.tags).has_length(2)
    
    @test("prevents duplicate tags")
    def test_no_duplicate_tags():
        todo = Todo(title="Study", tags=["learning"])
        
        todo.add_tag("learning")
        todo.add_tag("LEARNING")
        
        that(todo.tags).has_length(1)
    
    @test("validates empty tag")
    def test_empty_tag_validation():
        todo = Todo(title="Test")
        
        that(lambda: todo.add_tag("")).raises(ValueError)
        that(lambda: todo.add_tag("   ")).raises(ValueError)
    
    @test("removes tags from todo")
    def test_remove_tags():
        todo = Todo(title="Project", tags=["work", "urgent", "client"])
        
        todo.remove_tag("urgent")
        that(todo.tags).does_not_contain("urgent")
        that(todo.tags).has_length(2)
        
        # Removing non-existent tag is safe
        todo.remove_tag("nonexistent")
        that(todo.tags).has_length(2)
    
    @test("checks if todo has tag")
    def test_has_tag():
        todo = Todo(title="Task", tags=["python", "testing"])
        
        that(todo.has_tag("python")).is_true()
        that(todo.has_tag("PYTHON")).is_true()  # Case insensitive
        that(todo.has_tag("java")).is_false()


with suite("Todo Search and Serialization"):
    
    @test("matches search in title")
    def test_search_title():
        todo = Todo(title="Fix bug in authentication module")
        
        that(todo.matches_search("bug")).is_true()
        that(todo.matches_search("AUTH")).is_true()  # Case insensitive
        that(todo.matches_search("login")).is_false()
    
    @test("matches search in description")
    def test_search_description():
        todo = Todo(
            title="Update docs",
            description="Add examples for the new API endpoints"
        )
        
        that(todo.matches_search("api")).is_true()
        that(todo.matches_search("EXAMPLES")).is_true()
        that(todo.matches_search("bug")).is_false()
    
    @test("matches search in tags")
    def test_search_tags():
        todo = Todo(title="Task", tags=["backend", "database"])
        
        that(todo.matches_search("backend")).is_true()
        that(todo.matches_search("data")).is_true()  # Partial match
        that(todo.matches_search("frontend")).is_false()
    
    @test("serializes todo to dict")
    def test_todo_to_dict():
        todo = Todo(
            id="test-123",
            title="Test todo",
            description="A test",
            priority=Priority.HIGH,
            tags=["test", "example"]
        )
        
        data = todo.to_dict()
        
        that(data['id']).equals("test-123")
        that(data['title']).equals("Test todo")
        that(data['description']).equals("A test")
        that(data['priority']).equals("high")
        that(data['status']).equals("pending")
        that(data['tags']).has_length(2)
        that(data['tags']).contains("test")
        that(data['tags']).contains("example")
        # Just check it's an ISO timestamp string
        that(data['created_at']).is_instance_of(str)
        that(len(data['created_at'])).is_greater_than(10)
        that(data['completed_at']).is_none()
    
    @test("deserializes todo from dict")
    def test_todo_from_dict():
        data = {
            'id': 'test-456',
            'title': 'Restored todo',
            'description': 'From storage',
            'priority': 'low',
            'status': 'completed',
            'tags': ['restored'],
            'created_at': '2024-01-15T09:00:00',
            'completed_at': '2024-01-15T10:00:00'
        }
        
        todo = Todo.from_dict(data)
        
        that(todo.id).equals("test-456")
        that(todo.title).equals("Restored todo")
        that(todo.priority).equals(Priority.LOW)
        that(todo.status).equals(Status.COMPLETED)
        that(todo.tags).equals(['restored'])
        that(todo.created_at).equals(datetime(2024, 1, 15, 9, 0, 0))
        that(todo.completed_at).equals(datetime(2024, 1, 15, 10, 0, 0))