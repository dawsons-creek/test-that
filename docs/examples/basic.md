# Basic Examples

This page shows practical examples of using Test That for common testing scenarios.

## Simple Unit Tests

### Testing Functions

```python title="test_math.py"
from that import that, test

def add(a, b):
    return a + b

def multiply(a, b):
    return a * b

@test("addition should work with positive numbers")
def test_addition():
    result = add(2, 3)
    that(result).equals(5)

@test("multiplication should work with zero")
def test_multiply_by_zero():
    result = multiply(5, 0)
    that(result).equals(0)
```

### Testing Classes with @provide Fixtures

```python title="test_calculator.py"
from that import that, test, suite, provide

class Calculator:
    def __init__(self):
        self.value = 0
    
    def add(self, n):
        self.value += n
        return self
    
    def multiply(self, n):
        self.value *= n
        return self
    
    def get_value(self):
        return self.value

with suite("Calculator Tests"):
    
    @provide
    def fresh_calculator():
        """Create a fresh calculator for each test."""
        return Calculator()
    
    @test("should start with zero")
    def test_initial_value():
        # Clear where fresh_calculator comes from - provided above
        that(fresh_calculator.get_value()).equals(0)
    
    @test("should add numbers correctly")
    def test_addition():
        # Each test gets a fresh calculator instance
        fresh_calculator.add(5).add(3)
        that(fresh_calculator.get_value()).equals(8)
    
    @test("should chain operations")
    def test_chaining():
        # Fresh instance again - no state carried over
        fresh_calculator.add(10).multiply(2).add(5)
        that(fresh_calculator.get_value()).equals(25)
```

## String Testing

```python title="test_strings.py"
from that import that, test, suite

with suite("String Operations"):
    
    @test("should validate email format")
    def test_email_validation():
        email = "user@example.com"
        that(email) \
            .contains("@") \
            .contains(".") \
            .does_not_contain(" ") \
            .matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    
    @test("should handle text transformation")
    def test_text_transform():
        text = "Hello World"
        that(text.upper()).equals("HELLO WORLD")
        that(text.lower()).equals("hello world")
        that(text.replace("World", "Python")).equals("Hello Python")
    
    @test("should check string properties")
    def test_string_properties():
        that("hello").has_length(5)
        that("HELLO").is_upper()
        that("hello").is_lower()
        that("Hello World").starts_with("Hello")
        that("Hello World").ends_with("World")
```

## Collection Testing

```python title="test_collections.py"
from that import that, test, suite

with suite("List Operations"):
    
    @test("should handle empty lists")
    def test_empty_list():
        empty_list = []
        that(empty_list).is_empty()
        that(empty_list).has_length(0)
    
    @test("should validate list contents")
    def test_list_contents():
        numbers = [1, 2, 3, 4, 5]
        that(numbers) \
            .is_not_empty() \
            .has_length(5) \
            .contains(3) \
            .does_not_contain(6) \
            .contains_all([1, 3, 5])
    
    @test("should check list properties")
    def test_list_properties():
        even_numbers = [2, 4, 6, 8]
        that(even_numbers).all(lambda x: x % 2 == 0)
        
        mixed_numbers = [1, 2, 3, 4]
        that(mixed_numbers).any(lambda x: x > 3)

with suite("Dictionary Operations"):
    
    @test("should validate dictionary structure")
    def test_dict_structure():
        user = {"name": "Alice", "age": 30, "email": "alice@example.com"}
        
        that(user) \
            .has_key("name") \
            .has_key("age") \
            .has_value("Alice") \
            .contains_subset({"name": "Alice"})
    
    @test("should handle nested dictionaries")
    def test_nested_dict():
        config = {
            "database": {
                "host": "localhost",
                "port": 5432
            },
            "debug": True
        }
        
        that(config).has_key("database")
        that(config["database"]).has_key("host")
        that(config["database"]["port"]).equals(5432)
```

## Error Testing

```python title="test_errors.py"
from that import that, test

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

def validate_age(age):
    if age < 0:
        raise ValueError("Age cannot be negative")
    if age > 150:
        raise ValueError("Age seems unrealistic")
    return age

@test("should raise error on division by zero")
def test_division_by_zero():
    that(lambda: divide(10, 0)).raises(ValueError)

@test("should raise specific error message")
def test_specific_error_message():
    that(lambda: divide(10, 0)).raises(ValueError, "Cannot divide by zero")

@test("should validate age constraints")
def test_age_validation():
    that(lambda: validate_age(-5)).raises(ValueError)
    that(lambda: validate_age(200)).raises(ValueError)
    
    # Valid ages should not raise
    that(validate_age(25)).equals(25)
    that(validate_age(65)).equals(65)
```

## Numeric Testing

```python title="test_numbers.py"
from that import that, test, suite

with suite("Numeric Comparisons"):
    
    @test("should compare integers")
    def test_integer_comparison():
        that(10).is_greater_than(5)
        that(5).is_less_than(10)
        that(7).is_between(5, 10)
    
    @test("should handle floating point")
    def test_floating_point():
        result = 0.1 + 0.2
        that(result).is_close_to(0.3, tolerance=0.0001)
    
    @test("should validate ranges")
    def test_ranges():
        score = 85
        that(score).is_between(0, 100)
        that(score).is_greater_than_or_equal_to(80)
```

## File and Path Testing

```python title="test_files.py"
from that import that, test
import os
import tempfile

@test("should validate file existence")
def test_file_operations():
    # Create a temporary file
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        that(os.path.exists(temp_path)).is_true()
        
        with open(temp_path, 'r') as f:
            content = f.read()
        
        that(content).equals("Hello, World!")
        that(content).has_length(13)
    finally:
        os.unlink(temp_path)
```

## Running These Examples

Save any of these examples to a file starting with `test_` and run:

```bash
that
```

Or run a specific file:

```bash
that test_math.py
```

## Next Steps

- Learn about [advanced testing patterns](advanced.md)
- Explore [real-world examples](real-world.md)
- Check out the [full assertion API](../guide/assertions.md)