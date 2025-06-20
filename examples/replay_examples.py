"""
Examples demonstrating the replay system for deterministic testing.

Shows various usage patterns for time freezing and HTTP recording.
"""

import datetime

import requests

from test_that import replay, suite, test, that


# Basic time freezing
@test("time freezing with decorator")
@replay.time("2024-01-01T12:00:00Z")
def test_time_freezing():
    """Test that time is frozen at the specified moment."""
    current_time = datetime.datetime.now()
    expected = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    that(current_time).equals(expected)


# HTTP recording
@test("HTTP recording with decorator")
@replay.http("user_api_call")
def test_http_recording():
    """Test HTTP request recording and replay."""
    response = requests.get("https://jsonplaceholder.typicode.com/users/1")
    that(response.status_code).equals(200)
    user_data = response.json()
    that(user_data).contains("name")
    that(user_data).contains("email")


# Combined time and HTTP
@test("combined time and HTTP recording")
@replay(time="2024-01-01T12:00:00Z", http="user_creation")
def test_combined_replay():
    """Test both time freezing and HTTP recording together."""
    # Time should be frozen
    current_time = datetime.datetime.now()
    expected_time = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    that(current_time).equals(expected_time)

    # HTTP should be recorded
    response = requests.post(
        "https://jsonplaceholder.typicode.com/users",
        json={
            "name": "Test User",
            "email": "test@example.com",
            "created_at": current_time.isoformat()
        }
    )
    that(response.status_code).equals(201)


# Context manager usage
@test("time context manager")
def test_time_context_manager():
    """Test using time freezing as a context manager."""
    with replay.time("2024-06-15T18:30:00Z"):
        frozen_time = datetime.datetime.now()
        expected = datetime.datetime(2024, 6, 15, 18, 30, 0, tzinfo=datetime.timezone.utc)
        that(frozen_time).equals(expected)

    # Time should be unfrozen outside the context
    # (We can't easily test this without mocking, but the concept is demonstrated)


# Nested contexts
@test("nested time contexts")
def test_nested_contexts():
    """Test nested time contexts work correctly."""
    with replay.time("2024-01-01T12:00:00Z"):
        outer_time = datetime.datetime.now()

        with replay.time("2024-12-31T23:59:59Z"):
            inner_time = datetime.datetime.now()

        # Should return to outer context
        back_to_outer = datetime.datetime.now()

    expected_outer = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
    expected_inner = datetime.datetime(2024, 12, 31, 23, 59, 59, tzinfo=datetime.timezone.utc)

    that(outer_time).equals(expected_outer)
    that(inner_time).equals(expected_inner)
    that(back_to_outer).equals(expected_outer)


# Context manager with HTTP decorator
@test("context manager with HTTP decorator")
def test_context_with_http():
    """Test using time context manager with HTTP decorator."""
    with replay.time("2024-01-01T12:00:00Z"):
        @replay.http("api_in_context")
        def make_api_call():
            current_time = datetime.datetime.now()
            response = requests.get("https://jsonplaceholder.typicode.com/posts/1")
            return current_time, response.json()

        time_result, api_result = make_api_call()

        expected_time = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        that(time_result).equals(expected_time)
        that(api_result).contains("title")


# Test suite with shared time context
with suite("User Management Tests"):
    def setup():
        """Setup shared test data."""
        return {
            "test_user": {
                "name": "John Doe",
                "email": "john@example.com"
            }
        }

    # All tests in this context will use the same frozen time
    with replay.time("2024-01-01T12:00:00Z"):
        @test("create user")
        @replay.http("create_user")
        def test_create_user(context):
            """Test user creation with frozen time."""
            user_data = context["test_user"]
            current_time = datetime.datetime.now()

            response = requests.post(
                "https://jsonplaceholder.typicode.com/users",
                json={**user_data, "created_at": current_time.isoformat()}
            )

            that(response.status_code).equals(201)
            created_user = response.json()
            that(created_user).contains("id")

        @test("get user")
        @replay.http("get_user")
        def test_get_user(context):
            """Test user retrieval with frozen time."""
            response = requests.get("https://jsonplaceholder.typicode.com/users/1")
            that(response.status_code).equals(200)

            user = response.json()
            that(user).contains("name")
            that(user).contains("email")


# Different recording modes
@test("HTTP recording in record mode")
@replay.http("force_record", mode="record")
def test_force_record():
    """Test forcing re-recording of HTTP interactions."""
    response = requests.get("https://jsonplaceholder.typicode.com/users/2")
    that(response.status_code).equals(200)


@test("HTTP recording in replay-only mode")
@replay.http("existing_recording", mode="replay_only")
def test_replay_only():
    """Test replay-only mode (will fail if recording doesn't exist)."""
    # This test assumes the recording already exists
    response = requests.get("https://jsonplaceholder.typicode.com/users/1")
    that(response.status_code).equals(200)


# Error handling examples
@test("invalid time format handling")
def test_invalid_time_format():
    """Test that invalid time formats are handled gracefully."""
    def create_invalid_time():
        with replay.time("not-a-valid-date"):
            pass

    that(create_invalid_time).raises(RuntimeError)


# Real-world scenario: API testing with timestamps
@test("API with timestamp validation")
@replay(time="2024-01-01T12:00:00Z", http="timestamp_api")
def test_timestamp_api():
    """Test API that includes timestamps in responses."""
    current_time = datetime.datetime.now()

    # Make API call that might include server timestamp
    response = requests.post(
        "https://jsonplaceholder.typicode.com/posts",
        json={
            "title": "Test Post",
            "body": "This is a test post",
            "client_timestamp": current_time.isoformat()
        }
    )

    that(response.status_code).equals(201)
    post_data = response.json()
    that(post_data).contains("id")
    that(post_data["title"]).equals("Test Post")


# Performance testing scenario
@test("multiple API calls with consistent time")
@replay(time="2024-01-01T12:00:00Z", http="batch_api_calls")
def test_batch_operations():
    """Test multiple API calls with consistent timestamps."""
    base_time = datetime.datetime.now()

    # Simulate batch operations
    results = []
    for i in range(3):
        response = requests.post(
            "https://jsonplaceholder.typicode.com/posts",
            json={
                "title": f"Post {i+1}",
                "body": f"Content for post {i+1}",
                "timestamp": base_time.isoformat()
            }
        )
        results.append(response.json())

    # All posts should have been created with the same timestamp
    that(len(results)).equals(3)
    for i, result in enumerate(results):
        that(result["title"]).equals(f"Post {i+1}")


if __name__ == "__main__":
    print("Run these examples with: that examples/replay_examples.py")
    print("\nAvailable test patterns:")
    print("- @replay.time() - Freeze time")
    print("- @replay.http() - Record/replay HTTP")
    print("- @replay(time=..., http=...) - Combined")
    print("- with replay.time(): - Context manager")
    print("- Nested contexts and test suites")
