# Web API Testing

Learn how to test REST APIs, GraphQL endpoints, and web services using Test That's powerful features. This guide shows real-world patterns you'll use every day.

## Basic API Testing

### Testing REST Endpoints

```python
from that import that, test, suite, mock, replay
import requests

# Example API client
class UserAPI:
    def __init__(self, base_url="https://api.example.com"):
        self.base_url = base_url
    
    def get_user(self, user_id):
        response = requests.get(f"{self.base_url}/users/{user_id}")
        response.raise_for_status()
        return response.json()
    
    def create_user(self, user_data):
        response = requests.post(f"{self.base_url}/users", json=user_data)
        response.raise_for_status()
        return response.json()

with suite("User API Tests"):
    
    @test("should fetch user by ID")
    @replay.http("get_user_123")
    def test_get_user():
        api = UserAPI()
        user = api.get_user(123)
        
        # Test the response structure
        that(user) \
            .has_key("id") \
            .has_key("name") \
            .has_key("email") \
            .has_key("created_at")
        
        # Test specific values
        that(user["id"]).equals(123)
        that(user["email"]).matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
        that(user["created_at"]).is_not_none()
    
    @test("should create user with valid data")
    @replay.http("create_user_success")
    def test_create_user():
        api = UserAPI()
        user_data = {
            "name": "John Doe",
            "email": "john@example.com",
            "role": "user"
        }
        
        created_user = api.create_user(user_data)
        
        # Verify the created user
        that(created_user) \
            .has_key("id") \
            .has_value("name", "John Doe") \
            .has_value("email", "john@example.com") \
            .has_value("role", "user")
        
        # ID should be assigned
        that(created_user["id"]).is_instance_of(int).is_greater_than(0)
```

## Testing with Authentication

### API Key Authentication

```python
class AuthenticatedAPI:
    def __init__(self, api_key, base_url="https://api.example.com"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def get_protected_resource(self, resource_id):
        response = requests.get(
            f"{self.base_url}/protected/{resource_id}",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

@test("should access protected resource with valid API key")
@replay.http("protected_resource_success")
def test_protected_resource_access():
    api = AuthenticatedAPI("valid-api-key-123")
    resource = api.get_protected_resource("resource-456")
    
    that(resource) \
        .has_key("id") \
        .has_key("data") \
        .has_key("permissions")
    
    that(resource["permissions"]).contains("read")

@test("should handle authentication errors")
@replay.http("protected_resource_unauthorized")
def test_authentication_failure():
    api = AuthenticatedAPI("invalid-api-key")
    
    # Should raise an HTTP error for unauthorized access
    that(lambda: api.get_protected_resource("resource-456")) \
        .raises(requests.HTTPError)
```

### OAuth2 Flow Testing

```python
class OAuth2API:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
    
    def get_access_token(self, username, password):
        response = requests.post("https://api.example.com/oauth/token", data={
            "grant_type": "password",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "username": username,
            "password": password
        })
        response.raise_for_status()
        token_data = response.json()
        self.access_token = token_data["access_token"]
        return token_data

@test("should obtain access token with valid credentials")
@replay.http("oauth_token_success")
def test_oauth_token_success():
    api = OAuth2API("client-123", "secret-456")
    token_data = api.get_access_token("user@example.com", "password123")
    
    that(token_data) \
        .has_key("access_token") \
        .has_key("token_type") \
        .has_key("expires_in")
    
    that(token_data["token_type"]).equals("Bearer")
    that(token_data["expires_in"]).is_greater_than(0)
    that(api.access_token).is_not_none()
```

## Error Handling and Edge Cases

### HTTP Status Code Testing

```python
with suite("API Error Handling"):
    
    @test("should handle 404 not found")
    @replay.http("user_not_found")
    def test_user_not_found():
        api = UserAPI()
        
        that(lambda: api.get_user(99999)) \
            .raises(requests.HTTPError)
    
    @test("should handle 400 bad request")
    @replay.http("create_user_bad_request")
    def test_create_user_validation_error():
        api = UserAPI()
        invalid_data = {
            "name": "",  # Empty name
            "email": "not-an-email"  # Invalid email
        }
        
        that(lambda: api.create_user(invalid_data)) \
            .raises(requests.HTTPError)
    
    @test("should handle 500 server error")
    @replay.http("server_error")
    def test_server_error_handling():
        api = UserAPI()
        
        that(lambda: api.get_user(123)) \
            .raises(requests.HTTPError)
```

### Rate Limiting Tests

```python
@test("should handle rate limiting gracefully")
@replay.http("rate_limited_requests")
def test_rate_limiting():
    api = UserAPI()
    
    # Make multiple requests that trigger rate limiting
    results = []
    for i in range(10):
        try:
            user = api.get_user(i + 1)
            results.append(user)
        except requests.HTTPError as e:
            if e.response.status_code == 429:  # Too Many Requests
                # Rate limited - this is expected
                that(e.response.headers).has_key("Retry-After")
                break
            else:
                raise
    
    # Should have gotten some successful responses before rate limiting
    that(results).is_not_empty()
```

## Testing with Time-Sensitive Data

### Combining Time Control with API Testing

```python
@test("should create user with correct timestamp")
@replay(time="2024-01-01T12:00:00Z", http="create_user_with_timestamp")
def test_user_creation_timestamp():
    api = UserAPI()
    user_data = {"name": "John Doe", "email": "john@example.com"}
    
    created_user = api.create_user(user_data)
    
    # With time frozen, we can predict the exact timestamp
    that(created_user["created_at"]).equals("2024-01-01T12:00:00Z")

@test("should handle token expiration")
def test_token_expiration():
    # Create token at specific time
    with replay.time("2024-01-01T12:00:00Z"):
        api = OAuth2API("client-123", "secret-456")
        with replay.http("oauth_token_1hour"):
            token_data = api.get_access_token("user@example.com", "password123")
            that(token_data["expires_in"]).equals(3600)  # 1 hour
    
    # Move forward 30 minutes - token should still be valid
    with replay.time("2024-01-01T12:30:00Z"):
        # Token should still work (test would use recorded response)
        pass
    
    # Move forward 2 hours - token should be expired
    with replay.time("2024-01-01T14:00:00Z"):
        # In real scenario, API would return 401 Unauthorized
        # This would be captured in the HTTP recording
        pass
```

## GraphQL API Testing

```python
class GraphQLAPI:
    def __init__(self, endpoint="https://api.example.com/graphql"):
        self.endpoint = endpoint
    
    def query(self, query, variables=None):
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        
        response = requests.post(self.endpoint, json=payload)
        response.raise_for_status()
        return response.json()

@test("should fetch user with GraphQL query")
@replay.http("graphql_user_query")
def test_graphql_user_query():
    api = GraphQLAPI()
    query = """
        query GetUser($id: ID!) {
            user(id: $id) {
                id
                name
                email
                posts {
                    id
                    title
                    createdAt
                }
            }
        }
    """
    
    result = api.query(query, variables={"id": "123"})
    
    # Test GraphQL response structure
    that(result) \
        .has_key("data") \
        .does_not_have_key("errors")
    
    user = result["data"]["user"]
    that(user) \
        .has_key("id") \
        .has_key("name") \
        .has_key("email") \
        .has_key("posts")
    
    that(user["posts"]).is_instance_of(list)
    if user["posts"]:
        first_post = user["posts"][0]
        that(first_post) \
            .has_key("id") \
            .has_key("title") \
            .has_key("createdAt")

@test("should handle GraphQL errors")
@replay.http("graphql_error_response")
def test_graphql_error_handling():
    api = GraphQLAPI()
    invalid_query = """
        query {
            nonExistentField
        }
    """
    
    result = api.query(invalid_query)
    
    # GraphQL errors are returned in response, not as HTTP errors
    that(result).has_key("errors")
    that(result["errors"]).is_not_empty()
    
    error = result["errors"][0]
    that(error).has_key("message")
    that(error["message"]).contains("Cannot query field")
```

## Testing API Integrations

### Service-to-Service Communication

```python
class OrderService:
    def __init__(self, payment_api, inventory_api, notification_api):
        self.payment_api = payment_api
        self.inventory_api = inventory_api
        self.notification_api = notification_api
    
    def process_order(self, order_data):
        # Check inventory
        item_id = order_data["item_id"]
        quantity = order_data["quantity"]
        
        if not self.inventory_api.check_availability(item_id, quantity):
            raise ValueError("Insufficient inventory")
        
        # Process payment
        payment_result = self.payment_api.charge(
            order_data["payment_method"],
            order_data["amount"]
        )
        
        if not payment_result["success"]:
            raise ValueError("Payment failed")
        
        # Reserve inventory
        self.inventory_api.reserve_items(item_id, quantity)
        
        # Send confirmation
        self.notification_api.send_order_confirmation(
            order_data["customer_email"],
            order_data
        )
        
        return {
            "order_id": payment_result["transaction_id"],
            "status": "confirmed"
        }

@test("should process order successfully")
def test_order_processing():
    # Mock all external services
    payment_api = PaymentAPI()
    inventory_api = InventoryAPI()
    notification_api = NotificationAPI()
    
    # Set up mocks for successful flow
    mock(inventory_api, 'check_availability', return_value=True)
    mock(payment_api, 'charge', return_value={
        "success": True,
        "transaction_id": "txn_123456"
    })
    mock(inventory_api, 'reserve_items', return_value=True)
    mock(notification_api, 'send_order_confirmation', return_value=True)
    
    # Test the service
    service = OrderService(payment_api, inventory_api, notification_api)
    order_data = {
        "item_id": "item_123",
        "quantity": 2,
        "amount": 99.99,
        "payment_method": "card_456",
        "customer_email": "customer@example.com"
    }
    
    result = service.process_order(order_data)
    
    # Verify result
    that(result) \
        .has_key("order_id") \
        .has_key("status") \
        .has_value("status", "confirmed")
    
    # Verify all services were called correctly
    inventory_api.check_availability.assert_called_with("item_123", 2)
    payment_api.charge.assert_called_with("card_456", 99.99)
    inventory_api.reserve_items.assert_called_with("item_123", 2)
    notification_api.send_order_confirmation.assert_called_with(
        "customer@example.com", order_data
    )

@test("should handle payment failure")
def test_payment_failure():
    payment_api = PaymentAPI()
    inventory_api = InventoryAPI()
    notification_api = NotificationAPI()
    
    # Set up mocks - payment fails
    mock(inventory_api, 'check_availability', return_value=True)
    mock(payment_api, 'charge', return_value={
        "success": False,
        "error": "Card declined"
    })
    
    service = OrderService(payment_api, inventory_api, notification_api)
    order_data = {
        "item_id": "item_123",
        "quantity": 1,
        "amount": 50.00,
        "payment_method": "card_declined",
        "customer_email": "customer@example.com"
    }
    
    # Should raise error for payment failure
    that(lambda: service.process_order(order_data)) \
        .raises(ValueError, "Payment failed")
    
    # Should not reserve inventory or send confirmation after payment failure
    inventory_api.reserve_items.assert_not_called()
    notification_api.send_order_confirmation.assert_not_called()
```

## API Response Validation

### Schema Validation

```python
from that import that, test

def validate_user_schema(user):
    """Validate user object matches expected schema."""
    that(user) \
        .is_instance_of(dict) \
        .has_key("id") \
        .has_key("name") \
        .has_key("email") \
        .has_key("created_at")
    
    that(user["id"]).is_instance_of(int).is_greater_than(0)
    that(user["name"]).is_instance_of(str).is_not_empty()
    that(user["email"]).matches(r"^[\w\.-]+@[\w\.-]+\.\w+$")
    that(user["created_at"]).matches(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

@test("API response should match expected schema")
@replay.http("user_list_response")
def test_user_list_schema():
    api = UserAPI()
    response = api.get_users()
    
    that(response) \
        .has_key("users") \
        .has_key("total") \
        .has_key("page")
    
    that(response["users"]).is_instance_of(list)
    that(response["total"]).is_instance_of(int).is_greater_than_or_equal_to(0)
    
    # Validate each user in the list
    for user in response["users"]:
        validate_user_schema(user)
```

## Performance Testing

### Response Time Testing

```python
import time

@test("API should respond quickly")
@replay.http("fast_api_response")
def test_api_performance():
    api = UserAPI()
    
    start_time = time.time()
    user = api.get_user(123)
    end_time = time.time()
    
    response_time = end_time - start_time
    
    # API should respond within 200ms (when using recorded responses, this tests the client code performance)
    that(response_time).is_less_than(0.2)
    that(user).is_not_none()
```

## Best Practices

### 1. Use HTTP Recording for External APIs
```python
# Good - deterministic and fast
@test("should integrate with external service")
@replay.http("external_service_call")
def test_external_integration():
    result = call_external_service()
    that(result).has_key("data")

# Avoid - slow and unreliable
@test("should integrate with external service")
def test_external_integration_live():
    result = call_external_service()  # Makes real HTTP call
    that(result).has_key("data")
```

### 2. Mock Internal Services, Record External APIs
```python
@test("should handle mixed dependencies")
@replay.http("external_api_call")  # Record external API
def test_mixed_dependencies():
    # Mock internal service
    internal_service = InternalService()
    mock(internal_service, 'process_data', return_value={'processed': True})
    
    # External API call will be recorded/replayed
    result = process_with_external_api(internal_service)
    
    that(result).has_key('external_data')
    that(result).has_key('processed')
```

### 3. Test Both Success and Failure Scenarios
```python
with suite("API Error Scenarios"):
    
    @test("should handle network timeout")
    @replay.http("network_timeout")
    def test_network_timeout():
        api = UserAPI()
        that(lambda: api.get_user(123)).raises(requests.Timeout)
    
    @test("should handle malformed response")
    @replay.http("malformed_json")
    def test_malformed_response():
        api = UserAPI()
        that(lambda: api.get_user(123)).raises(requests.JSONDecodeError)
```

### 4. Validate Complete Workflows
```python
@test("complete user registration workflow")
@replay.http("user_registration_flow")
def test_complete_workflow():
    api = UserAPI()
    
    # Step 1: Create user
    user_data = {"name": "John Doe", "email": "john@example.com"}
    user = api.create_user(user_data)
    user_id = user["id"]
    
    # Step 2: Verify user was created
    fetched_user = api.get_user(user_id)
    that(fetched_user["email"]).equals("john@example.com")
    
    # Step 3: Update user
    updated_data = {"name": "John Smith"}
    updated_user = api.update_user(user_id, updated_data)
    that(updated_user["name"]).equals("John Smith")
    
    # Step 4: Delete user
    api.delete_user(user_id)
    that(lambda: api.get_user(user_id)).raises(requests.HTTPError)
```

## Next Steps

- **[Database Testing](database-testing.md)** - Test database integrations
- **[Async Testing](async-testing.md)** - Test async/await patterns
- **[Integration Patterns](integration-patterns.md)** - Advanced integration testing
