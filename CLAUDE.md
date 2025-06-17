# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running Tests
```bash
# Run all tests
uv run that

# Run specific test file
uv run that tests/test_example.py

# Run tests in verbose mode (includes stack traces)
uv run that -v

# Run specific suite
uv run that -s "Suite Name"

# Run tests matching pattern
uv run that -p "pattern"

# Disable colored output
uv run that --no-color
```

### Development Setup
```bash
# Install dependencies
uv sync

# Run linters (when implementing)
uv run black src/
uv run ruff check src/
```

## Architecture Overview

### Core Modules

1. **`__main__.py`** - CLI entry point
   - Handles command-line arguments and test discovery
   - Dynamically loads test files from the configured directory
   - Uses `TestRunner` and `TestFormatter` for execution and output

2. **`assertions.py`** - Fluent assertion API
   - `that()` function creates `ThatAssertion` instances
   - Custom `AssertionError` includes expected/actual values
   - All assertions return self for method chaining

3. **`runner.py`** - Test execution engine
   - `@test` decorator registers test functions
   - `suite()` context manager groups related tests
   - `TestRegistry` maintains global test/suite registration
   - `TestRunner` executes tests with setup/teardown lifecycle

4. **`output.py`** - Result formatting
   - `TestFormatter` handles colored terminal output
   - Shows test descriptions, pass/fail status, and timing
   - Displays assertion failures with expected/actual values

### Key Design Patterns

- **Global Registry**: Tests are registered in a global `TestRegistry` when files are imported
- **Fluent Interface**: Assertion API uses method chaining for readability
- **Context Managers**: Suites use context managers to group tests and manage lifecycle
- **Dynamic Loading**: Test files are discovered and imported at runtime
- **Decorator Pattern**: `@test` decorator captures test metadata without modifying function

### Test Lifecycle

1. CLI discovers test files matching pattern (default: `test_*.py`)
2. Test files are imported, triggering `@test` decorators
3. Decorators register tests in the global registry
4. Runner executes tests, handling setup/teardown if defined
5. Results are formatted and displayed with pass/fail status

### Configuration

Tests can be configured via `pyproject.toml`:
```toml
[tool.that]
test_dir = "tests"        # Directory to search for tests
pattern = "test_*.py"     # Pattern for test files
verbose = false           # Verbose output by default
color = true              # Colored output (auto-detected)
```