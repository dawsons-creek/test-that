Perfect choice! The library name matching the primary function is elegant - like how `pytest` is named after how you use it. Here's the updated spec:

# That - A Python Testing Library

*Because test output should tell you what failed, not make you guess.*

## Installation

```bash
pip install that
```

## Basic Usage

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

## Complete Product Specification

### Project Structure

```
myproject/
├── src/
│   └── myapp/
├── tests/
│   ├── test_user.py
│   ├── test_auth.py
│   └── test_api.py
├── pyproject.toml
└── README.md
```

### Running Tests

```bash
# Run all tests
that

# Run specific test file
that tests/test_user.py

# Run specific suite
that -s "User Management"

# Verbose mode (includes stack traces)
that -v

# Watch mode
that --watch
```

### Core API

```python
# tests/test_example.py
from that import test, suite, that

# Simple test
@test("basic math works")
def test_math():
    that(2 + 2).equals(4)

# Grouped tests
with suite("String Operations"):
    @test("uppercase conversion")
    def test_upper():
        that("hello".upper()).equals("HELLO")
    
    @test("string contains substring")
    def test_contains():
        that("hello world").contains("world")
```

### Setup/Teardown

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
        that(user.email).equals("john@example.com")
```

### Complete Assertion API

```python
# Equality
that(value).equals(expected)
that(value).does_not_equal(expected)

# Truthiness
that(value).is_true()
that(value).is_false()
that(value).is_none()
that(value).is_not_none()

# Collections
that(collection).contains(item)
that(collection).does_not_contain(item)
that(collection).is_empty()
that(collection).has_length(n)

# Strings
that(string).matches(regex_pattern)
that(string).starts_with(prefix)
that(string).ends_with(suffix)

# Exceptions
that(callable).raises(ExceptionType)
that(callable).does_not_raise()

# Numbers
that(number).is_greater_than(n)
that(number).is_less_than(n)
that(number).is_between(min, max)

# Types
that(value).is_instance_of(Type)
that(value).has_type(Type)
```

### Real-World Example

```python
# tests/test_payment.py
from that import test, suite, that
from myapp.payment import process_payment, PaymentError

with suite("Payment Processing"):
    @test("successful payment returns completed status")
    def test_successful_payment():
        result = process_payment({
            "amount": 99.99,
            "currency": "USD",
            "customer_id": 12345
        })
        
        that(result["status"]).equals("completed")
        that(result["amount"]).equals(99.99)
        that(result).contains("transaction_id")
    
    @test("invalid currency raises error")
    def test_invalid_currency():
        that(lambda: process_payment({
            "amount": 99.99,
            "currency": "INVALID"
        })).raises(PaymentError)
    
    @test("payment data matches expected format")
    def test_payment_format():
        result = process_payment({
            "amount": 50.00,
            "currency": "USD",
            "customer_id": 789
        })
        
        expected = {
            "status": "completed",
            "amount": 50.00,
            "currency": "USD",
            "customer_id": 789,
            "transaction_id": result.get("transaction_id"),  # Dynamic
            "timestamp": result.get("timestamp")  # Dynamic
        }
        
        that(result).equals(expected)
```

### Output Format

Normal output:
```
Payment Processing
  ✓ successful payment returns completed status
  ✗ invalid currency raises error
    
    that(lambda).raises(PaymentError)
    
    Expected exception: PaymentError
    Actual exception: ValueError("Unsupported currency: INVALID")
    
  ✗ payment data matches expected format
    
    that(result).equals(expected)
    
    Dictionary differences:
    ~ status: "pending" → "completed"
    - transaction_id (missing)

────────────────────────────────────────
Ran 3 tests in 0.021s
1 passed, 2 failed

FAILED
```

### Configuration

Optional `pyproject.toml`:
```toml
[tool.that]
# All optional - sensible defaults
test_dir = "tests"
pattern = "test_*.py"
verbose = false
color = true  # auto-detected by default
```

### Package Structure

```
that/
├── __init__.py       # Exports: test, suite, that
├── runner.py         # Test discovery and execution
├── assertions.py     # The 'that' API
├── output.py         # Formatting and display
└── __main__.py       # CLI entry point
```

## Design Principles

1. **One import**: `from that import test, suite, that`
2. **One way to do things**: No alternative APIs
3. **Clear over clever**: Readable code over magic
4. **Fast feedback**: Show what failed immediately
5. **No configuration required**: Just works

## Success Metrics

A developer using `that` should:
- Write their first test in under 30 seconds
- Understand any failure without scrolling or squinting
- Never need documentation for basic usage
- Feel like this is how testing should have always been

The name "that" perfectly captures the library's essence - it's all about asserting things about your values in plain English.