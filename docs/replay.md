# Replay Feature - Time and HTTP Control

The `replay` feature provides deterministic control over time and HTTP requests in tests. This is built into the core `that` library because almost every application needs to test time-dependent behavior and external API interactions.

## API Overview

```python
from that import test, that, replay
```

## Three Usage Patterns

### 1. Time Control Only

Use `@replay.time()` when you only need to freeze time:

```python
@test("user created at specific time")
@replay.time("2024-01-01T00:00:00Z")
def test_user_creation():
    user = create_user("john@example.com")
    that(user.created_at).equals(datetime(2024, 1, 1, 0, 0, 0))
    that(user.trial_expires_at).equals(datetime(2024, 1, 31, 0, 0, 0))
```

### 2. HTTP Recording Only

Use `@replay.http()` when you only need to record/replay HTTP requests:

```python
@test("fetches user from API")
@replay.http("user_fetch")
def test_fetch_user():
    # First run: makes real HTTP call and saves to tests/recordings/user_fetch.yaml
    # Subsequent runs: replays from recording
    response = requests.get("https://api.example.com/user/123")
    that(response.json()["name"]).equals("John Doe")
    that(response.status_code).equals(200)
```

### 3. Both Time and HTTP Control

Use `@replay()` with both parameters when you need deterministic time AND HTTP:

```python
@test("complete user signup flow")
@replay(time="2024-01-01T12:00:00Z", http="user_signup")
def test_signup_flow():
    # Time is frozen AND external API calls are recorded/replayed
    response = signup_user("john@example.com")
    user = User.from_api_response(response)
    
    that(user.created_at).equals(datetime(2024, 1, 1, 12, 0, 0))
    that(user.verification_token).equals("abc123")  # From recorded response
    that(user.welcome_email_sent_at).equals(datetime(2024, 1, 1, 12, 0, 1))
```

## File Structure

HTTP recordings are stored in a `recordings` directory:

```
tests/
├── recordings/
│   ├── user_fetch.yaml
│   ├── user_signup.yaml
│   └── payment_process.yaml
├── test_user.py
├── test_auth.py
└── test_payment.py
```

## Recording Format

HTTP recordings are stored in YAML format for readability:

```yaml
# tests/recordings/user_fetch.yaml
interactions:
- request:
    method: GET
    uri: https://api.example.com/user/123
  response:
    status:
      code: 200
    headers:
      content-type: application/json
    body:
      name: John Doe
      email: john@example.com
      created_at: 2024-01-01T00:00:00Z
```

## Advanced Usage

### Shared Time Across Multiple Tests

```python
# Use context manager for multiple tests with same frozen time
with replay.time("2024-01-01T09:00:00Z"):
    @test("morning signup")
    @replay.http("morning_signup")
    def test_morning():
        user = create_user("morning@example.com")
        that(user.created_at.hour).equals(9)
    
    @test("afternoon task")
    @replay.http("afternoon_task")
    def test_afternoon():
        # Still at 9 AM despite test name
        task = schedule_task()
        that(task.scheduled_at.hour).equals(9)
```

### Recording Modes

```python
# Force re-recording (useful when API changes)
@test("fetch updated data")
@replay.http("user_data", mode="record")
def test_force_record():
    # Always makes real HTTP call and overwrites recording
    pass

# Fail if no recording exists (for CI/CD)
@test("fetch cached data")
@replay.http("user_data", mode="replay_only")
def test_replay_only():
    # Fails if recording doesn't exist, never makes real HTTP call
    pass
```

## Why Built-In?

1. **Universal Need**: Nearly every app has timestamps and external API calls
2. **Test Determinism**: Can't have reliable tests without controlling time and HTTP
3. **Single Import**: No need to install and configure separate libraries
4. **Consistent API**: Unified interface for both time and HTTP control

## Implementation Notes

- Time freezing affects all datetime operations within the test
- HTTP recording captures full request/response including headers
- Recordings are human-readable YAML for easy inspection and editing
- Failed HTTP requests are also recorded and replayed
- Supports all common HTTP libraries (requests, httpx, urllib)