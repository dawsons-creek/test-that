# Test That - Python Testing That Makes Sense

<div align="center" markdown>

![Test That Logo](assets/logo.png){ width="200" }

**A Python testing library that tells you what failed, not makes you guess**

[![PyPI version](https://badge.fury.io/py/test-that.svg)](https://badge.fury.io/py/test-that)
[![Python versions](https://img.shields.io/pypi/pyversions/test-that.svg)](https://pypi.org/project/test-that/)
[![License](https://img.shields.io/pypi/l/test-that.svg)](https://github.com/dawsons-creek/test-that/blob/main/LICENSE)

[Get Started](getting-started/quickstart.md){ .md-button .md-button--primary }
[View on GitHub](https://github.com/dawsons-creek/test-that){ .md-button }

</div>

---

## Why Test That?

Testing should be simple, expressive, and informative. Test That is a modern Python testing framework designed with developer experience in mind.

=== "Clear Assertions"

    ```python
    from that import that, test

    @test("numbers should add correctly")
    def test_addition():
        result = 2 + 2
        that(result).equals(4)
    ```

=== "Helpful Error Messages"

    ```
    ✗ numbers should add correctly
      AssertionError: Expected 5 but got 4
      at test_math.py:6 in test_addition
    ```

=== "Fluent API"

    ```python
    that("hello world").contains("hello").has_length(11)
    that([1, 2, 3]).is_not_empty().all(lambda x: x > 0)
    that({"key": "value"}).has_key("key").has_value("value")
    ```

## Key Features

<div class="grid cards" markdown>

- **Fluent Assertions**  
  Chain assertions naturally with a readable API

- **Clear Error Messages**  
  Know exactly what went wrong and where

- **Zero Configuration**  
  Works out of the box with sensible defaults

- **Beautiful Output**  
  Color-coded results that are easy to scan

- **Smart Discovery**  
  Automatically finds and runs your tests

- **Fast Execution**  
  Minimal overhead for quick feedback

</div>

## Quick Start

### Installation

```bash
pip install test-that
```

### Write Your First Test

```python title="test_example.py"
from that import that, test, suite

with suite("String Operations"):
    
    @test("should handle string concatenation")
    def test_concat():
        result = "Hello" + " " + "World"
        that(result).equals("Hello World")
    
    @test("should convert to uppercase")
    def test_upper():
        that("hello".upper()).equals("HELLO")
```

### Run Your Tests

```bash
that
```

<div class="result" markdown>
```
String Operations
  ✓ should handle string concatenation (0.001s)
  ✓ should convert to uppercase (0.001s)

2 tests passed in 0.002s
```
</div>

## Learn More

<div class="grid cards" markdown>

- **[Getting Started Guide](getting-started/quickstart.md)**  
  Learn the basics in 5 minutes

- **[User Guide](guide/writing-tests.md)**  
  Deep dive into all features

- **[API Reference](api/that.md)**  
  Complete API documentation

- **[Examples](examples/basic.md)**  
  Real-world usage patterns

</div>

## Contributing

We welcome contributions! Check out our [contributing guide](contributing/guidelines.md) to get started.

## License

Test That is MIT licensed. See the [LICENSE](https://github.com/dawsons-creek/test-that/blob/main/LICENSE) file for details.