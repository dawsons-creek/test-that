# HTTP Recording and Replay

Test That includes powerful HTTP recording capabilities that make testing external API integrations deterministic, fast, and reliable. Record real HTTP interactions once, then replay them in tests.

## Why HTTP Recording?

Testing code that makes HTTP requests is challenging:

=== "Without HTTP Recording"
    ```python
    def test_user_api():
        # This test is slow, unreliable, and depends on external service
        response = requests.get("https://api.example.com/users/123")
        assert response.status_code == 200
        assert response.json()["name"] == "John Doe"
        
        # Problems:
        # - Slow (real network call)
        # - Unreliable (network issues, service downtime)
        # - Non-deterministic (data might change)
        # - Requires internet connection
    ```

=== "With Test That HTTP Recording"
    ```python
    from that import that, test, replay
    
    @test("should fetch user from API")
    @replay.http("user_fetch")
    def test_user_api():
        # First run: makes real HTTP call and records it
        # Subsequent runs: replays recorded response (fast & deterministic)
        response = requests.get("https://api.example.com/users/123")
        
        that(response.status_code).equals(200)
        that(response.json()["name"]).equals("John Doe")
        
        # Benefits:
        # - Fast (no network call after first run)
        # - Reliable (always same response)
        # - Deterministic (recorded data never changes)
        # - Works offline
    ```

## Basic HTTP Recording

### Decorator Usage

```python
from that import that, test, replay
import requests

@test("should get user profile")
@replay.http("get_user_profile")
def test_get_user():
    # First run: makes real HTTP request and saves to recordings/get_user_profile.yaml
    # Subsequent runs: replays from recording
    response = requests.get("https://api.example.com/users/123")
    
    that(response.status_code).equals(200)
    that(response.json()) \
        .has_key("id") \
        .has_key("name") \
        .has_key("email")

@test("should create new user")
@replay.http("create_user")
def test_create_user():
    user_data = {"name": "Jane Doe", "email": "jane@example.com"}
    response = requests.post("https://api.example.com/users", json=user_data)
    
    that(response.status_code).equals(201)
    that(response.json()["id"]).is_instance_of(int)
    that(response.json()["name"]).equals("Jane Doe")
```

### Context Manager Usage

```python
@test("multiple API calls in one test")
def test_user_workflow():
    with replay.http("user_workflow"):
        # All HTTP calls within this block are recorded together
        
        # Create user
        create_response = requests.post("https://api.example.com/users", json={
            "name": "John Doe",
            "email": "john@example.com"
        })
        user_id = create_response.json()["id"]
        
        # Fetch user
        get_response = requests.get(f"https://api.example.com/users/{user_id}")
        
        # Update user
        update_response = requests.put(f"https://api.example.com/users/{user_id}", json={
            "name": "John Smith"
        })
        
        # Verify all operations
        that(create_response.status_code).equals(201)
        that(get_response.status_code).equals(200)
        that(update_response.status_code).equals(200)
        that(update_response.json()["name"]).equals("John Smith")
```

## Recording File Structure

HTTP recordings are stored in YAML format for easy inspection and editing:

```
tests/
├── recordings/
│   ├── get_user_profile.yaml
│   ├── create_user.yaml
│   ├── user_workflow.yaml
│   └── api_error_scenarios.yaml
├── test_user_api.py
└── test_integration.py
```

### Recording File Format

```yaml title="recordings/get_user_profile.yaml"
interactions:
- request:
    method: GET
    uri: https://api.example.com/users/123
    headers:
      Accept: application/json
      User-Agent: python-requests/2.28.1
  response:
    status:
      code: 200
      message: OK
    headers:
      Content-Type: application/json
      Content-Length: '156'
    body:
      id: 123
      name: "John Doe"
      email: "john@example.com"
      created_at: "2024-01-01T12:00:00Z"
      verified: true
```

## Advanced Recording Patterns

### Recording Different HTTP Methods

```python
with suite("API CRUD Operations"):
    
    @test("should handle GET requests")
    @replay.http("api_get")
    def test_get_request():
        response = requests.get("https://api.example.com/users/123")
        that(response.status_code).equals(200)
    
    @test("should handle POST requests")
    @replay.http("api_post")
    def test_post_request():
        data = {"name": "New User", "email": "new@example.com"}
        response = requests.post("https://api.example.com/users", json=data)
        that(response.status_code).equals(201)
    
    @test("should handle PUT requests")
    @replay.http("api_put")
    def test_put_request():
        data = {"name": "Updated User"}
        response = requests.put("https://api.example.com/users/123", json=data)
        that(response.status_code).equals(200)
    
    @test("should handle DELETE requests")
    @replay.http("api_delete")
    def test_delete_request():
        response = requests.delete("https://api.example.com/users/123")
        that(response.status_code).equals(204)
```

### Recording with Authentication

```python
@test("should handle authenticated requests")
@replay.http("authenticated_api_call")
def test_authenticated_request():
    headers = {"Authorization": "Bearer your-api-token"}
    response = requests.get("https://api.example.com/protected/data", headers=headers)
    
    that(response.status_code).equals(200)
    that(response.json()).has_key("protected_data")

@test("should handle OAuth flow")
@replay.http("oauth_flow")
def test_oauth_authentication():
    # Token request
    token_response = requests.post("https://api.example.com/oauth/token", data={
        "grant_type": "client_credentials",
        "client_id": "your-client-id",
        "client_secret": "your-client-secret"
    })
    
    token = token_response.json()["access_token"]
    
    # Authenticated API call
    headers = {"Authorization": f"Bearer {token}"}
    api_response = requests.get("https://api.example.com/api/data", headers=headers)
    
    that(token_response.status_code).equals(200)
    that(api_response.status_code).equals(200)
```

### Recording Error Scenarios

```python
with suite("API Error Handling"):
    
    @test("should handle 404 not found")
    @replay.http("user_not_found")
    def test_user_not_found():
        response = requests.get("https://api.example.com/users/99999")
        
        that(response.status_code).equals(404)
        that(response.json()["error"]).equals("User not found")
    
    @test("should handle 400 bad request")
    @replay.http("invalid_user_data")
    def test_invalid_user_data():
        invalid_data = {"email": "not-an-email"}
        response = requests.post("https://api.example.com/users", json=invalid_data)
        
        that(response.status_code).equals(400)
        that(response.json()["errors"]).contains("Invalid email format")
    
    @test("should handle 500 server error")
    @replay.http("server_error")
    def test_server_error():
        response = requests.get("https://api.example.com/users/123")
        
        that(response.status_code).equals(500)
        that(response.json()["error"]).equals("Internal server error")
```

## Recording Modes

### Default Mode (Record Once, Then Replay)

```python
@test("normal recording behavior")
@replay.http("normal_recording")
def test_normal_recording():
    # First run: makes real HTTP call and records
    # Subsequent runs: replays from recording
    response = requests.get("https://api.example.com/users/123")
    that(response.status_code).equals(200)
```

### Force Recording Mode

```python
@test("always make real HTTP calls")
@replay.http("force_record", mode="record")
def test_force_recording():
    # Always makes real HTTP call and overwrites recording
    # Useful when API has changed and you need to update recordings
    response = requests.get("https://api.example.com/users/123")
    that(response.status_code).equals(200)
```

### Replay-Only Mode

```python
@test("never make real HTTP calls")
@replay.http("replay_only", mode="replay_only")
def test_replay_only():
    # Never makes real HTTP calls - fails if recording doesn't exist
    # Useful in CI/CD to ensure no external calls are made
    response = requests.get("https://api.example.com/users/123")
    that(response.status_code).equals(200)
```

## Combining with Time Control

HTTP recording works seamlessly with time control:

```python
@test("API call with timestamp should be deterministic")
@replay(time="2024-01-01T12:00:00Z", http="api_with_timestamp")
def test_api_with_timestamp():
    # Both time is frozen AND HTTP calls are recorded
    response = requests.post("https://api.example.com/events", json={
        "event": "user_login",
        "timestamp": datetime.now().isoformat()
    })
    
    that(response.status_code).equals(201)
    # The timestamp in the request will always be 2024-01-01T12:00:00Z
    # The response will always be the same recorded response
```

## Testing Different HTTP Libraries

Test That's HTTP recording works with popular Python HTTP libraries:

### Requests Library

```python
@test("works with requests library")
@replay.http("requests_example")
def test_with_requests():
    import requests
    response = requests.get("https://api.example.com/data")
    that(response.status_code).equals(200)
```

### HTTPX Library

```python
@test("works with httpx library")
@replay.http("httpx_example")
def test_with_httpx():
    import httpx
    response = httpx.get("https://api.example.com/data")
    that(response.status_code).equals(200)
```

### urllib

```python
@test("works with urllib")
@replay.http("urllib_example")
def test_with_urllib():
    import urllib.request
    response = urllib.request.urlopen("https://api.example.com/data")
    that(response.status).equals(200)
```

## Real-World Integration Testing

### Testing a Service Class

```python
class UserService:
    def __init__(self, api_base_url):
        self.api_base_url = api_base_url
    
    def get_user_profile(self, user_id):
        response = requests.get(f"{self.api_base_url}/users/{user_id}")
        response.raise_for_status()
        return response.json()
    
    def update_user_preferences(self, user_id, preferences):
        response = requests.patch(
            f"{self.api_base_url}/users/{user_id}/preferences",
            json=preferences
        )
        response.raise_for_status()
        return response.json()

@test("user service should fetch and update user data")
@replay.http("user_service_integration")
def test_user_service():
    service = UserService("https://api.example.com")
    
    # Get user profile
    profile = service.get_user_profile(123)
    that(profile) \
        .has_key("id") \
        .has_key("name") \
        .has_key("preferences")
    
    # Update preferences
    new_preferences = {"theme": "dark", "notifications": False}
    updated = service.update_user_preferences(123, new_preferences)
    
    that(updated["preferences"]["theme"]).equals("dark")
    that(updated["preferences"]["notifications"]).is_false()
```

### Testing API Client with Error Handling

```python
class APIClient:
    def __init__(self, base_url, api_key):
        self.base_url = base_url
        self.headers = {"Authorization": f"Bearer {api_key}"}
    
    def make_request(self, method, endpoint, **kwargs):
        url = f"{self.base_url}{endpoint}"
        response = requests.request(method, url, headers=self.headers, **kwargs)
        
        if response.status_code >= 400:
            raise APIError(f"API request failed: {response.status_code}")
        
        return response.json()

class APIError(Exception):
    pass

with suite("API Client Error Handling"):
    
    @test("should handle successful requests")
    @replay.http("api_client_success")
    def test_successful_request():
        client = APIClient("https://api.example.com", "valid-token")
        result = client.make_request("GET", "/users/123")
        
        that(result).has_key("id").has_key("name")
    
    @test("should handle authentication errors")
    @replay.http("api_client_auth_error")
    def test_authentication_error():
        client = APIClient("https://api.example.com", "invalid-token")
        
        that(lambda: client.make_request("GET", "/users/123")) \
            .raises(APIError, "API request failed: 401")
    
    @test("should handle rate limiting")
    @replay.http("api_client_rate_limit")
    def test_rate_limiting():
        client = APIClient("https://api.example.com", "valid-token")
        
        that(lambda: client.make_request("GET", "/users/123")) \
            .raises(APIError, "API request failed: 429")
```

## Managing Recordings

### Recording Organization

```python
# Organize recordings by feature or service
@test("user management features")
@replay.http("user_management/create_user")
def test_create_user():
    pass

@test("payment processing")
@replay.http("payments/process_payment")
def test_payment():
    pass

# This creates:
# recordings/user_management/create_user.yaml
# recordings/payments/process_payment.yaml
```

### Updating Recordings

```python
# When API changes, update recordings by running with record mode
@test("API response format updated")
@replay.http("updated_api_response", mode="record")
def test_updated_api():
    # This will make a real HTTP call and update the recording
    response = requests.get("https://api.example.com/v2/users/123")
    that(response.json()).has_key("new_field")
```

## Best Practices

### 1. Use Descriptive Recording Names
```python
# Good - describes what's being recorded
@replay.http("user_signup_with_email_verification")

# Less descriptive
@replay.http("test1")
```

### 2. Group Related Calls
```python
# Good - complete workflow in one recording
@test("complete user onboarding flow")
@replay.http("user_onboarding_flow")
def test_onboarding():
    # Create account
    # Send verification email
    # Verify email
    # Set up profile
    pass

# Less efficient - separate recordings for each step
@test("create account")
@replay.http("create_account")
def test_create():
    pass

@test("verify email")
@replay.http("verify_email")
def test_verify():
    pass
```

### 3. Test Both Success and Error Cases
```python
with suite("API Error Scenarios"):
    @test("successful user creation")
    @replay.http("user_creation_success")
    def test_success():
        pass
    
    @test("user creation with invalid data")
    @replay.http("user_creation_validation_error")
    def test_validation_error():
        pass
    
    @test("user creation when service is down")
    @replay.http("user_creation_service_error")
    def test_service_error():
        pass
```

### 4. Keep Recordings Up to Date
```python
# Periodically refresh recordings to catch API changes
# Use record mode to update when needed
@test("refresh API recording")
@replay.http("api_endpoint", mode="record")
def test_api_refresh():
    # This updates the recording with current API response
    pass
```

## Configuration Options

### Custom Recording Directory

```python
# Configure in pyproject.toml
[tool.that.replay]
recordings_dir = "tests/fixtures/http_recordings"
```

### Recording Filtering

```python
# Filter sensitive data from recordings
@test("API call with sensitive data")
@replay.http("filtered_api_call", filter_headers=["Authorization"], filter_body=["password"])
def test_with_filtering():
    # Authorization header and password field will be redacted in recording
    pass
```

## Next Steps

- **[Time Control](time-control.md)** - Combine HTTP recording with time freezing
- **[Web API Testing](../examples/web-api-testing.md)** - Complete API testing examples
- **[Integration Patterns](../examples/integration-patterns.md)** - Advanced integration testing
