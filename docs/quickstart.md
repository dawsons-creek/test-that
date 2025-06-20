# Quick Start

## Install

```bash
pip install test-that
```

## Write Your First Test

Create `test_example.py`:

```python
from test_that import test, that

@test("basic math works")
def test_math():
    result = 2 + 2
    that(result).equals(4)

@test("string contains substring")
def test_strings():
    message = "Hello, world!"
    that(message).contains("world")
    that(message).has_length(13)

@test("function raises exception")
def test_exceptions():
    def divide_by_zero():
        return 1 / 0
    
    that(divide_by_zero).raises(ZeroDivisionError)
```

## Run Tests

```bash
that
```

Output:
```
  ✓ basic math works
  ✓ string contains substring
  ✓ function raises exception
────────────────────────────────────────
Ran 3 tests in 156μs
3 passed
```

## Group Tests with Suites

```python
from test_that import test, suite, that

with suite("User Validation"):
    
    @test("validates email format")
    def test_email():
        email = "user@example.com"
        that(email).matches(r".+@.+\..+")
    
    @test("validates age range")
    def test_age():
        age = 25
        that(age).is_between(18, 65)

with suite("Calculator"):
    
    @test("adds numbers")
    def test_add():
        that(10 + 5).equals(15)
    
    @test("divides numbers")
    def test_divide():
        that(10 / 2).equals(5.0)
```

Output:
```
User Validation
  ✓ validates email format
  ✓ validates age range
Calculator
  ✓ adds numbers
  ✓ divides numbers
────────────────────────────────────────
Ran 4 tests in 234μs
4 passed
```

## Add Test Data with Fixtures

```python
from test_that import test, suite, that, provide

with suite("Shopping Cart"):
    
    @provide
    def empty_cart():
        return {"items": [], "total": 0.0}
    
    @provide
    def sample_product():
        return {"id": 1, "name": "Widget", "price": 9.99}
    
    @test("starts empty")
    def test_empty_cart():
        that(empty_cart["items"]).is_empty()
        that(empty_cart["total"]).equals(0.0)
    
    @test("can add items")
    def test_add_item():
        empty_cart["items"].append(sample_product)
        empty_cart["total"] += sample_product["price"]
        
        that(empty_cart["items"]).has_length(1)
        that(empty_cart["total"]).equals(9.99)
```

## Test with Mocks

```python
from test_that import test, that, mock

class EmailService:
    def send_email(self, to, subject, body):
        # Real implementation would send email
        raise NotImplementedError()

class UserService:
    def __init__(self, email_service):
        self.email_service = email_service
    
    def welcome_user(self, email):
        self.email_service.send_email(
            to=email,
            subject="Welcome!",
            body="Thanks for signing up"
        )
        return {"status": "sent"}

@test("sends welcome email")
def test_welcome():
    email_service = EmailService()
    user_service = UserService(email_service)
    
    # Mock the email service
    email_mock = mock(email_service, 'send_email', return_value=True)
    
    # Test the behavior
    result = user_service.welcome_user("alice@example.com")
    
    # Verify the mock was called correctly
    email_mock.assert_called_once()
    that(email_mock.last_call.args[0]).equals("alice@example.com")
    that(email_mock.last_call.kwargs["subject"]).equals("Welcome!")
    that(result["status"]).equals("sent")
```

## Next Steps

- Read [Features](features.md) to learn about time control and HTTP recording
- See [All Assertions](assertions.md) for complete assertion reference
- Check [Running Tests](running.md) for command-line options