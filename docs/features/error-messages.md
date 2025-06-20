# Intelligent Error Messages

Test That's greatest strength is showing you exactly what went wrong when tests fail. No more guessing, no more digging through stack traces.

## The Problem with Traditional Testing

When traditional tests fail, you get cryptic messages:

=== "pytest"
    ```
    >       assert user == expected_user
    E       AssertionError: assert {'age': 28, 'email': 'john@example.com', 'name': 'John Doe', 'verified': False} == {'age': 30, 'email': 'john@example.com', 'name': 'John Doe', 'verified': True}
    E         Omitting 1 identical items, use -vv to show
    E         Differing items:
    E         {'age': 28} != {'age': 30}
    E         {'verified': False} != {'verified': True}
    ```

=== "unittest"
    ```
    AssertionError: {'age': 28, 'email': 'john@example.com', 'name': 'John Doe', 'verified': False} != {'age': 30, 'email': 'john@example.com', 'name': 'John Doe', 'verified': True}
    ```

**You have to decode what went wrong.**

## Test That's Clear Messages

The same test failure in Test That:

```
✗ user data should match expected format

  that(user).equals(expected_user)
  
  Dictionary differences:
  ✓ email: "john@example.com"
  ✓ name: "John Doe"
  ✗ age: expected 30, got 28
  ✗ verified: expected True, got False
```

**You immediately know what's different and why the test failed.**

## Type-Specific Error Messages

### Dictionary Differences

```python
from that import that, test

@test("user profile should be complete")
def test_user_profile():
    user = {
        "id": 123,
        "name": "John Doe",
        "email": "john@example.com",
        "age": 28,
        "verified": False,
        "extra_field": "unexpected"
    }
    
    expected = {
        "id": 123,
        "name": "John Doe", 
        "email": "john@example.com",
        "age": 30,
        "verified": True,
        "missing_field": "should be here"
    }
    
    that(user).equals(expected)
```

**Output:**
```
✗ user profile should be complete

  that(user).equals(expected)
  
  Dictionary differences:
  ✓ id: 123
  ✓ name: "John Doe"
  ✓ email: "john@example.com"
  ✗ age: expected 30, got 28
  ✗ verified: expected True, got False
  + extra_field: "unexpected" (not in expected)
  - missing_field: "should be here" (expected but not found)
```

### List Differences

```python
@test("shopping cart should contain correct items")
def test_shopping_cart():
    cart_items = ["laptop", "keyboard", "monitor", "speakers"]
    expected_items = ["laptop", "mouse", "monitor"]
    
    that(cart_items).equals(expected_items)
```

**Output:**
```
✗ shopping cart should contain correct items

  that(cart_items).equals(expected_items)
  
  List differences:
  Length: expected 3 items, got 4
  
  [0] ✓ "laptop"
  [1] ✗ expected "mouse", got "keyboard"
  [2] ✓ "monitor"
  [3] + "speakers" (unexpected item)
```

### String Differences

```python
@test("welcome message should be personalized")
def test_welcome_message():
    message = "Hello, Jane! Welcome to our service."
    expected = "Hello, John! Welcome to our service."
    
    that(message).equals(expected)
```

**Output:**
```
✗ welcome message should be personalized

  that(message).equals(expected)
  
  Expected: "Hello, John! Welcome to our service."
  Actual:   "Hello, Jane! Welcome to our service."
  ----------^
  
  First difference at position 7: expected 'John' but got 'Jane'
```

### Numeric Differences

```python
@test("calculation should be accurate")
def test_calculation():
    total = 89.99
    expected = 99.99
    
    that(total).equals(expected)
```

**Output:**
```
✗ calculation should be accurate

  that(total).equals(expected)
  
  Expected: 99.99
  Actual:   89.99
  Difference: -10.00
```

## Complex Nested Structures

### API Response Differences

```python
@test("API response should match expected format")
def test_api_response():
    response = {
        "status": "success",
        "data": {
            "user": {
                "id": 123,
                "name": "Jane Doe",
                "profile": {
                    "age": 25,
                    "location": "New York"
                }
            },
            "permissions": ["read", "write"]
        },
        "metadata": {
            "timestamp": "2024-01-01T12:30:00Z",
            "version": "1.1"
        }
    }
    
    expected = {
        "status": "success",
        "data": {
            "user": {
                "id": 123,
                "name": "John Doe",
                "profile": {
                    "age": 30,
                    "location": "San Francisco"
                }
            },
            "permissions": ["read", "write", "admin"]
        },
        "metadata": {
            "timestamp": "2024-01-01T12:00:00Z",
            "version": "1.0"
        }
    }
    
    that(response).equals(expected)
```

**Output:**
```
✗ API response should match expected format

  that(response).equals(expected)
  
  Nested dictionary differences:
  ✓ status: "success"
  ✗ data.user.name: expected "John Doe", got "Jane Doe"
  ✗ data.user.profile.age: expected 30, got 25
  ✗ data.user.profile.location: expected "San Francisco", got "New York"
  ✗ data.permissions: expected ["read", "write", "admin"], got ["read", "write"]
  ✗ metadata.timestamp: expected "2024-01-01T12:00:00Z", got "2024-01-01T12:30:00Z"
  ✗ metadata.version: expected "1.0", got "1.1"
```

## Collection Error Messages

### List Content Errors

```python
@test("user roles should be correct")
def test_user_roles():
    user_roles = ["user", "editor", "viewer"]
    that(user_roles).contains("admin")
```

**Output:**
```
✗ user roles should be correct

  that(user_roles).contains("admin")
  
  Expected: list containing "admin"
  Actual:   ["user", "editor", "viewer"]
  
  The item "admin" was not found in the list.
```

### Dictionary Key Errors

```python
@test("user should have required fields")
def test_required_fields():
    user = {"name": "John", "email": "john@example.com"}
    that(user).has_key("phone")
```

**Output:**
```
✗ user should have required fields

  that(user).has_key("phone")
  
  Expected: dictionary with key "phone"
  Actual:   {"name": "John", "email": "john@example.com"}
  
  Available keys: ["name", "email"]
```

## Type Mismatch Messages

### Instance Type Errors

```python
@test("user ID should be an integer")
def test_user_id_type():
    user_id = "123"  # String instead of int
    that(user_id).is_instance_of(int)
```

**Output:**
```
✗ user ID should be an integer

  that(user_id).is_instance_of(int)
  
  Expected: instance of <class 'int'>
  Actual:   "123" (instance of <class 'str'>)
```

### Exact Type Errors

```python
@test("price should be a float")
def test_price_type():
    price = 19  # int instead of float
    that(price).has_type(float)
```

**Output:**
```
✗ price should be a float

  that(price).has_type(float)
  
  Expected: exact type <class 'float'>
  Actual:   19 (exact type <class 'int'>)
  
  Note: Value is instance of int, but exact type float was required.
```

## Pattern Matching Errors

### Regex Pattern Failures

```python
@test("email should be valid format")
def test_email_format():
    email = "not-an-email"
    that(email).matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
```

**Output:**
```
✗ email should be valid format

  that(email).matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
  
  Expected: string matching pattern '^[\w\.-]+@[\w\.-]+\.\w+$'
  Actual:   "not-an-email"
  
  The string does not match the required email pattern.
```

### String Content Errors

```python
@test("message should contain greeting")
def test_message_content():
    message = "Goodbye, have a nice day!"
    that(message).contains("Hello")
```

**Output:**
```
✗ message should contain greeting

  that(message).contains("Hello")
  
  Expected: string containing "Hello"
  Actual:   "Goodbye, have a nice day!"
  
  The substring "Hello" was not found.
```

## Numeric Comparison Errors

### Range Errors

```python
@test("age should be valid")
def test_age_validation():
    age = 15
    that(age).is_between(18, 65)
```

**Output:**
```
✗ age should be valid

  that(age).is_between(18, 65)
  
  Expected: number between 18 and 65 (inclusive)
  Actual:   15
  
  Value 15 is below the minimum of 18.
```

### Floating Point Precision

```python
@test("calculation should be precise")
def test_precision():
    result = 0.1 + 0.2  # 0.30000000000000004
    that(result).equals(0.3)
```

**Output:**
```
✗ calculation should be precise

  that(result).equals(0.3)
  
  Expected: 0.3
  Actual:   0.30000000000000004
  Difference: 4.163336342344337e-17
  
  Hint: For floating point comparisons, consider using is_close_to() with a tolerance.
  Example: that(result).is_close_to(0.3, tolerance=0.0001)
```

## Exception Testing Errors

### Wrong Exception Type

```python
@test("should raise validation error")
def test_validation_error():
    def validate_age(age):
        if age < 0:
            raise TypeError("Age cannot be negative")  # Wrong exception type
        return age
    
    that(lambda: validate_age(-5)).raises(ValueError)
```

**Output:**
```
✗ should raise validation error

  that(lambda: validate_age(-5)).raises(ValueError)
  
  Expected: ValueError to be raised
  Actual:   TypeError was raised instead
  
  Exception message: "Age cannot be negative"
```

### No Exception Raised

```python
@test("should raise error for invalid input")
def test_error_handling():
    def safe_function():
        return "all good"
    
    that(safe_function).raises(ValueError)
```

**Output:**
```
✗ should raise error for invalid input

  that(safe_function).raises(ValueError)
  
  Expected: ValueError to be raised
  Actual:   No exception was raised
  
  Function returned: "all good"
```

## Chained Assertion Errors

When chained assertions fail, Test That shows exactly which assertion in the chain failed:

```python
@test("user should be valid and active")
def test_user_validation():
    user = {
        "name": "John",
        "email": "invalid-email",
        "active": True
    }
    
    that(user) \
        .has_key("name") \
        .has_key("email") \
        .has_value_matching("email", lambda e: "@" in e) \
        .has_key("active") \
        .has_value("active", True)
```

**Output:**
```
✗ user should be valid and active

  that(user).has_key("name").has_key("email").has_value_matching("email", lambda e: "@" in e)
                                                ^
  Chain failed at: has_value_matching("email", lambda e: "@" in e)
  
  Expected: email value to match condition
  Actual:   "invalid-email"
  
  The lambda condition returned False for the email value.
```

## Contextual Hints and Suggestions

Test That provides helpful hints when it can suggest better approaches:

### Floating Point Comparison Hint

```python
@test("prices should match")
def test_price_comparison():
    calculated_price = 19.999999999999996
    expected_price = 20.0
    
    that(calculated_price).equals(expected_price)
```

**Output:**
```
✗ prices should match

  that(calculated_price).equals(expected_price)
  
  Expected: 20.0
  Actual:   19.999999999999996
  Difference: -4.440892098500626e-15
  
  💡 Hint: This looks like a floating point precision issue.
  Consider using: that(calculated_price).is_close_to(20.0, tolerance=0.0001)
```

### Collection Comparison Hint

```python
@test("lists should be equivalent")
def test_list_comparison():
    actual = [3, 1, 2]
    expected = [1, 2, 3]
    
    that(actual).equals(expected)
```

**Output:**
```
✗ lists should be equivalent

  that(actual).equals(expected)
  
  List differences:
  [0] ✗ expected 1, got 3
  [1] ✗ expected 2, got 1  
  [2] ✗ expected 3, got 2
  
  💡 Hint: Lists contain the same elements but in different order.
  Consider using: that(actual).contains_same_elements_as(expected)
  Or if order matters, sort first: that(sorted(actual)).equals(sorted(expected))
```

## Best Practices for Clear Error Messages

### 1. Use Descriptive Test Names
```python
# Good - error message includes context
@test("user email should be validated before account creation")
def test_email_validation():
    that(create_user("invalid")).raises(ValueError)

# Less helpful
@test("test user")
def test_user():
    that(create_user("invalid")).raises(ValueError)
```

### 2. Test Specific Behaviors
```python
# Good - specific assertion with clear error
@test("user age should be positive integer")
def test_user_age():
    that(user.age).is_instance_of(int).is_greater_than(0)

# Less specific - harder to understand failure
@test("user should be valid")
def test_user():
    that(validate_user(user)).is_true()
```

### 3. Use Appropriate Assertion Methods
```python
# Good - specific assertion for the use case
that(email).matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# Less specific - generic equality check
that(bool(re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email))).is_true()
```

## Next Steps

- **[Fluent Assertions](fluent-assertions.md)** - Learn all available assertion methods
- **[Real Examples](../examples/web-api-testing.md)** - See error messages in real scenarios
- **[Best Practices](../best-practices/assertion-patterns.md)** - Write tests that fail clearly
