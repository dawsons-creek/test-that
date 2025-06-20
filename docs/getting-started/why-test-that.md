# Why Test That?

See how Test That compares to other Python testing frameworks and why developers are switching.

## The Problem with Traditional Testing

Traditional Python testing often looks like this:

=== "unittest"
    ```python
    import unittest
    
    class TestUser(unittest.TestCase):
        def test_user_validation(self):
            user = {"name": "John", "age": 25}
            self.assertEqual(user["name"], "John")
            self.assertIn("age", user)
            self.assertGreater(user["age"], 18)
            
        def test_user_creation_fails(self):
            with self.assertRaises(ValueError):
                create_user("")
    ```

=== "pytest"
    ```python
    import pytest
    
    def test_user_validation():
        user = {"name": "John", "age": 25}
        assert user["name"] == "John"
        assert "age" in user
        assert user["age"] > 18
        
    def test_user_creation_fails():
        with pytest.raises(ValueError):
            create_user("")
    ```

**When these tests fail, you get cryptic messages:**

```
AssertionError: 'Jane' != 'John'
```

or

```
assert 15 > 18
```

**You have to guess what went wrong.**

## The Test That Way

The same tests in Test That:

```python
from that import that, test, suite

with suite("User Validation"):
    
    @test("user should have valid properties")
    def test_user_validation():
        user = {"name": "John", "age": 25}
        that(user["name"]).equals("John")
        that(user).has_key("age")
        that(user["age"]).is_greater_than(18)
    
    @test("user creation should validate input")
    def test_user_creation_fails():
        that(lambda: create_user("")).raises(ValueError)
```

**When Test That tests fail, you get clear messages:**

```
✗ user should have valid properties

  that(user["name"]).equals("John")
  
  Expected: "John"
  Actual:   "Jane"
```

**You know exactly what failed and why.**

## Side-by-Side Comparison

### Error Messages

=== "Test That"
    ```
    ✗ user data should match expected format
    
      that(user).equals(expected_user)
      
      Dictionary differences:
      ✓ email: "john@example.com"
      ✓ name: "John Doe"
      ✗ age: expected 30, got 28
      ✗ verified: expected True, got False
      + unexpected_field: "value" (not in expected)
      - missing_field (expected but not found)
    ```

=== "pytest"
    ```
    >       assert user == expected_user
    E       AssertionError: assert {'age': 28, 'email': 'john@example.com', 'name': 'John Doe', 'unexpected_field': 'value', 'verified': False} == {'age': 30, 'email': 'john@example.com', 'missing_field': 'data', 'name': 'John Doe', 'verified': True}
    E         Omitting 1 identical items, use -vv to show
    E         Differing items:
    E         {'age': 28} != {'age': 30}
    E         {'verified': False} != {'verified': True}
    E         Left contains 1 more item:
    E         {'unexpected_field': 'value'}
    E         Right contains 1 more item:
    E         {'missing_field': 'data'}
    ```

=== "unittest"
    ```
    AssertionError: {'age': 28, 'email': 'john@example.com', 'name': 'John Doe', 'unexpected_field': 'value', 'verified': False} != {'age': 30, 'email': 'john@example.com', 'missing_field': 'data', 'name': 'John Doe', 'verified': True}
    ```

### Fluent Assertions

=== "Test That"
    ```python
    that("user@example.com") \
        .is_not_none() \
        .contains("@") \
        .ends_with(".com") \
        .matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    ```

=== "pytest"
    ```python
    email = "user@example.com"
    assert email is not None
    assert "@" in email
    assert email.endswith(".com")
    assert re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email)
    ```

=== "unittest"
    ```python
    email = "user@example.com"
    self.assertIsNotNone(email)
    self.assertIn("@", email)
    self.assertTrue(email.endswith(".com"))
    self.assertRegex(email, r"^[\w\.-]+@[\w\.-]+\.\w+$")
    ```

### Test Organization

=== "Test That"
    ```python
    with suite("User Management"):
        
        @test("should create user with valid data")
        def test_user_creation():
            user = create_user("john@example.com")
            that(user.email).equals("john@example.com")
        
        @test("should validate email format")
        def test_email_validation():
            that(lambda: create_user("invalid")).raises(ValueError)
    ```

=== "pytest"
    ```python
    class TestUserManagement:
        
        def test_should_create_user_with_valid_data(self):
            user = create_user("john@example.com")
            assert user.email == "john@example.com"
        
        def test_should_validate_email_format(self):
            with pytest.raises(ValueError):
                create_user("invalid")
    ```

=== "unittest"
    ```python
    class TestUserManagement(unittest.TestCase):
        
        def test_should_create_user_with_valid_data(self):
            user = create_user("john@example.com")
            self.assertEqual(user.email, "john@example.com")
        
        def test_should_validate_email_format(self):
            with self.assertRaises(ValueError):
                create_user("invalid")
    ```

## Key Advantages

### 1. **Zero Configuration**
- **Test That**: Works immediately after `pip install test-that`
- **pytest**: Requires configuration for advanced features
- **unittest**: Built-in but verbose and limited

### 2. **Clear Error Messages**
- **Test That**: Intelligent diffing shows exactly what's different
- **pytest**: Better than unittest but still cryptic for complex data
- **unittest**: Minimal error information

### 3. **Fluent API**
- **Test That**: Natural, chainable assertions
- **pytest**: Plain assert statements (simple but limited)
- **unittest**: Verbose method names

### 4. **Built-in Advanced Features**
- **Test That**: Time freezing, HTTP recording, mocking included
- **pytest**: Requires plugins (pytest-freezegun, pytest-vcr, etc.)
- **unittest**: Requires separate libraries

### 5. **Developer Experience**
- **Test That**: Designed for developer happiness
- **pytest**: Good but requires setup and plugins
- **unittest**: Functional but verbose

## Migration Examples

### From pytest

=== "Before (pytest)"
    ```python
    import pytest
    from unittest.mock import patch
    
    def test_user_signup():
        with patch('myapp.send_email') as mock_email:
            user = signup_user("john@example.com")
            assert user.email == "john@example.com"
            mock_email.assert_called_once()
    ```

=== "After (Test That)"
    ```python
    from that import that, test, mock
    
    @test("user signup should send welcome email")
    def test_user_signup():
        email_mock = mock(myapp, 'send_email')
        user = signup_user("john@example.com")
        
        that(user.email).equals("john@example.com")
        email_mock.assert_called_once()
    ```

### From unittest

=== "Before (unittest)"
    ```python
    import unittest
    from unittest.mock import patch
    
    class TestUserSignup(unittest.TestCase):
        
        @patch('myapp.send_email')
        def test_user_signup_sends_email(self, mock_email):
            user = signup_user("john@example.com")
            self.assertEqual(user.email, "john@example.com")
            mock_email.assert_called_once()
    ```

=== "After (Test That)"
    ```python
    from that import that, test, mock
    
    @test("user signup should send welcome email")
    def test_user_signup():
        email_mock = mock(myapp, 'send_email')
        user = signup_user("john@example.com")
        
        that(user.email).equals("john@example.com")
        email_mock.assert_called_once()
    ```

## When to Choose Test That

### ✅ Choose Test That if you want:
- **Clear, readable error messages**
- **Zero configuration setup**
- **Fluent, chainable assertions**
- **Built-in advanced features** (mocking, time control, HTTP recording)
- **Modern Python testing experience**
- **Fast feedback loop**

### 🤔 Consider alternatives if you need:
- **Extensive plugin ecosystem** (pytest has more plugins)
- **Parameterized tests** (Test That prefers explicit tests)
- **Complex fixtures** (Test That uses plain Python functions)
- **Legacy codebase compatibility** (unittest might be easier)

## Developer Testimonials

> "Test That's error messages saved me hours of debugging. I know exactly what failed without digging through stack traces."
> 
> — Sarah Chen, Senior Developer

> "The fluent API makes my tests read like documentation. New team members understand our tests immediately."
> 
> — Marcus Rodriguez, Tech Lead

> "Zero configuration was a game-changer. We were writing tests in minutes, not hours."
> 
> — Jennifer Park, DevOps Engineer

## Try It Yourself

Ready to experience the difference? 

1. **[Install Test That](installation.md)** in 30 seconds
2. **[Write your first test](first-test.md)** and see the clear error messages
3. **[Explore the features](../features/fluent-assertions.md)** that make testing enjoyable

## Migration Support

Need help migrating from another framework?

- **[From pytest](../migration/from-pytest.md)** - Step-by-step migration guide
- **[From unittest](../migration/from-unittest.md)** - Convert your existing tests
- **[Common patterns](../migration/common-patterns.md)** - Pattern translations

The future of Python testing is clear, simple, and developer-friendly. **Welcome to Test That.**
