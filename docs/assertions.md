# All Assertions

Complete reference for all assertion methods available with `that()`.

## Equality

### `equals(value)`
Value equals expected value.
```python
that(42).equals(42)
that("hello").equals("hello")
that([1, 2, 3]).equals([1, 2, 3])
```

### `does_not_equal(value)`
Value does not equal expected value.
```python
that(42).does_not_equal(43)
that("hello").does_not_equal("world")
```

## Boolean Values

### `is_true()`
Value is exactly `True`.
```python
that(True).is_true()
that(1 == 1).is_true()
```

### `is_false()`
Value is exactly `False`.
```python
that(False).is_false()
that(1 == 2).is_false()
```

### `is_none()`
Value is `None`.
```python
that(None).is_none()
that(function_that_returns_none()).is_none()
```

### `is_not_none()`
Value is not `None`.
```python
that("hello").is_not_none()
that(42).is_not_none()
that([]).is_not_none()  # Empty list is not None
```

## String Assertions

### `contains(substring)`
String contains the given substring.
```python
that("hello world").contains("world")
that("test@example.com").contains("@")
```

### `does_not_contain(substring)`
String does not contain the given substring.
```python
that("hello world").does_not_contain("goodbye")
that("test@example.com").does_not_contain("invalid")
```

### `starts_with(prefix)`
String starts with the given prefix.
```python
that("hello world").starts_with("hello")
that("https://example.com").starts_with("https://")
```

### `ends_with(suffix)`
String ends with the given suffix.
```python
that("hello world").ends_with("world")
that("test.py").ends_with(".py")
```

### `matches(pattern)`
String matches the given regex pattern.
```python
that("test@example.com").matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
that("2024-01-01").matches(r"\d{4}-\d{2}-\d{2}")
```

## Collection Assertions

### `is_empty()`
Collection has no items.
```python
that([]).is_empty()
that("").is_empty()
that({}).is_empty()
that(set()).is_empty()
```

### `has_length(n)`
Collection has exactly n items.
```python
that([1, 2, 3]).has_length(3)
that("hello").has_length(5)
that({"a": 1, "b": 2}).has_length(2)
```

### `contains(item)`
Collection contains the given item.
```python
that([1, 2, 3]).contains(2)
that("hello world").contains("world")
that({"name": "Alice"}).contains("name")  # Dictionary key
```

### `does_not_contain(item)`
Collection does not contain the given item.
```python
that([1, 2, 3]).does_not_contain(4)
that("hello world").does_not_contain("goodbye")
that({"name": "Alice"}).does_not_contain("age")
```

### `all_satisfy(predicate)`
All items in collection satisfy the predicate function.
```python
that([1, 2, 3]).all_satisfy(lambda x: x > 0)
that(["apple", "banana"]).all_satisfy(lambda s: len(s) > 3)
```

### `are_unique()`
All items in collection are unique (no duplicates).
```python
that([1, 2, 3]).are_unique()
that(["a", "b", "c"]).are_unique()

# These would fail:
# that([1, 1, 2]).are_unique()
# that(["a", "a"]).are_unique()
```

### `are_sorted_by(key_func=None)`
Items in collection are sorted by the given key function.
```python
that([1, 2, 3]).are_sorted_by()  # Natural ordering
that(["a", "bb", "ccc"]).are_sorted_by(len)  # Sort by length
that([{"age": 20}, {"age": 25}]).are_sorted_by(lambda x: x["age"])
```

## Number Assertions

### `is_greater_than(value)`
Number is greater than the given value.
```python
that(10).is_greater_than(5)
that(3.14).is_greater_than(3)
```

### `is_less_than(value)`
Number is less than the given value.
```python
that(5).is_less_than(10)
that(2.5).is_less_than(3)
```

### `is_between(min_value, max_value)`
Number is between min and max values (inclusive).
```python
that(5).is_between(1, 10)
that(3.14).is_between(3, 4)
```

### `approximately_equals(value, tolerance=1e-9)`
Number equals value within the given tolerance.
```python
that(3.14159).approximately_equals(3.14, tolerance=0.01)
that(0.1 + 0.2).approximately_equals(0.3, tolerance=1e-10)
```

## Type Assertions

### `is_instance_of(type)`
Value is an instance of the given type (includes subclasses).
```python
that("hello").is_instance_of(str)
that(42).is_instance_of(int)
that([1, 2, 3]).is_instance_of(list)

# Works with inheritance
class Animal: pass
class Dog(Animal): pass

that(Dog()).is_instance_of(Animal)  # True
```

### `has_type(type)`
Value has the exact type (does not include subclasses).
```python
that("hello").has_type(str)
that(42).has_type(int)

# Strict type checking
class Animal: pass
class Dog(Animal): pass

that(Dog()).has_type(Dog)     # True
that(Dog()).has_type(Animal)  # False
```

## Exception Assertions

### `raises(exception_type)`
Function raises the given exception type.
```python
def divide_by_zero():
    return 1 / 0

that(divide_by_zero).raises(ZeroDivisionError)

def validate_age(age):
    if age < 0:
        raise ValueError("Age cannot be negative")
    return age

that(lambda: validate_age(-5)).raises(ValueError)
```

### `does_not_raise()`
Function does not raise any exception.
```python
def safe_function():
    return "success"

result = that(safe_function).does_not_raise()
that(result.value).equals("success")  # Access return value

def add_numbers(a, b):
    return a + b

result = that(lambda: add_numbers(2, 3)).does_not_raise()
that(result.value).equals(5)
```

## Dictionary Assertions

Dictionaries support all collection assertions plus:

### `has_key(key)`
Dictionary contains the given key.
```python
user = {"name": "Alice", "age": 30}
that(user).has_key("name")
that(user).has_key("age")
```

### Dictionary Value Access
```python
user = {"name": "Alice", "age": 30, "address": {"city": "New York"}}

# Access values directly
that(user["name"]).equals("Alice")
that(user["age"]).is_greater_than(18)

# Nested access
that(user["address"]["city"]).equals("New York")

# Check for nested structures
that(user["address"]).has_key("city")
```

## Chaining Assertions

All assertions return `self`, allowing you to chain multiple assertions:

```python
that("hello world") \
    .is_not_none() \
    .is_instance_of(str) \
    .has_length(11) \
    .contains("world") \
    .starts_with("hello") \
    .ends_with("world")

that([1, 2, 3, 4, 5]) \
    .is_not_empty() \
    .has_length(5) \
    .contains(3) \
    .does_not_contain(6) \
    .all_satisfy(lambda x: x > 0) \
    .are_unique()

that(42) \
    .is_not_none() \
    .is_instance_of(int) \
    .is_greater_than(40) \
    .is_less_than(50) \
    .is_between(35, 45)
```

## Error Messages

When assertions fail, you get clear, helpful error messages:

```python
# This assertion fails:
that(5).is_greater_than(10)
```

Error message:
```
that(5).is_greater_than(10)

Expected: number greater than 10
Actual:   5

Value 5 is not greater than 10.
```

```python
# Complex data structures show detailed diffs:
expected = {"name": "Alice", "age": 30}
actual = {"name": "Bob", "age": 25}

that(actual).equals(expected)
```

Error message:
```
that(actual).equals(expected)

Dictionary differences:
  ✗ name: expected 'Alice', got 'Bob'
  ✗ age: expected 30, got 25
```

## Examples by Use Case

### Testing APIs
```python
response = api_client.get("/users/123")

that(response.status_code).equals(200)
that(response.json()) \
    .has_key("id") \
    .has_key("name") \
    .has_key("email")

that(response.json()["email"]).matches(r".+@.+\..+")
```

### Testing Data Processing
```python
numbers = [1, 2, 3, 4, 5]
processed = process_numbers(numbers)

that(processed) \
    .has_length(5) \
    .all_satisfy(lambda x: x > 0) \
    .are_sorted_by() \
    .are_unique()
```

### Testing Business Logic
```python
user = create_user("alice@example.com", age=25)

that(user) \
    .is_not_none() \
    .is_instance_of(User)

that(user.email).equals("alice@example.com")
that(user.age).is_between(18, 120)
that(user.created_at).is_instance_of(datetime)
```

### Testing Error Conditions
```python
# Test that validation works
that(lambda: create_user("invalid-email")).raises(ValueError)
that(lambda: create_user("user@example.com", age=-5)).raises(ValueError)

# Test that valid input doesn't raise
result = that(lambda: create_user("valid@example.com", age=25)).does_not_raise()
that(result.value).is_instance_of(User)
```