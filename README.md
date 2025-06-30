# Test That: Modern Python Testing Framework

**A developer-first testing framework that delivers crystal-clear failure diagnostics and precise test targeting.**

Test That transforms the testing experience by eliminating guesswork from test failures. When tests break, you get immediate, actionable insights with side-by-side expected vs actual comparisons. Combined with flexible test targeting and an intuitive fluent API, Test That accelerates debugging workflows and reduces time-to-fix.

## Why Test That?

- **Crystal Clear Failures**: No more parsing cryptic assertion errors - see exactly what went wrong
- **Precise Test Targeting**: Run specific tests by line number, pattern, or suite for efficient debugging  
- **Intelligent Test Organization**: Suite-based organization with automatic setup/teardown and dependency injection
- **Extensible Architecture**: Plugin system for custom assertions, time control, and HTTP recording
- **Rich Output**: Color-coded results with timing, stack traces, and focused failure modes

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

Write tests that read like documentation:

```python
from test_that import test, suite, that, fixture

@test("validates user email format")
def test_email_validation():
    user = User(email="invalid-email")
    that(user.is_valid()).equals(True)
    that(user.errors).is_empty()

@test("calculates order total with tax")  
def test_order_total():
    order = Order(items=[Item(price=100), Item(price=50)])
    that(order.total_with_tax(0.08)).equals(162.0)
```

**Crystal clear failures when things go wrong:**
```
✗ validates user email format

  that(user.is_valid()).equals(True)
  
  Expected: True
  Actual:   False
  
  Additional context:
  user.errors = ['Invalid email format: invalid-email']
```

No more digging through stack traces or print statements to understand test failures.

## Running Tests

Multiple CLI commands are available for convenience:

```bash
# Run all tests (any of these work)
test_that
that  
tt

# Run specific test file
tt tests/test_user.py

# Run test at specific line number
tt tests/test_user.py:42

# Run tests in line range  
tt tests/test_user.py:20-50

# Run multiple line numbers
tt tests/test_user.py:15,30,45

# Run specific suite
tt -s "User Management"

# Run tests matching pattern
tt -k "validation"

# Verbose mode (includes stack traces)
tt -v

# Disable colors
tt --no-color
```

## Core Features

### Intuitive Test Organization

Organize tests naturally with descriptive names and logical grouping:

```python
from test_that import suite, test, that

with suite("User Authentication"):
    @test("authenticates valid user credentials")
    def test_valid_login():
        user = authenticate("john@example.com", "secure_password")
        that(user.is_authenticated).is_true()
        that(user.role).equals("user")
    
    @test("rejects invalid credentials")
    def test_invalid_login():
        that(lambda: authenticate("bad@email.com", "wrong")).raises(AuthenticationError)
```

### Rich Assertion Library

Expressive assertions that read like natural language:

```python
# Collections and strings
that(users).has_length(5)
that(email).contains("@").and_starts_with("user")
that(response.status_code).is_between(200, 299)

# Objects and types  
that(user).is_instance_of(User)
that(user.created_at).is_not_none()

# Advanced assertions
that(api_call).raises(ValidationError).with_message("Invalid input")
that(slow_function).completes_within(seconds=2)
```

### Powerful Test Fixtures

Clean, predictable test environments with automatic resource management:

```python
from test_that import fixture

# Function-scoped fixture (runs for each test)
@fixture()
def database():
    """Create test database with automatic cleanup"""
    db = create_test_database()
    yield db  # Provide to test
    db.cleanup()  # Automatic teardown

# Suite-scoped fixture (shared across tests)
@fixture(scope="suite")
def api_client():
    """Expensive setup shared across all tests"""
    return APIClient(base_url="https://api.test.com")

# Fixtures with dependencies
@fixture()
def user(database):
    """Fixture that depends on database fixture"""
    return database.create_user(email="test@example.com")

with suite("Payment Processing"):
    @test("processes successful payment")
    def test_payment_success(database, api_client):
        payment = process_payment(api_client, amount=100.0)
        database.save(payment)
        that(payment.status).equals("completed")
        that(payment.transaction_id).is_not_none()
```

### Parametrized Testing

Run the same test with multiple inputs:

```python
from test_that import parametrize

@parametrize((2, 2, 4), (3, 3, 6), (5, 5, 10))
@test("multiplication works")
def test_multiply(a, b, expected):
    that(a * b).equals(expected)

# With descriptive parameters
@parametrize(
    {"email": "valid@example.com", "valid": True},
    {"email": "invalid-email", "valid": False},
    {"email": "@no-name.com", "valid": False}
)
@test("validates email formats")
def test_email_validation(email, valid):
    that(is_valid_email(email)).equals(valid)
```

### Class-Based Test Suites

Organize related tests as methods in a class:

```python
@suite
class UserManagementTests:
    @test("creates new user")
    def test_create_user(self, database):
        user = User.create(email="new@example.com")
        that(database.users.count()).equals(1)
        that(user.id).is_not_none()
    
    @test("prevents duplicate emails")
    def test_duplicate_email(self, database):
        User.create(email="test@example.com")
        that(lambda: User.create(email="test@example.com")).raises(DuplicateError)
```

### Async Test Support

Full support for async/await testing:

```python
@test("fetches data asynchronously")
async def test_async_fetch(api_client):
    data = await api_client.fetch_data()
    that(data).is_not_empty()
    that(data[0]).contains("id")

@test("handles concurrent requests")
async def test_concurrent():
    results = await asyncio.gather(
        fetch_user(1),
        fetch_user(2),
        fetch_user(3)
    )
    that(results).has_length(3)
```

### Advanced Testing Capabilities

#### Time Control and Replay
```python
from test_that import replay

# Freeze time for deterministic testing
@replay.time("2024-01-15T10:00:00Z")
@test("creates order with correct timestamp")
def test_order_timestamp():
    order = create_order()
    that(order.created_at).equals(datetime(2024, 1, 15, 10, 0, 0))
```

#### HTTP Request Recording and Replay
```python
from test_that import replay

# Record HTTP interactions for reliable API testing
@replay.http("user_api_calls.json")
@test("fetches user profile from API")
def test_user_api():
    # First run: records real HTTP calls
    # Subsequent runs: replays recorded responses
    user = fetch_user_profile(user_id=123)
    that(user.name).equals("John Doe")
    that(user.email).contains("@example.com")

# Test with sanitized recordings (removes sensitive data)
@replay.http("sanitized_api.json", sanitize=True)
@test("processes payment without exposing credentials")
def test_payment_processing():
    # API keys, tokens, and sensitive headers are automatically redacted
    result = process_payment(amount=100.0, token="secret_token")
    that(result.status).equals("success")
```

#### Intelligent Mocking
```python
from test_that import mock, mock_that

@test("handles API failures gracefully")
def test_api_failure():
    # Simple mocking
    api_mock = mock(client, 'get_user', side_effect=ConnectionError("Timeout"))
    result = fetch_user_data(user_id=123)
    that(result.error).equals("Service temporarily unavailable")
    
    # Verify mock was called
    api_mock.assert_called_once()

# Advanced mock features
@test("tracks complex API interactions")
def test_api_patterns():
    # Sequential returns
    api_mock = mock(client, 'fetch', side_effect=[data1, data2, data3])
    
    # Make calls
    service = DataService(client)
    service.sync_all()
    
    # Rich assertions with mock_that
    that(mock_that(api_mock).call_count).equals(3)
    that(mock_that(api_mock).first_call.args).contains('users')
    that(mock_that(api_mock).last_call.kwargs).contains('retry')
    
    # Access specific calls
    second_call = api_mock.get_call(1)
    that(second_call.args[0]).equals('posts')
```

#### Plugin System
```python
# Custom assertion plugins
from test_that.plugins import register_assertion

@register_assertion
def validates_email(that_obj, email):
    """Custom assertion for email validation"""
    if "@" not in email or "." not in email:
        raise AssertionError(f"Invalid email format: {email}")
    return that_obj

# Usage
that("user@example.com").validates_email()
```

### Combined Time and HTTP Replay
```python
from test_that import replay

# Test with both frozen time and recorded HTTP calls
@replay(time="2024-01-01T12:00:00Z", http="integration_test")
@test("complete integration flow")
def test_user_registration():
    # Time is frozen and HTTP calls are recorded/replayed
    user = register_user(email="test@example.com")
    that(user.created_at).equals(datetime(2024, 1, 1, 12, 0, 0))
    that(user.verification_sent).is_true()
```

## Precise Test Targeting

Test That supports flexible test execution with granular control:

### Line Number Targeting
```bash
# Note: Line number targeting is currently being fixed in the CLI
# The feature exists but has an argument parsing issue

# Run test at specific line
tt tests/test_user.py:42

# Run tests in a range 
tt tests/test_user.py:20-50

# Run multiple specific lines
tt tests/test_user.py:15,30,45
```

### Pattern Matching
```bash
# Run tests with names containing "validation"
tt -k "validation"

# Run specific test suite
tt -s "User Management"

# Combine file and pattern
tt tests/test_user.py -k "email"
```

This makes debugging and development much faster by running only the tests you're working on.

## Assertion API

### Equality
```python
that(value).equals(expected)
that(value).does_not_equal(expected)
that(3.14159).approximately_equals(3.14, tolerance=0.01)
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
that([2, 4, 6]).all_satisfy(lambda x: x % 2 == 0)
that([1, 2, 3]).any_satisfy(lambda x: x > 2)
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

### Object Attributes
```python
that(user).has_attr("email")
that(user).attr("email").equals("test@example.com")
that(user).attr("roles").contains("admin")
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

## Production Ready

### Enterprise Features
- **Plugin Architecture**: Extend functionality with custom assertions, reporters, and integrations
- **CI/CD Optimized**: Fast test execution with precise targeting reduces pipeline times
- **Team Collaboration**: Clear, consistent test output improves code review efficiency
- **Comprehensive Examples**: Full-featured [Todo CLI example](examples/todo_cli/) demonstrates real-world patterns

### Design Philosophy

Test That is built on principles that scale from solo projects to enterprise teams:

- **Clarity First**: Every failure message should immediately reveal the problem
- **Speed Matters**: Precise test targeting eliminates time wasted running irrelevant tests  
- **Zero Friction**: Single import, zero configuration, immediate productivity
- **Extensible Core**: Plugin system adapts to your specific testing needs
- **Production Ready**: Designed with years of testing experience, built for modern development workflows

## Get Started Today

Transform your testing experience:

1. **Install**: `pip install git+ssh://git@github.com/dawsons-creek/test-that.git`
2. **Write**: Use the intuitive `that()` API for crystal-clear assertions
3. **Run**: Target specific tests with `tt -k "pattern"` for efficient debugging
4. **Scale**: Leverage plugins and advanced features as your project grows

Experience the difference that clear, actionable test failures make in your development workflow.

---

## License

MIT License - see LICENSE file for details.
