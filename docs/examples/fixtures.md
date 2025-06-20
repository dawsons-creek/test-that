# Test Fixtures with @provide

Test That provides a clear, explicit way to create test fixtures using the `@provide` decorator. No magic - just simple, readable code.

## Why @provide Over Setup/Teardown

Traditional testing frameworks use "magic" setup/teardown functions:

```python
# ❌ Magic - where does 'db' come from?
with suite("Database Tests"):
    def setup():  # Magic function name
        return create_database()  # Magic return becomes parameter
    
    @test("should save user")
    def test_save_user(db):  # Magic parameter injection
        # Where did 'db' come from? Not clear!
```

Test That uses explicit `@provide` fixtures:

```python
# ✅ Clear and explicit
from that import that, test, suite, provide

with suite("Database Tests"):
    
    @provide
    def mock_database():
        """Create a fresh database for each test."""
        return {"users": [], "next_id": 1}
    
    @test("should save user")
    def test_save_user():
        # Crystal clear where mock_database comes from!
        user = {"id": mock_database["next_id"], "name": "Alice"}
        mock_database["users"].append(user)
        
        that(mock_database["users"]).has_length(1)
```

## Basic Fixture Usage

### Simple Fixtures

```python
from that import that, test, suite, with_

with suite("User Service"):
    
    @with_
    def sample_user():
        return {"name": "John", "email": "john@example.com", "age": 30}
    
    @with_
    def user_service():
        return UserService(database=MockDatabase())
    
    @test("should create user with valid data")
    def test_user_creation():
        # Use fixtures by name - clear and explicit
        created_user = user_service.create(sample_user)
        
        that(created_user["id"]).is_not_none()
        that(created_user["name"]).equals("John")
    
    @test("should validate email format")
    def test_email_validation():
        # Modify fixture data for this specific test
        invalid_user = sample_user.copy()
        invalid_user["email"] = "invalid-email"
        
        that(lambda: user_service.create(invalid_user)).raises(ValueError)
```

### Fresh Instances Per Test

Each test gets a completely fresh instance of every fixture:

```python
with suite("Counter Tests"):
    
    @with_
    def counter():
        return {"value": 0}
    
    @test("should increment")
    def test_increment():
        counter["value"] += 1
        that(counter["value"]).equals(1)
    
    @test("should start fresh")
    def test_fresh_start():
        # This test gets a brand new counter, not the modified one
        that(counter["value"]).equals(0)  # ✅ Passes!
        
        counter["value"] += 5
        that(counter["value"]).equals(5)
    
    @test("isolation is guaranteed")
    def test_isolation():
        # Again, completely fresh counter
        that(counter["value"]).equals(0)  # ✅ Always passes!
```

## Complex Fixture Examples

### Mock API Client

```python
from that import that, test, suite, with_

class MockApiClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.requests = []
    
    def get(self, path):
        self.requests.append(f"GET {path}")
        return {"status": 200, "data": f"Response for {path}"}

with suite("API Integration"):
    
    @with_
    def api_client():
        return MockApiClient("https://api.example.com")
    
    @with_
    def sample_user_data():
        return {
            "users": [
                {"id": 1, "name": "Alice"},
                {"id": 2, "name": "Bob"}
            ]
        }
    
    @test("should fetch user data")
    def test_fetch_users():
        response = api_client.get("/users")
        
        that(response["status"]).equals(200)
        that(api_client.requests).contains("GET /users")
    
    @test("should handle user lookup")
    def test_user_lookup():
        # Fresh api_client for this test
        user_id = sample_user_data["users"][0]["id"]
        response = api_client.get(f"/users/{user_id}")
        
        that(response["status"]).equals(200)
        that(api_client.requests).has_length(1)  # Fresh client, only one request
```

### Database Mocking

```python
with suite("User Repository"):
    
    @with_
    def mock_database():
        return {
            "users": [],
            "next_id": 1,
            "connected": True
        }
    
    @with_
    def user_repository():
        # Fixtures can reference other fixtures
        return UserRepository(database=mock_database)
    
    @test("should save new user")
    def test_save_user():
        user_data = {"name": "Charlie", "email": "charlie@example.com"}
        
        saved_user = user_repository.save(user_data)
        
        that(saved_user["id"]).equals(1)
        that(mock_database["users"]).has_length(1)
        that(mock_database["next_id"]).equals(2)
    
    @test("should find user by id")
    def test_find_user():
        # Pre-populate database for this test
        mock_database["users"].append({"id": 1, "name": "David"})
        
        found_user = user_repository.find_by_id(1)
        
        that(found_user["name"]).equals("David")
    
    @test("should handle database errors")
    def test_database_error():
        # Simulate database disconnection
        mock_database["connected"] = False
        
        that(lambda: user_repository.save({"name": "Eve"})).raises(DatabaseError)
```

### File System Mocking

```python
import tempfile
from pathlib import Path

with suite("File Operations"):
    
    @with_
    def temp_directory():
        """Create a temporary directory for each test."""
        return tempfile.mkdtemp()
    
    @with_
    def sample_file():
        """Create a sample file in the temp directory."""
        file_path = Path(temp_directory) / "sample.txt"
        file_path.write_text("Hello, World!")
        return str(file_path)
    
    @test("should read file contents")
    def test_read_file():
        content = Path(sample_file).read_text()
        that(content).equals("Hello, World!")
    
    @test("should write to file")
    def test_write_file():
        new_file = Path(temp_directory) / "new.txt"
        new_file.write_text("New content")
        
        that(new_file.exists()).is_true()
        that(new_file.read_text()).equals("New content")
    
    @test("directory is fresh each time")
    def test_fresh_directory():
        # Each test gets a clean temp directory
        directory = Path(temp_directory)
        files = list(directory.glob("*"))
        
        # Only sample.txt should exist (created by sample_file fixture)
        that(files).has_length(1)
        that(files[0].name).equals("sample.txt")
```

## Best Practices

### 1. Use Descriptive Names

```python
# ✅ Good - clear what this provides
@with_
def authenticated_user():
    return create_user_with_auth_token()

@with_
def empty_shopping_cart():
    return ShoppingCart()

# ❌ Less clear
@with_
def user():
    return create_user_with_auth_token()

@with_
def cart():
    return ShoppingCart()
```

### 2. Keep Fixtures Simple

```python
# ✅ Good - single responsibility
@with_
def sample_product():
    return {"name": "Widget", "price": 10.99}

@with_
def product_service():
    return ProductService(database=mock_db)

# ❌ Too complex - does too much
@with_
def complete_e_commerce_setup():
    db = setup_database()
    products = create_sample_products()
    users = create_sample_users()
    orders = create_sample_orders()
    return ComplexSetup(db, products, users, orders)
```

### 3. Document Your Fixtures

```python
@with_
def mock_payment_processor():
    """
    Mock payment processor that simulates successful payments.
    
    Returns a PaymentProcessor that:
    - Always returns success for amounts < $1000
    - Simulates network delay of 100ms
    - Tracks all payment attempts
    """
    return MockPaymentProcessor(success_threshold=1000)
```

### 4. Use Fixtures for Data, Not Behavior

```python
# ✅ Good - fixtures provide data/objects
@with_
def user_credentials():
    return {"username": "test@example.com", "password": "secret123"}

@test("should authenticate user")
def test_authentication():
    # Test behavior using fixture data
    result = auth_service.login(user_credentials["username"], user_credentials["password"])
    that(result.success).is_true()

# ❌ Avoid - fixtures shouldn't perform test actions
@with_
def logged_in_user():
    credentials = {"username": "test@example.com", "password": "secret123"}
    return auth_service.login(credentials["username"], credentials["password"])  # Too much!
```

## Migration from Setup/Teardown

If you have existing setup/teardown code, here's how to migrate:

### Before (Magic Setup/Teardown)

```python
with suite("User Tests"):
    def setup():
        return {
            "database": create_test_db(),
            "user_service": UserService(),
            "sample_user": {"name": "Test"}
        }
    
    def teardown(resources):
        resources["database"].close()
    
    @test("should create user")
    def test_create_user(resources):
        user = resources["user_service"].create(resources["sample_user"])
        that(user.id).is_not_none()
```

### After (@with_ Fixtures)

```python
with suite("User Tests"):
    
    @with_
    def test_database():
        # Cleanup happens automatically when test ends
        return create_test_db()
    
    @with_
    def user_service():
        return UserService(database=test_database)
    
    @with_
    def sample_user():
        return {"name": "Test"}
    
    @test("should create user")
    def test_create_user():
        # Clear, explicit - no magic parameters
        user = user_service.create(sample_user)
        that(user.id).is_not_none()
```

The `@with_` system is clearer, more explicit, and easier to understand than magic setup/teardown functions!