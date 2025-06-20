# That Testing Library - Feature Specification

## Core Features (Built-in)

These features are included in the core library because they directly support the primary goal: **clear test output that shows exactly what went wrong**.

### 1. **Type-Specific Output**
Intelligent diffing that clearly shows what you expected vs what you got, formatted appropriately for each type.

**Dictionary/Object Differences:**
```python
that(user).equals(expected_user)

# Output when it fails:
✗ user data matches expected

that(user).equals(expected_user)

User object differences:
✓ email: "john@example.com"
✓ name: "John Doe"
✗ age: expected 30, got 28
✗ verified: expected True, got False
+ unexpected_field: "value" (not in expected)
- missing_field (expected but not found)
```

**List/Array Differences:**
```python
that(processed_items).equals(expected_items)

# Output when it fails:
✗ processed items match expected

that(processed_items).equals(expected_items)

List differences:
Length: expected 3 items, got 4

[0] ✓ "apple"
[1] ✗ expected "orange", got "banana"
[2] ✓ "grape"
[3] + "melon" (unexpected)
```

**String Differences:**
```python
that(message).equals(expected_message)

# Output when it fails:
✗ message matches expected

that(message).equals(expected_message)

Expected: "Hello, John! Welcome to our service."
Got:      "Hello, Jane! Welcome to our service."
--------^

First difference at position 7: expected 'John' but got 'Jane'
```

**Number Differences:**
```python
that(total).equals(99.99)

# Output when it fails:
✗ total equals expected

that(total).equals(99.99)

Expected: 99.99
Got: 89.99
Difference: -10.00
```

**Complex Nested Structure:**
```python
that(api_response).equals(expected_response)

# Output when it fails:
✗ API response matches expected

that(api_response).equals(expected_response)

Dictionary differences:
✓ status: "success"
✗ data.user.name: expected "John Doe", got "Jane Doe"
✗ data.user.roles: expected ["user", "admin"], got ["user"]
✗ data.timestamp: expected "2024-01-01T12:00:00Z", got "2024-01-01T12:30:00Z"
✓ data.user.email: "john@example.com"
+ data.debug_info: {...} (not in expected)
```

The key principle: **always use plain English "expected X, got Y"** to make differences immediately obvious.

### 2. **Time Freezing**
Freeze time for deterministic date/time testing - built-in because almost every app needs this.

```python
from that import test, that, frozen_at

@test("user created at midnight")
@frozen_at("2024-01-01T00:00:00Z")
def test_user_creation():
    user = create_user()
    that(user.created_at).equals(datetime(2024, 1, 1, 0, 0, 0))
```

### 3. **HTTP Recording**
Record and replay HTTP requests - built-in because external API calls are ubiquitous.

```python
from that import test, that, recorded

@test("fetches user from API")
@recorded("user_fetch")  # Records to tests/cassettes/user_fetch.yaml
def test_fetch_user():
    response = requests.get("https://api.example.com/user/123")
    that(response.json()["name"]).equals("John Doe")
```

### 4. **Approximate Comparisons**
For floating point numbers, timestamps, and other imprecise values.

```python
that(price).approximately_equals(19.99, tolerance=0.01)
that(timestamp).approximately_equals(expected, within=timedelta(seconds=1))
```

### 3. **Test Speed Warnings**
Automatic detection and warning for slow tests.

```
✓ processes data (0.003s)
✓ calculates statistics (0.145s)
⚠ generates report (1.234s) [SLOW]
```

### 4. **Simple Snapshot Testing**
Compare test output against saved snapshots.

```python
@test("API response format stays consistent")
def test_api_response():
    response = get_user_api_response()
    that(response).matches_snapshot()
```

### 5. **Enhanced Collection Assertions**
More expressive assertions for lists, sets, and other collections.

```python
that(users).all_satisfy(lambda u: u.age >= 18)
that(emails).are_unique()
that(products).are_sorted_by("price")
that(items).has_length(5)
```

### 6. **Async Test Support**
Native support for async/await tests.

```python
@test("async operation completes")
async def test_async():
    result = await fetch_data()
    that(result).equals(expected)
```

### 7. **Test Tagging**
Tag tests for selective execution.

```python
@test("sends email notification")
@slow
@requires_network
def test_email():
# Run with: that --skip-slow
# Or: that --only-tag=requires_network
```

### 8. **Focused Output Mode**
Show only failures with full context.

```bash
that --focus

✓ test_user_creation
✓ test_user_validation
✗ test_user_login
  
  that(login_result.status).equals("success")
  
  Expected: "success"
  Actual: "failed"
  
  Context:
    login_result = {"status": "failed", "error": "Invalid password"}
```

## Plugin Features

These features are available as separate packages to keep the core library focused. They add specialized functionality that not everyone needs.

### 1. **Performance Benchmarking** (`that-benchmark`)
Fail tests that exceed time limits.

```python
from that_benchmark import benchmark

@test("processes quickly")
@benchmark(max_time=0.1)  # Fails if > 100ms
def test_performance():
    process_large_dataset()
```

### 2. **Simple Mocking** (`that-mock`)
Basic mocking functionality.

```python
from that_mock import mock

@test("sends notification")
@mock("myapp.send_email")
def test_notification(send_email):
# send_email is automatically mocked
```

## Explicitly Excluded Features

These features were considered but rejected to maintain simplicity and clarity.

### 1. **Built-in Fixtures**
**Why not:** Python already has functions and context managers. Adding a fixture system creates unnecessary complexity and non-standard patterns.

**Instead:** Use plain Python functions
```python
# Just use a function
def test_user():
    return User("john@example.com")

@test("user has email")
def test_email():
    user = test_user()
    that(user.email).equals("john@example.com")
```

### 2. **Setup/Teardown Blocks**
**Why not:** Context managers and try/finally already handle this better and more explicitly.

**Instead:** Use context managers
```python
from contextlib import contextmanager

@contextmanager
def test_database():
    db = create_db()
    try:
        yield db
    finally:
        db.close()

@test("database operation")
def test_db():
    with test_database() as db:
# Auto cleanup when done
```

### 3. **Test Subjects**
**Why not:** Adds state and complexity. `that(user.age).equals(30)` is already clear.

**What we avoided:**
```python
# We don't need this
subject(user)
subject.age.equals(30)  # Less clear than that(user.age).equals(30)
```

### 4. **Dependency Injection**
**Why not:** Too much magic. Explicit is better than implicit.

### 5. **Test Generators**
**Why not:** Write explicit tests. Generated tests are harder to debug and understand.

### 6. **Built-in Factory Functions**
**Why not:** Test data creation is domain-specific. Libraries shouldn't dictate how you create test data.

### 7. **Complex Mocking Framework**
**Why not:** This dramatically expands scope. Use existing mocking libraries if needed.

### 8. **Parameterized Tests**
**Why not:** Just write multiple tests or use a loop. Explicit is clearer than decorator magic.

## Design Principles

Every feature decision is evaluated against these criteria:

1. **Does it make test output clearer?** - Core mission
2. **Does it reduce boilerplate without adding magic?** - Simplicity matters
3. **Can it be explained in one sentence?** - Complexity test
4. **Would a developer guess how to use it without docs?** - Intuitive API

## Plugin Architecture

Plugins use a minimal interface to extend functionality:

```python
class Plugin:
    def before_test(self, test): pass
    def after_test(self, test, result): pass
    def setup(self): pass
```

This allows powerful extensions while keeping the core library under 1000 lines of code.

## Summary

**Core**: Features that make test output clearer, assertions more expressive, and handle common real-world testing needs (time control, HTTP recording).

**Plugins**: Specialized features that genuinely aren't needed by most projects.

**Excluded**: Features that add complexity without proportional benefit or duplicate existing Python functionality.

### Why Time Freezing and HTTP Recording Are Core Features

Initially, we considered making these plugins to keep the core minimal. However, real-world experience shows that:

1. **Almost every application** deals with timestamps and external APIs
2. **Deterministic tests require both** - you can't have reproducible tests with dynamic times or live HTTP calls
3. **Making them plugins is friction** - if everyone needs to install `that-freezegun` and `that-vcr`, we're just making setup harder

Following the "boring over trendy" principle: these are established, essential testing needs, not fancy extras. Including them by default provides a better out-of-box experience without sacrificing simplicity.

The goal remains a testing library that Python developers can understand in 30 seconds and that shows them exactly what went wrong when tests fail - now with the tools they actually need built-in.