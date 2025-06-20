# Your First Test

Let's write your first Test That test in 30 seconds and see why developers love this library.

## The 30-Second Test

Create a file called `test_first.py`:

```python title="test_first.py"
from that import that, test

@test("math should work correctly")
def test_basic_math():
    result = 2 + 2
    that(result).equals(4)
```

Run it:

```bash
that
```

Output:
```
✓ math should work correctly (0.001s)

1 test passed in 0.001s
```

**Congratulations!** You just wrote and ran your first Test That test.

## What Makes This Special?

Let's see what happens when a test fails. Change the test to:

```python title="test_first.py"
from that import that, test

@test("math should work correctly")
def test_basic_math():
    result = 2 + 2
    that(result).equals(5)  # Wrong expected value
```

Run it again:

```bash
that
```

Output:
```
✗ math should work correctly

  that(result).equals(5)
  
  Expected: 5
  Actual:   4
```

**See the difference?** Test That tells you exactly:
- What assertion failed
- What you expected
- What you actually got

No cryptic error messages. No guessing.

## Let's Try Something More Interesting

```python title="test_user.py"
from that import that, test

@test("user data should be valid")
def test_user_validation():
    user = {
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "age": 28,
        "active": True
    }
    
    # Chain multiple assertions
    that(user["name"]) \
        .is_not_none() \
        .is_instance_of(str) \
        .contains("Alice") \
        .has_length(13)
    
    that(user["email"]).matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    that(user["age"]).is_between(18, 65)
    that(user["active"]).is_true()
```

Run it:
```bash
that test_user.py
```

Output:
```
✓ user data should be valid (0.002s)

1 test passed in 0.002s
```

## When Things Go Wrong

Let's see Test That's intelligent error messages. Change the user data:

```python title="test_user.py"
from that import that, test

@test("user data should be valid")
def test_user_validation():
    user = {
        "name": "Alice Johnson",
        "email": "invalid-email",  # Invalid email
        "age": 28,
        "active": True
    }
    
    that(user["email"]).matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
```

Output:
```
✗ user data should be valid

  that(user["email"]).matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
  
  Expected: string matching pattern '^[\w\.-]+@[\w\.-]+\.\w+$'
  Actual:   'invalid-email'
```

**Crystal clear!** You know exactly what failed and why.

## Testing Collections

Test That excels at testing complex data structures:

```python title="test_collections.py"
from that import that, test

@test("shopping cart should work correctly")
def test_shopping_cart():
    cart = {
        "items": [
            {"name": "Laptop", "price": 999.99, "quantity": 1},
            {"name": "Mouse", "price": 29.99, "quantity": 2},
            {"name": "Keyboard", "price": 79.99, "quantity": 1}
        ],
        "total": 1139.97,
        "discount": 0.1
    }
    
    # Test the structure
    that(cart).has_key("items").has_key("total")
    
    # Test the items
    that(cart["items"]) \
        .has_length(3) \
        .all(lambda item: item["price"] > 0) \
        .any(lambda item: item["name"] == "Laptop")
    
    # Test calculations
    expected_total = sum(item["price"] * item["quantity"] for item in cart["items"])
    that(cart["total"]).is_close_to(expected_total, tolerance=0.01)
```

## Error Handling

Test That makes testing exceptions elegant:

```python title="test_errors.py"
from that import that, test

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

@test("division should handle zero correctly")
def test_division_by_zero():
    # Test that it raises the right exception
    that(lambda: divide(10, 0)).raises(ValueError)
    
    # Test the exact error message
    that(lambda: divide(10, 0)).raises(ValueError, "Cannot divide by zero")
    
    # Test normal operation
    that(divide(10, 2)).equals(5.0)
```

## Organizing Tests with Suites

Group related tests together:

```python title="test_calculator.py"
from that import that, test, suite

class Calculator:
    def add(self, a, b): return a + b
    def subtract(self, a, b): return a - b
    def multiply(self, a, b): return a * b

with suite("Calculator Operations"):
    
    @test("should add numbers")
    def test_addition():
        calc = Calculator()
        that(calc.add(2, 3)).equals(5)
    
    @test("should subtract numbers")
    def test_subtraction():
        calc = Calculator()
        that(calc.subtract(5, 3)).equals(2)
    
    @test("should multiply numbers")
    def test_multiplication():
        calc = Calculator()
        that(calc.multiply(4, 3)).equals(12)
```

Output:
```
Calculator Operations
  ✓ should add numbers (0.001s)
  ✓ should subtract numbers (0.001s)
  ✓ should multiply numbers (0.001s)

3 tests passed in 0.003s
```

## What You've Learned

In just a few minutes, you've seen how Test That:

1. **Makes testing simple** - Just import and use `that()`
2. **Provides clear error messages** - Know exactly what failed
3. **Supports fluent assertions** - Chain assertions naturally
4. **Handles complex data** - Test collections, objects, and more
5. **Organizes tests elegantly** - Use suites to group related tests

## Common Patterns You'll Use

### String Testing
```python
that("hello@example.com") \
    .contains("@") \
    .ends_with(".com") \
    .matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
```

### Number Testing
```python
that(price) \
    .is_greater_than(0) \
    .is_less_than(1000) \
    .is_close_to(99.99, tolerance=0.01)
```

### Collection Testing
```python
that(users) \
    .is_not_empty() \
    .has_length(5) \
    .all(lambda u: u["age"] >= 18) \
    .any(lambda u: u["role"] == "admin")
```

## Next Steps

You're ready to dive deeper! Here's what to explore next:

1. **[Quick Start Guide](quickstart.md)** - Learn all the core features in 5 minutes
2. **[Assertion Guide](../guide/assertions.md)** - Master all available assertions
3. **[Real Examples](../examples/basic.md)** - See practical testing patterns

## Pro Tips

### Use Descriptive Test Names
```python
# Good
@test("user email should be validated before saving to database")

# Less helpful
@test("test email")
```

### Chain Related Assertions
```python
# Good - shows the relationship
that(response) \
    .has_key("status") \
    .has_key("data") \
    .contains_subset({"status": "success"})

# Works but less clear
that(response).has_key("status")
that(response).has_key("data")
that(response).contains_subset({"status": "success"})
```

### Test One Thing at a Time
```python
# Good - focused test
@test("user age should be validated")
def test_user_age_validation():
    that(validate_age(25)).equals(25)
    that(lambda: validate_age(-1)).raises(ValueError)

# Less focused
@test("user validation")
def test_user_everything():
    # Tests age, email, name, etc. all in one test
```

Ready to become a Test That expert? → [Quick Start Guide](quickstart.md)
