# That - A Python Testing Library

*Because test output should tell you what failed, not make you guess.*

## Installation

```bash
pip install that
```

## Quick Start

```python
from that import test, suite, that

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

```bash
# Run all tests
that

# Run specific test file
that tests/test_user.py

# Run specific suite
that -s "User Management"

# Verbose mode (includes stack traces)
that -v

# Disable colors
that --no-color
```

## Core Features

### Simple Test Definition

```python
from that import test, that

@test("basic math works")
def test_math():
    that(2 + 2).equals(4)
```

### Test Suites

```python
from that import suite, test, that

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

1. **One import**: `from that import test, suite, that`
2. **One way to do things**: No alternative APIs
3. **Clear over clever**: Readable code over magic
4. **Fast feedback**: Show what failed immediately
5. **No configuration required**: Just works

## License

MIT License - see LICENSE file for details.
