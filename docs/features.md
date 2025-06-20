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

See detailed examples in the complete [Features Guide](https://github.com/dawsons-creek-software/that/blob/main/docs/features.md).