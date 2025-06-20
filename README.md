# Test That - A Python Testing Library

*Because test output should tell you what failed, not make you guess.*

## Installation

This package is available on GitHub only (not published to PyPI):

```bash
# Install from GitHub
pip install git+ssh://git@github.com/dawsons-creek/test-that.git

# Or with uv
uv add git+ssh://git@github.com/dawsons-creek/test-that.git

# For development
git clone git@github.com:dawsons-creek/test-that.git
cd test-that
uv sync
```

## Quick Start

```python
from test_that import test, suite, that

@test("user age is correct")
def test_user_age():
    user = {"name": "John", "age": 30}
    that(user["age"]).equals(30)
```

When this fails, you see:
```
✗ user age is correct

  that(user["age"]).equals(30)
  
  Expected: 30
  Actual:   None
```

## Running Tests

Multiple CLI commands are available for convenience:

```bash
# Run all tests (any of these work)
test_that
that  
tt

# Run specific test file
tt tests/test_user.py

# Run specific suite
tt -s "User Management"

# Verbose mode (includes stack traces)
tt -v

# Disable colors
tt --no-color
```

## Core Features

### Simple Test Definition

```python
from test_that import test, that

@test("basic math works")
def test_math():
    that(2 + 2).equals(4)
```

### Test Suites

```python
from test_that import suite, test, that

with suite("String Operations"):
    @test("uppercase conversion")
    def test_upper():
        that("hello".upper()).equals("HELLO")
    
    @test("string contains substring")
    def test_contains():
        that("hello world").contains("world")
```

### Setup and Teardown

```python
with suite("Database Tests"):
    def setup():
        """Return value is passed to tests"""
        return create_test_db()
    
    def teardown(db):
        """Receives setup's return value"""
        db.close()
    
    @test("can insert user")
    def test_insert(db=setup):
        user = db.insert_user("john@example.com")
        that(user.id).equals(1)
```

## Assertion API

### Equality
```python
that(value).equals(expected)
that(value).does_not_equal(expected)
```

### Truthiness
```python
that(value).is_true()
that(value).is_false()
that(value).is_none()
that(value).is_not_none()
```

### Collections
```python
that(collection).contains(item)
that(collection).does_not_contain(item)
that(collection).is_empty()
that(collection).has_length(n)
```

### Strings
```python
that(string).matches(regex_pattern)
that(string).starts_with(prefix)
that(string).ends_with(suffix)
```

### Numbers
```python
that(number).is_greater_than(n)
that(number).is_less_than(n)
that(number).is_between(min, max)
```

### Types
```python
that(value).is_instance_of(Type)
that(value).has_type(Type)
```

### Exceptions
```python
that(callable).raises(ExceptionType)
that(callable).does_not_raise()
```

## Configuration

Optional `pyproject.toml` configuration:

```toml
[tool.that]
test_dir = "tests"        # Directory to search for tests
pattern = "test_*.py"     # Pattern for test files
verbose = false           # Verbose output by default
color = true              # Colored output (auto-detected)
```

## Development

This project uses [uv](https://github.com/astral-sh/uv) for dependency management.

```bash
# Install dependencies
uv sync

# Run tests
uv run that

# Run tests with verbose output
uv run that -v

# Run specific test file
uv run that tests/test_example.py
```

## Design Principles

1. **One import**: `from test_that import test, suite, that`
2. **One way to do things**: No alternative APIs
3. **Clear over clever**: Readable code over magic
4. **Fast feedback**: Show what failed immediately
5. **No configuration required**: Just works

## License

MIT License - see LICENSE file for details.
