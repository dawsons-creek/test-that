# Mocking System

Test That includes a powerful, built-in mocking system that makes testing dependencies simple and clear. No need for external libraries or complex setup.

## Why Built-in Mocking?

Most Python testing requires external mocking libraries:

=== "Traditional Approach"
    ```python
    from unittest.mock import patch, Mock
    import pytest
    
    @patch('myapp.database.query')
    @patch('myapp.email.send')
    def test_user_signup(mock_send, mock_query):
        mock_query.return_value = []
        mock_send.return_value = True
        
        result = signup_user("john@example.com")
        
        assert result.email == "john@example.com"
        mock_query.assert_called_once()
        mock_send.assert_called_once()
    ```

=== "Test That Approach"
    ```python
    from that import that, test, mock
    
    @test("user signup should work correctly")
    def test_user_signup():
        query_mock = mock(database, 'query', return_value=[])
        email_mock = mock(email_service, 'send', return_value=True)
        
        result = signup_user("john@example.com")
        
        that(result.email).equals("john@example.com")
        query_mock.assert_called_once()
        email_mock.assert_called_once()
    ```

**Test That's mocking is cleaner, more explicit, and automatically cleans up after each test.**

## Basic Mocking

### Simple Method Mocking

```python
from that import that, test, mock

class DatabaseService:
    def get_user(self, user_id):
        # This would normally hit a real database
        raise RuntimeError("Should not call real database in tests")

@test("should mock database calls")
def test_database_mocking():
    db = DatabaseService()
    
    # Mock the method to return test data
    user_mock = mock(db, 'get_user', return_value={'id': 1, 'name': 'John'})
    
    # Call the mocked method
    result = db.get_user(123)
    
    # Verify the result and call
    that(result).equals({'id': 1, 'name': 'John'})
    user_mock.assert_called_with(123)
```

### Return Values

```python
@test("mock can return different values")
def test_return_values():
    service = ApiService()
    
    # Simple return value
    mock(service, 'get_data', return_value={'status': 'success'})
    that(service.get_data()).equals({'status': 'success'})
    
    # Return None
    mock(service, 'delete_item', return_value=None)
    that(service.delete_item(123)).is_none()
    
    # Return complex objects
    user = User(name="John", email="john@example.com")
    mock(service, 'create_user', return_value=user)
    that(service.create_user("John")).equals(user)
```

### Raising Exceptions

```python
@test("mock can raise exceptions")
def test_exception_mocking():
    service = ApiService()
    
    # Mock to raise an exception
    mock(service, 'get_data', raises=ConnectionError("Network unavailable"))
    
    # Test that the exception is raised
    that(lambda: service.get_data()).raises(ConnectionError, "Network unavailable")
```

## Advanced Mocking Patterns

### Side Effects with Lists

```python
@test("mock can return different values on successive calls")
def test_side_effect_list():
    service = ApiService()
    
    # Return different values for each call
    mock(service, 'get_next_id', side_effect=[1, 2, 3, 4])
    
    that(service.get_next_id()).equals(1)
    that(service.get_next_id()).equals(2)
    that(service.get_next_id()).equals(3)
    that(service.get_next_id()).equals(4)
    
    # After exhausting the list, raises ValueError
    that(lambda: service.get_next_id()).raises(ValueError)
```

### Side Effects with Functions

```python
@test("mock can use dynamic side effects")
def test_side_effect_function():
    service = UserService()
    
    def dynamic_user_lookup(user_id):
        if user_id == 1:
            return {'id': 1, 'name': 'Admin', 'role': 'admin'}
        elif user_id == 2:
            return {'id': 2, 'name': 'User', 'role': 'user'}
        else:
            raise ValueError(f"User {user_id} not found")
    
    mock(service, 'get_user', side_effect=dynamic_user_lookup)
    
    # Test different scenarios
    admin = service.get_user(1)
    that(admin['role']).equals('admin')
    
    user = service.get_user(2)
    that(user['role']).equals('user')
    
    that(lambda: service.get_user(999)).raises(ValueError, "User 999 not found")
```

### Mocking Properties and Attributes

```python
@test("can mock object attributes")
def test_attribute_mocking():
    config = ConfigService()
    
    # Mock a property
    mock(config, 'database_url', return_value='sqlite:///:memory:')
    mock(config, 'debug_mode', return_value=True)
    
    that(config.database_url).equals('sqlite:///:memory:')
    that(config.debug_mode).is_true()
```

## Call Verification

### Basic Call Assertions

```python
@test("verify mock was called correctly")
def test_call_verification():
    service = EmailService()
    email_mock = mock(service, 'send_email', return_value=True)
    
    # Make some calls
    service.send_email('john@example.com', 'Welcome!', body='Hello John')
    service.send_email('jane@example.com', 'Update', body='Hi Jane')
    
    # Verify call count
    that(email_mock.call_count).equals(2)
    
    # Verify specific calls
    email_mock.assert_called_with('jane@example.com', 'Update', body='Hi Jane')  # Last call
    email_mock.assert_called_times(2)
```

### Advanced Call Verification

```python
@test("verify complex call patterns")
def test_advanced_call_verification():
    service = DatabaseService()
    query_mock = mock(service, 'execute_query', return_value=[])
    
    # Make various calls
    service.execute_query('SELECT * FROM users')
    service.execute_query('SELECT * FROM posts WHERE user_id = ?', 123)
    service.execute_query('UPDATE users SET active = ? WHERE id = ?', True, 456)
    
    # Verify first and last calls
    that(query_mock.first_call.args).equals(('SELECT * FROM users',))
    that(query_mock.last_call.args).equals(('UPDATE users SET active = ? WHERE id = ?', True, 456))
    
    # Verify specific call by index
    second_call = query_mock.get_call(1)
    that(second_call.args).equals(('SELECT * FROM posts WHERE user_id = ?', 123))
    
    # Verify call was made with specific arguments
    query_mock.assert_any_call('SELECT * FROM users')
    query_mock.assert_any_call('SELECT * FROM posts WHERE user_id = ?', 123)
```

### Call History and Inspection

```python
@test("inspect call history")
def test_call_history():
    service = LoggingService()
    log_mock = mock(service, 'log', return_value=None)
    
    # Make calls with different arguments
    service.log('INFO', 'Application started')
    service.log('ERROR', 'Database connection failed', extra={'retry': True})
    service.log('DEBUG', 'Processing user request', user_id=123)
    
    # Inspect all calls
    that(log_mock.calls).has_length(3)
    
    # Check specific call details
    first_call = log_mock.calls[0]
    that(first_call.args).equals(('INFO', 'Application started'))
    that(first_call.kwargs).equals({})
    
    second_call = log_mock.calls[1]
    that(second_call.args).equals(('ERROR', 'Database connection failed'))
    that(second_call.kwargs).equals({'extra': {'retry': True}})
    
    third_call = log_mock.calls[2]
    that(third_call.kwargs).has_key('user_id')
    that(third_call.kwargs['user_id']).equals(123)
```

## Integration with Test That Assertions

### Using mock_that() for Fluent Assertions

```python
from that import that, test, mock, mock_that

@test("mock_that provides fluent mock assertions")
def test_mock_that_integration():
    service = ApiService()
    api_mock = mock(service, 'fetch_data', return_value={'data': 'test'})
    
    # Make some calls
    service.fetch_data('/users')
    service.fetch_data('/posts', limit=10)
    
    # Use mock_that for fluent assertions
    mock_assertions = mock_that(api_mock)
    
    that(mock_assertions.call_count).equals(2)
    that(mock_assertions.calls).has_length(2)
    that(mock_assertions.first_call.args).contains('/users')
    that(mock_assertions.last_call.kwargs).has_key('limit')
    that(mock_assertions.last_call.kwargs['limit']).equals(10)
```

## Real-World Examples

### Testing a User Service

```python
from that import that, test, suite, mock

class UserService:
    def __init__(self, db, email_service, logger):
        self.db = db
        self.email_service = email_service
        self.logger = logger
    
    def create_user(self, email, name):
        # Check if user exists
        existing = self.db.find_user_by_email(email)
        if existing:
            raise ValueError("User already exists")
        
        # Create user
        user_id = self.db.create_user({'email': email, 'name': name})
        user = self.db.get_user(user_id)
        
        # Send welcome email
        self.email_service.send_welcome_email(user['email'], user['name'])
        
        # Log the creation
        self.logger.info(f"Created user {user_id}")
        
        return user

with suite("User Service Tests"):
    
    @test("should create new user successfully")
    def test_create_user_success():
        # Set up mocks
        db_mock = DatabaseService()
        email_mock = EmailService()
        logger_mock = Logger()
        
        mock(db_mock, 'find_user_by_email', return_value=None)
        mock(db_mock, 'create_user', return_value=123)
        mock(db_mock, 'get_user', return_value={'id': 123, 'email': 'john@example.com', 'name': 'John'})
        mock(email_mock, 'send_welcome_email', return_value=True)
        mock(logger_mock, 'info', return_value=None)
        
        # Test the service
        service = UserService(db_mock, email_mock, logger_mock)
        result = service.create_user('john@example.com', 'John')
        
        # Verify result
        that(result).has_key('id').has_key('email').has_key('name')
        that(result['email']).equals('john@example.com')
        
        # Verify all dependencies were called correctly
        db_mock.find_user_by_email.assert_called_with('john@example.com')
        db_mock.create_user.assert_called_with({'email': 'john@example.com', 'name': 'John'})
        email_mock.send_welcome_email.assert_called_with('john@example.com', 'John')
        logger_mock.info.assert_called_with('Created user 123')
    
    @test("should handle existing user error")
    def test_create_user_already_exists():
        # Set up mocks
        db_mock = DatabaseService()
        email_mock = EmailService()
        logger_mock = Logger()
        
        # Mock existing user
        existing_user = {'id': 456, 'email': 'john@example.com', 'name': 'Existing John'}
        mock(db_mock, 'find_user_by_email', return_value=existing_user)
        
        service = UserService(db_mock, email_mock, logger_mock)
        
        # Should raise error for existing user
        that(lambda: service.create_user('john@example.com', 'John')).raises(ValueError, "User already exists")
        
        # Should not attempt to create or send email
        db_mock.find_user_by_email.assert_called_once()
        # Verify create_user was never called (no mock set up for it)
```

## Mock Cleanup and Isolation

Test That automatically cleans up mocks between tests:

```python
with suite("Mock Cleanup Tests"):
    
    @test("first test sets up mock")
    def test_first():
        service = ApiService()
        mock(service, 'get_data', return_value='mocked')
        that(service.get_data()).equals('mocked')
    
    @test("second test has clean slate")
    def test_second():
        service = ApiService()
        # Mock from previous test is automatically cleaned up
        # This will call the real method (or raise if not implemented)
        try:
            result = service.get_data()
            # If real method exists, test its behavior
        except NotImplementedError:
            # Expected if method is not implemented
            pass
```

## Best Practices

### 1. Mock at the Right Level
```python
# Good - mock the direct dependency
@test("user service should send welcome email")
def test_user_service():
    email_service = EmailService()
    mock(email_service, 'send_email', return_value=True)
    
    user_service = UserService(email_service)
    user_service.create_user('john@example.com')
    
    email_service.send_email.assert_called_once()

# Less ideal - mocking too deep in the stack
@test("user service test")
def test_user_service_deep_mock():
    # Don't mock internal SMTP details, mock the service interface
    pass
```

### 2. Use Descriptive Return Values
```python
# Good - realistic test data
mock(user_service, 'get_user', return_value={
    'id': 123,
    'name': 'John Doe',
    'email': 'john@example.com',
    'created_at': '2024-01-01T00:00:00Z'
})

# Less helpful - minimal data
mock(user_service, 'get_user', return_value={'id': 1})
```

### 3. Verify Important Interactions
```python
@test("should log important events")
def test_logging():
    logger = Logger()
    log_mock = mock(logger, 'info', return_value=None)
    
    service = ImportantService(logger)
    service.do_critical_operation()
    
    # Verify the important event was logged
    log_mock.assert_called_with('Critical operation completed successfully')
```

### 4. Test Error Scenarios
```python
@test("should handle service failures gracefully")
def test_service_failure():
    external_service = ExternalService()
    mock(external_service, 'call_api', raises=ConnectionError("Service unavailable"))
    
    our_service = OurService(external_service)
    result = our_service.get_data_with_fallback()
    
    # Should handle the error and provide fallback
    that(result).has_key('error')
    that(result['error']).equals('Service temporarily unavailable')
```

## Next Steps

- **[Time Control](time-control.md)** - Learn about time freezing and replay
- **[HTTP Recording](http-recording.md)** - Record and replay HTTP interactions
- **[Real Examples](../examples/web-api-testing.md)** - See mocking in action with real applications
