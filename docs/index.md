# That - Python Testing Framework

A Python testing framework focused on clarity and simplicity.

## Overview

That provides:
- Fluent assertions that read like English
- Clear error messages showing exactly what failed
- JSON and dictionary testing with nested path support
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

## Core Concepts

### Tests and Suites

```python
from that import test, suite, that

# Simple test
@test("validates user email")
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

### Fixtures

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

## Features

### Mocking

```python
from that import test, that, mock

@test("sends welcome email")
def test_welcome_email():
    email_service = EmailService()
    user_service = UserService(email_service)
    
    # Mock the email service
    email_mock = mock(email_service, 'send_email', return_value=True)
    
    # Test the behavior
    user_service.create_user("alice@example.com")
    
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

### JSON & Dictionary Testing

```python
from that import test, that

@test("validates API response")
def test_api_response():
    response = '{"user": {"id": 123, "profile": {"name": "Alice"}}}'
    
    # Parse JSON and test nested values
    parsed = that(response).as_json()
    parsed.path("user.id").equals(123)
    parsed.path("user.profile.name").equals("Alice")
    
    # Validate structure with schema
    schema = {
        "type": "object",
        "properties": {
            "user": {
                "type": "object",
                "required": ["id", "profile"]
            }
        }
    }
    parsed.matches_schema(schema)
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

### Combined Features

```python
@test("complete user signup flow")
@replay(time="2024-01-01T12:00:00Z", http="signup_flow")
def test_signup():
    # Both time and HTTP are controlled
    response = signup_user("alice@example.com")
    user = User.from_response(response)
    
    that(user.created_at.year).equals(2024)
    that(response.status_code).equals(201)
```

## All Assertions

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
- `does_not_contain(substring)` - String does not contain substring
- `starts_with(prefix)` - String starts with prefix
- `ends_with(suffix)` - String ends with suffix
- `matches(pattern)` - String matches regex pattern

### Collections
- `is_empty()` - Collection is empty
- `has_length(n)` - Collection has length n
- `contains(item)` - Collection contains item
- `does_not_contain(item)` - Collection does not contain item
- `all_satisfy(predicate)` - All items satisfy predicate
- `are_unique()` - All items are unique
- `are_sorted_by(key_func)` - Items are sorted by key function

### Numbers
- `is_greater_than(value)` - Number is greater than value
- `is_less_than(value)` - Number is less than value
- `is_between(min, max)` - Number is between min and max
- `approximately_equals(value, tolerance)` - Number equals value within tolerance

### Types
- `is_instance_of(type)` - Value is instance of type
- `has_type(type)` - Value has exact type

### Dictionaries
- `has_key(key)` - Dictionary contains key
- `has_keys(*keys)` - Dictionary contains all keys
- `has_value(key, value)` - Dictionary has key with specific value
- `has_path(path)` - Nested path exists (dot notation)
- `path(path)` - Get nested value by path
- `as_json()` - Parse JSON string
- `matches_schema(schema)` - Validate against JSON Schema
- `has_structure(structure)` - Validate dictionary structure

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

## API Reference

### Core Functions
- `test(description)` - Mark function as a test
- `suite(name)` - Group related tests
- `that(value)` - Create assertion on value
- `provide` - Create test fixture
- `mock(obj, attr, **kwargs)` - Mock object attribute
- `replay.time(timestamp)` - Control time
- `replay.http(cassette)` - Record/replay HTTP calls
- `replay(time=..., http=...)` - Combined control