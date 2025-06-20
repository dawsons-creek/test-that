# That - Python Testing Framework

A Python testing framework focused on clarity and simplicity.

## Overview

That provides:
- Fluent assertions that read like English
- Clear error messages showing exactly what failed
- Built-in mocking, time control, and HTTP recording
- Zero configuration - works out of the box

## Quick Start

### Install

```bash
pip install test-that
```

### Write a test

```python
from that import test, that

@test("math works correctly")
def test_addition():
    result = 2 + 2
    that(result).equals(4)
```

### Run tests

```bash
that
```

Output:
```
  ✓ math works correctly
────────────────────────────────────────
Ran 1 test in 12μs
1 passed
```

## Core Features

### Test Organization

```python
from that import test, suite, that

# Simple test
@test("validates email format")
def test_email():
    that("user@example.com").matches(r".+@.+\..+")

# Grouped tests
with suite("User Management"):
    
    @test("creates user with valid data")
    def test_create_user():
        user = create_user("john@example.com")
        that(user).has_key("id")
        that(user["email"]).equals("john@example.com")
    
    @test("rejects invalid email")
    def test_invalid_email():
        that(lambda: create_user("invalid")).raises(ValueError)
```

### Test Fixtures

```python
from that import test, suite, that, provide

with suite("Database Tests"):
    
    @provide
    def temp_db():
        """Create a fresh database for each test."""
        return create_temp_database()
    
    @test("saves user to database")
    def test_save_user():
        # temp_db is automatically available
        user = User(name="Alice")
        temp_db.save(user)
        
        that(temp_db.count()).equals(1)
```

### Mocking

```python
from that import test, that, mock

@test("sends welcome email")
def test_welcome():
    email_service = EmailService()
    user_service = UserService(email_service)
    
    # Mock the email service
    email_mock = mock(email_service, 'send_email', return_value=True)
    
    # Test the behavior
    user_service.welcome_user("alice@example.com")
    
    # Verify the mock was called
    email_mock.assert_called_once()
    that(email_mock.last_call.args[0]).equals("alice@example.com")
```

### Time Control

```python
from that import test, that, replay
import datetime

@test("user has correct creation timestamp")
@replay.time("2024-01-01T12:00:00Z")
def test_user_timestamp():
    user = create_user("alice@example.com")
    
    expected = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    that(user.created_at).equals(expected)
```

### HTTP Recording

```python
from that import test, that, replay
import requests

@test("fetches user from API")
@replay.http("user_api")
def test_api_call():
    # First run: makes real HTTP call and records response
    # Later runs: replays recorded response (fast & deterministic)
    response = requests.get("https://api.example.com/users/123")
    
    that(response.status_code).equals(200)
    that(response.json()).has_key("name")
```

## Assertions Reference

### Equality
- `equals(value)` - Value equals expected
- `does_not_equal(value)` - Value does not equal expected

### Boolean
- `is_true()` - Value is True
- `is_false()` - Value is False
- `is_none()` - Value is None
- `is_not_none()` - Value is not None

### Strings
- `contains(substring)` - String contains substring
- `starts_with(prefix)` - String starts with prefix
- `ends_with(suffix)` - String ends with suffix
- `matches(pattern)` - String matches regex pattern

### Collections
- `is_empty()` - Collection is empty
- `has_length(n)` - Collection has length n
- `contains(item)` - Collection contains item
- `all_satisfy(predicate)` - All items satisfy predicate

### Numbers
- `is_greater_than(value)` - Number is greater than value
- `is_less_than(value)` - Number is less than value
- `is_between(min, max)` - Number is between min and max
- `approximately_equals(value, tolerance)` - Number equals value within tolerance

### Types
- `is_instance_of(type)` - Value is instance of type
- `has_type(type)` - Value has exact type

### Exceptions
- `raises(exception_type)` - Function raises exception
- `does_not_raise()` - Function does not raise exception

## Running Tests

```bash
# Run all tests
that

# Run specific file
that test_user.py

# Run specific directory
that tests/unit/

# Verbose output
that -v

# Run specific suite
that -s "User Management"

# Pattern matching
that -k "email"
```

## Configuration

Optional `pyproject.toml` configuration:

```toml
[tool.that]
test_dir = "tests"
pattern = "test_*.py"
verbose = false
color = true
```

## Documentation

Full documentation available at: [https://that-framework.readthedocs.io](https://that-framework.readthedocs.io)

---

## Development

This section is for contributors to the That framework.

### Prerequisites

- Python 3.8+
- [uv](https://github.com/astral-sh/uv) for dependency management

### Setup

```bash
# Clone the repository
git clone https://github.com/dawsons-creek-software/that.git
cd that

# Install dependencies
uv sync

# Install in development mode
uv pip install -e .
```

### Running Tests

```bash
# Run all tests
uv run that

# Run with verbose output
uv run that -v

# Run specific test file
uv run that tests/test_example.py

# Run only unit tests
uv run that tests/unit/

# Run only integration tests
uv run that tests/integration/
```

### Code Quality

```bash
# Run linter
uv run ruff check src/

# Auto-fix linting issues
uv run ruff check src/ --fix

# Format code
uv run black src/
```

### Building Documentation

```bash
# Install documentation dependencies
uv sync --extra docs

# Serve documentation locally
uv run mkdocs serve

# Build static documentation
uv run mkdocs build

# Deploy to GitHub Pages
uv run mkdocs gh-deploy
```

### Project Structure

```
that/
├── src/that/           # Main package
│   ├── assertions.py   # Assertion API
│   ├── runner.py       # Test execution
│   ├── mocking.py      # Mock system
│   ├── features/       # Advanced features
│   └── ...
├── tests/              # Framework tests
├── examples/           # Example applications
├── docs/               # Documentation
└── pyproject.toml      # Project configuration
```

### Contributing

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/new-assertion`
3. **Make** your changes with tests
4. **Run** the test suite: `uv run that`
5. **Run** linting: `uv run ruff check src/`
6. **Submit** a pull request

### Guidelines

- **Write tests** for all new features
- **Keep tests fast** - unit tests should run in microseconds
- **Use clear assertions** - prefer multiple simple assertions over complex ones
- **Follow the API patterns** - maintain consistency with existing code
- **Document new features** - update both code docs and user documentation

### Development Commands

```bash
# Full development cycle
uv run ruff check src/ --fix  # Lint and fix
uv run that                   # Run tests
uv run mkdocs serve          # Preview docs

# Before committing
uv run that tests/           # Full test suite
uv run ruff check src/       # Final lint check
```

### Release Process

1. Update version in `pyproject.toml`
2. Update `CHANGELOG.md`
3. Run full test suite: `uv run that`
4. Create git tag: `git tag v1.0.0`
5. Push tag: `git push origin v1.0.0`
6. GitHub Actions will automatically build and publish to PyPI

### Architecture Notes

- **No external dependencies** for core functionality
- **Minimal API surface** - prefer composition over configuration
- **Fast execution** - optimized for quick feedback loops
- **Clear error messages** - every assertion failure should be immediately understandable

## License

MIT License - see [LICENSE](LICENSE) file for details.