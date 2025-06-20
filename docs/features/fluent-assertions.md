# Fluent Assertions

Test That's fluent assertion API makes your tests readable, expressive, and easy to understand. Chain assertions naturally to create tests that read like English.

## The Power of Fluent Assertions

Instead of multiple separate assertions:

```python
# Traditional approach
assert user is not None
assert isinstance(user, dict)
assert "email" in user
assert user["email"].endswith("@example.com")
assert len(user["name"]) > 0
```

Write fluent, chainable assertions:

```python
# Test That approach
that(user) \
    .is_not_none() \
    .is_instance_of(dict) \
    .has_key("email") \
    .has_value_matching("email", lambda email: email.endswith("@example.com")) \
    .has_key("name") \
    .has_value_matching("name", lambda name: len(name) > 0)
```

## Core Assertion Categories

### Equality and Identity

```python
# Basic equality
that(42).equals(42)
that("hello").equals("hello")
that([1, 2, 3]).equals([1, 2, 3])

# Identity checks
that(obj).is_same_as(obj)
that(copy).is_not_same_as(original)

# Inequality
that(5).does_not_equal(10)
that("hello").is_not("goodbye")
```

### Type Assertions

```python
# Instance checking
that("hello").is_instance_of(str)
that([1, 2, 3]).is_instance_of(list)
that(42).is_instance_of(int)

# Exact type checking
that("hello").has_type(str)
that(42).has_type(int)
that(3.14).has_type(float)

# Multiple type checking
that(value).is_instance_of((str, int))  # Either string or int
```

### Numeric Assertions

```python
# Comparisons
that(10).is_greater_than(5)
that(5).is_less_than(10)
that(7).is_greater_than_or_equal_to(7)
that(3).is_less_than_or_equal_to(3)

# Ranges
that(5).is_between(1, 10)
that(5).is_between(1, 10, inclusive=True)  # Default
that(5).is_between(1, 10, inclusive=False)  # Exclusive

# Floating point comparisons
that(0.1 + 0.2).is_close_to(0.3, tolerance=0.0001)
that(price).approximately_equals(19.99, tolerance=0.01)

# Sign checks
that(5).is_positive()
that(-3).is_negative()
that(0).is_zero()
that(42).is_non_zero()

# Even/odd
that(4).is_even()
that(5).is_odd()
```

### String Assertions

```python
# Content checks
that("hello world").contains("world")
that("hello world").does_not_contain("goodbye")
that("hello").starts_with("he")
that("hello").ends_with("lo")

# Pattern matching
that("test@example.com").matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
that("not-an-email").does_not_match(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# Length
that("hello").has_length(5)
that("").is_empty()
that("hello").is_not_empty()

# Case checks
that("hello").is_lower()
that("HELLO").is_upper()
that("Hello World").is_title()

# Whitespace
that("  hello  ").strip().equals("hello")
that("hello world").contains_whitespace()
that("helloworld").does_not_contain_whitespace()
```

### Collection Assertions

#### Lists and Tuples

```python
# Membership
that([1, 2, 3]).contains(2)
that([1, 2, 3]).does_not_contain(4)
that([1, 2, 3]).contains_all([1, 3])
that([1, 2, 3]).contains_any([4, 3])

# Length and emptiness
that([1, 2, 3]).has_length(3)
that([]).is_empty()
that([1, 2, 3]).is_not_empty()

# Ordering
that([1, 2, 3]).is_sorted()
that([3, 2, 1]).is_sorted(reverse=True)
that([1, 3, 2]).is_not_sorted()

# Uniqueness
that([1, 2, 3]).has_unique_elements()
that([1, 2, 2]).has_duplicate_elements()

# Predicates
that([2, 4, 6]).all(lambda x: x % 2 == 0)
that([1, 2, 3]).any(lambda x: x > 2)
that([1, 2, 3]).none(lambda x: x > 5)

# First and last elements
that([1, 2, 3]).first_element().equals(1)
that([1, 2, 3]).last_element().equals(3)
```

#### Dictionaries

```python
# Keys and values
that({"name": "John"}).has_key("name")
that({"name": "John"}).does_not_have_key("age")
that({"name": "John"}).has_value("John")
that({"name": "John"}).does_not_have_value("Jane")

# Multiple keys
that({"name": "John", "age": 30}).has_keys(["name", "age"])
that({"name": "John", "age": 30}).has_all_keys(["name", "age"])
that({"name": "John", "age": 30}).has_any_keys(["name", "height"])

# Key-value pairs
that({"name": "John"}).has_item("name", "John")
that({"name": "John"}).does_not_have_item("name", "Jane")

# Subsets and supersets
that({"a": 1, "b": 2}).contains_subset({"a": 1})
that({"a": 1, "b": 2, "c": 3}).is_superset_of({"a": 1, "b": 2})

# Nested access
that({"user": {"name": "John"}}).has_nested_key("user.name")
that({"user": {"name": "John"}}).has_nested_value("user.name", "John")
```

#### Sets

```python
# Set relationships
that({1, 2, 3}).is_subset_of({1, 2, 3, 4, 5})
that({1, 2, 3, 4, 5}).is_superset_of({2, 3})
that({1, 2}).is_disjoint_with({3, 4})
that({1, 2, 3}).intersects_with({3, 4, 5})

# Set operations
that({1, 2, 3}).union({4, 5}).equals({1, 2, 3, 4, 5})
that({1, 2, 3}).intersection({2, 3, 4}).equals({2, 3})
that({1, 2, 3}).difference({2, 3}).equals({1})
```

### Boolean and None Assertions

```python
# Boolean values
that(True).is_true()
that(False).is_false()

# Truthiness
that(1).is_truthy()
that(0).is_falsy()
that("hello").is_truthy()
that("").is_falsy()

# None checks
that(None).is_none()
that("something").is_not_none()
```

### Exception Assertions

```python
# Basic exception checking
that(lambda: 1/0).raises(ZeroDivisionError)
that(lambda: int("abc")).raises(ValueError)

# Exception with specific message
that(lambda: raise_error()).raises(ValueError, "Invalid input")

# Exception message patterns
that(lambda: raise_error()).raises(ValueError) \
    .with_message_containing("Invalid") \
    .with_message_matching(r"Invalid \w+")

# No exception expected
that(lambda: safe_function()).does_not_raise()

# Capturing exceptions for further testing
def test_exception_details():
    with that(ValueError).as_exception() as exc:
        validate_input(-5)
    
    that(exc.value.args[0]).contains("negative")
```

## Advanced Chaining Patterns

### Complex Object Validation

```python
@test("user object should be completely valid")
def test_user_validation():
    user = {
        "id": 123,
        "profile": {
            "name": "John Doe",
            "email": "john@example.com",
            "preferences": {
                "theme": "dark",
                "notifications": True
            }
        },
        "roles": ["user", "admin"],
        "created_at": "2024-01-01T00:00:00Z"
    }
    
    that(user) \
        .is_instance_of(dict) \
        .has_key("id") \
        .has_key("profile") \
        .has_key("roles") \
        .has_nested_key("profile.name") \
        .has_nested_key("profile.email") \
        .has_nested_value("profile.preferences.theme", "dark") \
        .has_value_matching("roles", lambda roles: "admin" in roles) \
        .has_value_matching("created_at", lambda dt: dt.endswith("Z"))
```

### API Response Validation

```python
@test("API response should have correct structure")
def test_api_response():
    response = {
        "status": "success",
        "data": {
            "users": [
                {"id": 1, "name": "Alice", "active": True},
                {"id": 2, "name": "Bob", "active": False}
            ],
            "total": 2,
            "page": 1
        },
        "meta": {
            "timestamp": "2024-01-01T12:00:00Z",
            "version": "1.0"
        }
    }
    
    that(response) \
        .has_key("status") \
        .has_value("status", "success") \
        .has_nested_key("data.users") \
        .has_nested_key("data.total") \
        .has_nested_value("data.total", 2) \
        .has_value_matching("data.users", lambda users: len(users) == 2) \
        .has_value_matching("data.users", lambda users: all(u["id"] > 0 for u in users)) \
        .has_nested_key("meta.timestamp") \
        .has_nested_value_matching("meta.timestamp", lambda ts: ts.endswith("Z"))
```

## Custom Assertion Extensions

You can extend Test That with domain-specific assertions:

```python
from that.assertions import ThatAssertion

class EmailAssertions:
    def is_valid_email(self):
        """Check if the value is a valid email address."""
        import re
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, self.value):
            raise AssertionError(f"'{self.value}' is not a valid email address")
        return self
    
    def has_domain(self, domain):
        """Check if email has specific domain."""
        if not self.value.endswith(f"@{domain}"):
            raise AssertionError(f"Email '{self.value}' does not have domain '{domain}'")
        return self

# Extend ThatAssertion
ThatAssertion.is_valid_email = EmailAssertions.is_valid_email
ThatAssertion.has_domain = EmailAssertions.has_domain

# Usage
that("user@example.com").is_valid_email().has_domain("example.com")
```

## Best Practices

### 1. Chain Related Assertions
```python
# Good - shows relationship between assertions
that(user) \
    .is_not_none() \
    .is_instance_of(dict) \
    .has_key("email") \
    .has_value_matching("email", lambda e: "@" in e)

# Less clear - separate assertions
that(user).is_not_none()
that(user).is_instance_of(dict)
that(user).has_key("email")
that(user["email"]).contains("@")
```

### 2. Use Specific Assertions
```python
# Good - specific and clear
that(numbers).is_sorted()

# Less specific
that(numbers).equals(sorted(numbers))
```

### 3. Meaningful Test Names
```python
# Good - describes what's being tested
@test("user email should be validated before account creation")
def test_email_validation():
    that(lambda: create_user("invalid-email")).raises(ValueError)

# Less descriptive
@test("test user")
def test_user():
    # What about the user are we testing?
```

### 4. Break Long Chains When Needed
```python
# If the chain gets too long, break it up logically
user_assertion = that(user).is_not_none().is_instance_of(dict)
user_assertion.has_key("profile").has_key("settings")

profile_assertion = that(user["profile"])
profile_assertion.has_key("name").has_key("email")
```

## Next Steps

- **[Error Messages](error-messages.md)** - See how Test That provides clear feedback
- **[Advanced Features](../features/mocking.md)** - Explore mocking and time control
- **[Real Examples](../examples/web-api-testing.md)** - Practical usage patterns
