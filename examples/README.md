# That Framework Examples

This directory contains example applications demonstrating how to use the That testing framework in real-world scenarios.

## Available Examples

### [Todo CLI](./todo_cli/)

A full-featured command-line todo application with comprehensive test coverage.

**Demonstrates:**
- Unit testing with That's fluent assertion API
- Integration testing of CLI commands
- Test organization with suites and directories
- Fixtures using `@provide` decorator
- Mocking for file I/O operations
- Time control with `@replay.time()`
- Separation of unit and integration tests

**Key Features:**
- Todo model with validation
- Multiple storage backends (memory and file-based)
- Rich CLI with add, list, complete, update commands
- 50+ tests covering edge cases and error handling

## Running Examples

Each example includes its own test suite. To run tests:

```bash
# Run all tests for an example
uv run that examples/todo_cli/tests

# Run only unit tests
uv run that examples/todo_cli/tests/unit

# Run specific test file
uv run that examples/todo_cli/tests/unit/test_models.py
```

## Contributing Examples

When adding new examples:

1. Create a new directory under `examples/`
2. Include a clear README.md explaining:
   - What the example demonstrates
   - How to run it
   - Key patterns and techniques used
3. Organize tests into `unit/` and `integration/` subdirectories
4. Organize tests by directory structure (unit/, integration/, etc.)
5. Include both positive and negative test cases

Examples should showcase That's features while remaining realistic and educational.