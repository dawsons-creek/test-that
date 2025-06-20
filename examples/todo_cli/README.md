# Todo CLI Example

A comprehensive example demonstrating the That testing framework through a full-featured todo command-line application.

## Overview

This example showcases:
- **Unit testing** with That's assertion API
- **Integration testing** of CLI commands
- **Test organization** with suites and directories
- **Fixtures** using the `@provide` decorator
- **Mocking** for file I/O operations
- **Time control** with `replay.time()`
- **Realistic test scenarios** for a production-like application

## Project Structure

```
todo_cli/
├── src/
│   ├── __init__.py
│   ├── models.py        # Todo data model with validation
│   ├── storage.py       # Storage backends (memory & file)
│   ├── commands.py      # Business logic layer
│   ├── formatters.py    # Output formatting
│   └── cli.py          # Command-line interface
└── tests/
    ├── fixtures.py      # Shared test fixtures
    ├── unit/
    │   ├── test_models.py    # Model validation tests
    │   └── test_storage.py   # Storage backend tests
    └── integration/
        ├── test_cli_commands.py   # Command logic tests
        └── test_cli_interface.py  # CLI argument tests
```

## Running the Tests

From the project root:

```bash
# Run all tests
uv run tt examples/todo_cli/tests

# Run only unit tests
uv run tt examples/todo_cli/tests/unit

# Run only integration tests
uv run tt examples/todo_cli/tests/integration

# Run tests for a specific module
uv run tt examples/todo_cli/tests/unit/test_models.py

# Run tests in verbose mode
uv run tt examples/todo_cli/tests -v
```

## Key Testing Patterns Demonstrated

### 1. Model Testing with Validation

```python
@test("validates empty title")
def test_empty_title_validation():
    that(lambda: Todo(title="")).raises(ValueError)
```

### 2. Storage Testing with Multiple Backends

```python
@provide
def storage_backends():
    """Test both memory and file storage."""
    return [
        ("memory", MemoryStorage()),
        ("file", FileStorage("test.json"))
    ]

@test("finds todos by status")
def test_find_by_status():
    for name, storage in storage_backends:
        # Test each backend...
```

### 3. Time-Based Testing

```python
@test("completes todo with timestamp")
@replay.time("2024-01-15T10:00:00Z")
def test_complete_todo():
    todo = Todo(title="Task")
    todo.complete()
    that(todo.completed_at).equals(datetime(2024, 1, 15, 10, 0, 0))
```

### 4. Integration Testing with Real Files

```python
@test("persists todos across sessions")
def test_file_persistence():
    with tempfile.NamedTemporaryFile() as tmp:
        # First session
        commands1 = TodoCommands(FileStorage(tmp.name))
        commands1.add("Persistent todo")
        
        # Second session
        commands2 = TodoCommands(FileStorage(tmp.name))
        todos = commands2.list_todos()
        that(todos).has_length(1)
```

### 5. CLI Testing with Subprocess

```python
@test("adds todo via CLI")
def test_cli_add():
    result = run_cli(["add", "Buy milk", "-p", "high"])
    that(result.returncode).equals(0)
    that(result.stdout).contains("Todo added")
```

## Test Organization

### Directory Structure

Tests are organized by type and purpose:
- `unit/` - Fast, isolated unit tests
- `integration/` - Tests involving multiple components

### Test Suites

Tests are organized into logical suites:
- **Todo Model Creation** - Model instantiation and validation
- **Todo Status Management** - Complete/reopen functionality
- **Todo Tag Management** - Tag operations
- **Storage Tests** - Backend-agnostic storage operations
- **CLI Commands** - Business logic integration
- **CLI Interface** - Command-line argument handling

## Running the Todo CLI

The todo CLI itself can be run with:

```bash
# Add a todo
python -m todo_cli.src.cli add "Buy groceries" -p high -t shopping

# List todos
python -m todo_cli.src.cli list

# Complete a todo (using ID prefix)
python -m todo_cli.src.cli complete abc123

# Show statistics
python -m todo_cli.src.cli stats
```

## Learning Points

1. **Test Isolation**: Each test gets fresh fixtures via `@provide`
2. **Comprehensive Coverage**: Tests cover happy paths, edge cases, and errors
3. **Realistic Scenarios**: Tests mirror actual usage patterns
4. **Clean Test Code**: That's API makes tests readable and maintainable  
5. **Performance**: Unit tests run in microseconds, integration tests in milliseconds
6. **Simple Organization**: Directory structure eliminates need for metadata

This example demonstrates how That can scale from simple unit tests to complex integration testing scenarios while maintaining clarity and performance.