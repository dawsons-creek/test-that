# Assertions Guide

Test That provides a fluent, chainable assertion API that makes your tests readable and expressive.

## Basic Assertions

### Equality

```python
that(42).equals(42)
that("hello").equals("hello")
that([1, 2, 3]).equals([1, 2, 3])
```

### Inequality

```python
that(5).does_not_equal(10)
that("hello").is_not("goodbye")
```

## Type Assertions

```python
that(42).is_instance_of(int)
that("hello").is_instance_of(str)
that([1, 2, 3]).is_instance_of(list)
```

## Numeric Assertions

```python
# Comparisons
that(10).is_greater_than(5)
that(5).is_less_than(10)
that(7).is_greater_than_or_equal_to(7)
that(7).is_less_than_or_equal_to(7)

# Ranges
that(5).is_between(1, 10)
that(0.1 + 0.2).is_close_to(0.3, tolerance=0.0001)
```

## String Assertions

```python
# Content checks
that("hello world").contains("world")
that("hello world").does_not_contain("goodbye")
that("hello").starts_with("he")
that("hello").ends_with("lo")

# Pattern matching
that("test@example.com").matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")

# Length
that("hello").has_length(5)

# Case
that("hello").is_lower()
that("HELLO").is_upper()
```

## Collection Assertions

### Lists and Tuples

```python
# Membership
that([1, 2, 3]).contains(2)
that([1, 2, 3]).does_not_contain(4)
that([1, 2, 3]).contains_all([1, 3])
that([1, 2, 3]).contains_any([4, 3])

# Length
that([1, 2, 3]).has_length(3)
that([]).is_empty()
that([1, 2, 3]).is_not_empty()

# Ordering
that([1, 2, 3]).is_sorted()
that([3, 2, 1]).is_sorted(reverse=True)

# Predicates
that([2, 4, 6]).all(lambda x: x % 2 == 0)
that([1, 2, 3]).any(lambda x: x > 2)
that([1, 2, 3]).none(lambda x: x > 5)
```

### Dictionaries

```python
# Keys and values
that({"name": "John"}).has_key("name")
that({"name": "John"}).does_not_have_key("age")
that({"name": "John"}).has_value("John")

# Multiple keys
that({"name": "John", "age": 30}).has_keys(["name", "age"])

# Subsets
that({"a": 1, "b": 2}).contains_subset({"a": 1})
```

### Sets

```python
that({1, 2, 3}).is_subset_of({1, 2, 3, 4, 5})
that({1, 2, 3, 4, 5}).is_superset_of({2, 3})
that({1, 2}).is_disjoint_with({3, 4})
```

## Boolean Assertions

```python
that(True).is_true()
that(False).is_false()
that(1).is_truthy()
that(0).is_falsy()
```

## None Assertions

```python
that(None).is_none()
that("something").is_not_none()
```

## Exception Assertions

```python
# Basic exception checking
that(lambda: 1/0).raises(ZeroDivisionError)

# With exception message
that(lambda: raise_error()).raises(ValueError, "Invalid input")

# Capturing the exception
with that(ValueError) as exc:
    validate_input(-5)
that(exc.value).has_message("Input must be positive")
```

## Chaining Assertions

One of Test That's powerful features is assertion chaining:

```python
that("Hello World") \
    .is_not_none() \
    .is_instance_of(str) \
    .has_length(11) \
    .contains("World") \
    .starts_with("Hello") \
    .does_not_contain("Goodbye")

that([1, 2, 3, 4, 5]) \
    .is_not_empty() \
    .has_length(5) \
    .contains_all([1, 3, 5]) \
    .all(lambda x: x > 0) \
    .is_sorted()
```

## Custom Assertions

You can extend Test That with custom assertions:

```python
from that import that

class CustomAssertions:
    def is_valid_email(self):
        email_pattern = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not re.match(email_pattern, self.value):
            raise AssertionError(f"{self.value} is not a valid email")
        return self

# Usage
that("user@example.com").is_valid_email()
```

## Best Practices

1. **Be Specific**: Use the most specific assertion available
   ```python
   # Good
   that(result).equals(42)
   
   # Less specific
   that(result == 42).is_true()
   ```

2. **Use Descriptive Test Names**: The test name appears in failure messages
   ```python
   @test("user email should be validated before saving")
   def test_email_validation():
       # test code
   ```

3. **Chain Related Assertions**: Group related checks together
   ```python
   that(response) \
       .has_key("status") \
       .has_key("data") \
       .has_value_at("status", 200)
   ```

4. **Leverage Custom Messages**: Add context to assertions
   ```python
   that(user.age).is_greater_than(17).with_message("User must be 18+")
   ```

Next: Learn about [organizing your tests](organization.md)