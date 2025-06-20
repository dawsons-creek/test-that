# Quick Start Guide

Master Test That in 5 minutes. This guide covers everything you need to know to start writing effective tests.

## Installation

```bash
pip install test-that
```

That's it! Test That works out of the box with zero configuration.

## Core Concepts

### 1. Tests and Assertions

```python
from that import that, test

@test("user data should be valid")
def test_user_validation():
    user = {"name": "Alice", "age": 28, "email": "alice@example.com"}

    # Fluent, chainable assertions
    that(user["name"]) \
        .is_not_none() \
        .is_instance_of(str) \
        .has_length(5) \
        .equals("Alice")

    that(user["age"]).is_between(18, 65)
    that(user["email"]).matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
```

### 2. Test Suites

Group related tests for better organization:

```python
from that import that, test, suite

with suite("User Management"):

    @test("should create user with valid data")
    def test_create_user():
        user_data = {"name": "John", "email": "john@example.com"}
        user = create_user(user_data)

        that(user) \
            .has_key("id") \
            .has_key("created_at") \
            .has_value("name", "John")

    @test("should validate email format")
    def test_email_validation():
        that(lambda: create_user({"email": "invalid"})) \
            .raises(ValueError, "Invalid email format")
```

### 3. Clear Error Messages

When tests fail, you get crystal clear feedback:

```python
@test("user age should be valid")
def test_user_age():
    user = {"name": "John", "age": 15}  # Too young
    that(user["age"]).is_greater_than(18)
```

**Output when it fails:**
```
✗ user age should be valid

  that(user["age"]).is_greater_than(18)

  Expected: number greater than 18
  Actual:   15

  Value 15 is not greater than 18.
```

## Essential Assertion Patterns

### String Testing

```python
@test("string operations should work")
def test_strings():
    message = "Hello, World!"

    that(message) \
        .contains("World") \
        .starts_with("Hello") \
        .ends_with("!") \
        .has_length(13) \
        .is_not_empty()
```

### Collection Testing

```python
@test("list operations should work")
def test_collections():
    numbers = [1, 2, 3, 4, 5]

    that(numbers) \
        .has_length(5) \
        .contains(3) \
        .does_not_contain(6) \
        .all(lambda x: x > 0) \
        .is_sorted()

    # Dictionary testing
    user = {"name": "Alice", "role": "admin"}
    that(user) \
        .has_key("name") \
        .has_value("role", "admin") \
        .contains_subset({"name": "Alice"})
```

### Exception Testing

```python
@test("should handle errors gracefully")
def test_error_handling():
    def divide_by_zero():
        return 10 / 0

    def validate_age(age):
        if age < 0:
            raise ValueError("Age cannot be negative")
        return age

    # Test that exceptions are raised
    that(divide_by_zero).raises(ZeroDivisionError)
    that(lambda: validate_age(-5)).raises(ValueError, "Age cannot be negative")

    # Test that functions don't raise exceptions
    result = that(lambda: validate_age(25)).does_not_raise()
    that(result.value).equals(25)
```

### Type and Instance Testing

```python
@test("type checking should work")
def test_types():
    data = {"count": 42, "items": ["a", "b", "c"]}

    that(data["count"]) \
        .is_instance_of(int) \
        .has_type(int) \
        .is_greater_than(0)

    that(data["items"]) \
        .is_instance_of(list) \
        .all(lambda item: isinstance(item, str))
```

## Advanced Features

### Clear Test Fixtures with @provide

```python
from that import that, test, suite, provide

class EmailService:
    def send_email(self, to, subject, body):
        # This would normally send a real email
        raise NotImplementedError("Real email sending not implemented")

with suite("User Signup"):
    
    @provide
    def email_service():
        return EmailService()
    
    @provide
    def mock_user_data():
        return {"name": "John", "email": "john@example.com"}

    @test("user signup should work with valid data")
    def test_user_signup():
        # Clear where fixtures come from - provided above with @provide
        user = create_user(mock_user_data, email_service)
        
        that(user["email"]).equals("john@example.com")
        that(user["name"]).equals("John")
```

### Time Control

```python
from that import that, test, replay
import datetime

@test("user creation should have correct timestamp")
@replay.time("2024-01-01T12:00:00Z")
def test_user_timestamp():
    user = create_user("john@example.com")

    # Time is frozen, so timestamp is predictable
    expected_time = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    that(user.created_at).equals(expected_time)
```

### HTTP Recording

```python
from that import that, test, replay
import requests

@test("should fetch user from API")
@replay.http("fetch_user_api")
def test_api_integration():
    # First run: makes real HTTP call and records response
    # Subsequent runs: replays recorded response (fast & deterministic)
    response = requests.get("https://api.example.com/users/123")

    that(response.status_code).equals(200)
    that(response.json()) \
        .has_key("id") \
        .has_key("name") \
        .has_key("email")
```

### Test Tagging

```python
from that import that, test, slow, integration, requires_network

@test("fast unit test")
def test_calculation():
    that(2 + 2).equals(4)

@test("database integration test")
@integration
def test_database():
    # Test database operations
    pass

@test("external API test")
@slow
@requires_network
def test_external_api():
    # Test external service
    pass
```

Run specific test types:
```bash
# Run only fast tests (skip slow ones)
that --exclude-tags slow

# Run only integration tests
that --include-tags integration
```

## Running Tests

### Basic Commands

```bash
# Run all tests
that

# Run specific file
that test_user.py

# Run specific directory
that tests/unit/

# Verbose output (shows stack traces)
that -v

# Disable colors
that --no-color
```

### Filtering Tests

```bash
# Run tests matching pattern
that -k "user"

# Run specific suite
that -s "User Management"

# Run tagged tests
that --include-tags integration
that --exclude-tags slow
```

### Output Options

```bash
# Quiet mode (only show failures)
that -q

# Show test discovery
that --collect-only

# Stop on first failure
that -x
```

## What Makes Test That Special

### 1. **Zero Configuration**
- Works immediately after installation
- No setup files or configuration needed
- Sensible defaults for everything

### 2. **Clear Error Messages**
- Shows exactly what failed and why
- Intelligent diffing for complex data structures
- No cryptic assertion errors

### 3. **Fluent API**
- Natural, readable assertions
- Chainable methods that read like English
- Comprehensive assertion library

### 4. **Built-in Advanced Features**
- Mocking system included
- Time control for deterministic tests
- HTTP recording for API testing
- Test tagging and filtering

### 5. **Developer Experience**
- Fast test execution
- Beautiful, colored output
- Helpful error messages and hints

## Next Steps

Now that you know the basics, dive deeper:

1. **[Master Assertions](../guide/assertions.md)** - Learn all available assertion methods
2. **[Explore Features](../features/fluent-assertions.md)** - Discover advanced capabilities
3. **[See Real Examples](../examples/web-api-testing.md)** - Learn from practical scenarios
4. **[Compare Frameworks](why-test-that.md)** - See how Test That compares to others

## Quick Reference

### Common Assertions
```python
# Equality
that(value).equals(expected)
that(value).does_not_equal(other)

# Types
that(value).is_instance_of(str)
that(value).has_type(int)

# Strings
that(text).contains("substring")
that(text).starts_with("prefix")
that(text).matches(r"pattern")

# Collections
that(list).has_length(5)
that(list).contains(item)
that(dict).has_key("key")

# Numbers
that(number).is_greater_than(10)
that(number).is_between(1, 100)
that(float_val).is_close_to(3.14, tolerance=0.01)

# Booleans
that(value).is_true()
that(value).is_false()
that(value).is_none()

# Exceptions
that(function).raises(ValueError)
that(function).does_not_raise()
```

### Test Organization
```python
# Simple test
@test("description")
def test_function():
    pass

# Test suite
with suite("Suite Name"):
    @test("test in suite")
    def test_in_suite():
        pass

# Tagged test
@test("slow test")
@slow
def test_slow_operation():
    pass
```

### Advanced Features
```python
# Mocking
mock(object, 'method', return_value=result)

# Time control
@replay.time("2024-01-01T12:00:00Z")

# HTTP recording
@replay.http("recording_name")

# Combined
@replay(time="2024-01-01T12:00:00Z", http="api_call")
```

**Ready to write better tests? Start with [your first test](first-test.md)!**
```
```