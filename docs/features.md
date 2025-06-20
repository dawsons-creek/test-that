# Features

## Mocking

Mock object methods and verify calls.

```python
from that import test, that, mock

@test("sends welcome email")  
def test_welcome():
    email_service = EmailService()
    user_service = UserService(email_service)
    
    # Mock the email service
    email_mock = mock(email_service, 'send_email', return_value=True)
    
    # Test the behavior
    user_service.welcome_user("alice@example.com")
    
    # Verify the mock was called
    email_mock.assert_called_once()
    that(email_mock.last_call.args[0]).equals("alice@example.com")
```

## Time Control

Control time for deterministic testing.

```python
from that import test, that, replay
import datetime

@test("user has correct creation timestamp")
@replay.time("2024-01-01T12:00:00Z")
def test_user_timestamp():
    user = create_user("alice@example.com")
    
    expected = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    that(user.created_at).equals(expected)
```

## HTTP Recording

Record and replay HTTP requests for deterministic API testing.

```python
from that import test, that, replay
import requests

@test("fetches user from API")
@replay.http("user_api")
def test_api_call():
    # First run: makes real HTTP call and records response
    # Later runs: replays recorded response (fast & deterministic)
    response = requests.get("https://api.example.com/users/123")
    
    that(response.status_code).equals(200)
    that(response.json()).has_key("name")
```

## JSON & Dictionary Assertions

Test JSON data and nested dictionaries with ease.

```python
from that import test, that

@test("validates complex API response")
def test_api_validation():
    api_response = {
        "status": "success",
        "data": {
            "user": {
                "id": 123,
                "profile": {
                    "name": "Alice",
                    "settings": {"theme": "dark", "notifications": True}
                },
                "roles": ["user", "admin"]
            }
        },
        "metadata": {"version": "1.0", "timestamp": "2024-01-01T12:00:00Z"}
    }
    
    # Test structure and values
    that(api_response).has_keys("status", "data", "metadata")
    that(api_response).has_value("status", "success")
    
    # Test nested paths with dot notation
    that(api_response).path("data.user.id").equals(123)
    that(api_response).path("data.user.profile.name").equals("Alice")
    that(api_response).path("data.user.profile.settings.theme").equals("dark")
    that(api_response).path("data.user.roles[0]").equals("user")
    that(api_response).path("data.user.roles").has_length(2)
    
    # Validate with JSON schema
    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["success", "error"]},
            "data": {
                "type": "object",
                "properties": {
                    "user": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "profile": {"type": "object"},
                            "roles": {"type": "array", "items": {"type": "string"}}
                        },
                        "required": ["id", "profile", "roles"]
                    }
                }
            }
        },
        "required": ["status", "data"]
    }
    that(api_response).matches_schema(schema)

@test("parses and validates JSON strings")
def test_json_parsing():
    json_data = '{"users": [{"name": "Alice"}, {"name": "Bob"}]}'
    
    # Parse JSON and chain assertions
    parsed = that(json_data).as_json()
    parsed.has_key("users")
    parsed.path("users").has_length(2)
    parsed.path("users[0].name").equals("Alice")
    parsed.path("users[1].name").equals("Bob")
```

See detailed examples in the complete [Features Guide](https://github.com/dawsons-creek-software/that/blob/main/docs/features.md).