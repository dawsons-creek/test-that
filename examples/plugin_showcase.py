"""
Comprehensive showcase of the That testing library plugin system.

This example demonstrates all three types of plugins working together:
- Decorator plugins (replay functionality)
- Assertion plugins (custom assertion methods)
- Lifecycle plugins (test execution hooks)
"""

import datetime
import requests
from that import test, suite, that, replay


# Enable lifecycle plugin for this demo
# (You can enable it in pyproject.toml: [tool.that.plugins.example_lifecycle] enabled = true)

with suite("Plugin System Showcase"):
    
    @test("decorator plugin: time freezing")
    @replay.time("2024-01-01T12:00:00Z")
    def test_time_freezing():
        """Demonstrate decorator plugin with time freezing."""
        current_time = datetime.datetime.now()
        
        # Use built-in assertions
        that(current_time.year).equals(2024)
        that(current_time.month).equals(1)
        that(current_time.day).equals(1)
        that(current_time.hour).equals(12)

    @test("decorator plugin: HTTP recording")
    @replay.http("plugin_demo_api")
    def test_http_recording():
        """Demonstrate decorator plugin with HTTP recording."""
        response = requests.get("https://jsonplaceholder.typicode.com/users/1")
        
        # Use built-in assertions
        that(response.status_code).equals(200)
        that(response.json()).has_key("name")
        that(response.json()).has_key("email")

    @test("assertion plugin: email validation")
    def test_email_validation():
        """Demonstrate assertion plugin with email validation."""
        # These methods come from the example assertion plugin
        that("user@example.com").is_email()
        that("test.email+tag@domain.co.uk").is_email()
        that("admin@company.org").is_email()
        
        # Test invalid emails
        def invalid_email():
            that("not-an-email").is_email()
        that(invalid_email).raises(Exception)

    @test("assertion plugin: URL validation")
    def test_url_validation():
        """Demonstrate assertion plugin with URL validation."""
        that("https://example.com").is_url()
        that("http://test.org/path?query=value").is_url()
        that("https://api.github.com/repos/user/repo").is_url()
        
        # Test invalid URLs
        def invalid_url():
            that("not-a-url").is_url()
        that(invalid_url).raises(Exception)

    @test("assertion plugin: number validation")
    def test_number_validation():
        """Demonstrate assertion plugin with number validation."""
        # Positive numbers
        that(5).is_positive()
        that(3.14).is_positive()
        that(100).is_positive()
        
        # Even/odd numbers
        that(2).is_even()
        that(0).is_even()
        that(-4).is_even()
        
        that(1).is_odd()
        that(3).is_odd()
        that(-5).is_odd()

    @test("assertion plugin: length validation")
    def test_length_validation():
        """Demonstrate assertion plugin with length validation."""
        that("hello").has_length_between(3, 10)
        that([1, 2, 3]).has_length_between(2, 5)
        that({"a": 1, "b": 2}).has_length_between(1, 3)
        that("test").has_length_between(4, 4)  # Exact length

    @test("combined plugins: time + HTTP + assertions")
    @replay(time="2024-06-15T14:30:00Z", http="combined_demo")
    def test_combined_functionality():
        """Demonstrate all plugin types working together."""
        # Time is frozen (decorator plugin)
        current_time = datetime.datetime.now()
        that(current_time.year).equals(2024)
        that(current_time.month).equals(6)
        
        # HTTP is recorded (decorator plugin)
        response = requests.post(
            "https://jsonplaceholder.typicode.com/posts",
            json={
                "title": "Plugin Demo",
                "body": "Testing all plugin types together",
                "timestamp": current_time.isoformat()
            }
        )
        
        # Use built-in assertions
        that(response.status_code).equals(201)
        that(response.json()).has_key("id")
        
        # Use plugin assertions
        post_data = response.json()
        that(post_data["title"]).has_length_between(5, 20)
        
        # Validate the timestamp format (should be ISO format)
        timestamp = post_data.get("timestamp", "")
        that(len(timestamp)).is_greater_than(10)  # ISO timestamps are long

    @test("plugin extensibility demonstration")
    def test_plugin_extensibility():
        """Show how plugins extend the framework capabilities."""
        # Without plugins, you'd need to write custom validation logic
        # With plugins, you get domain-specific assertions
        
        user_data = {
            "email": "john.doe@company.com",
            "website": "https://johndoe.dev",
            "age": 28,
            "id": 12345
        }
        
        # Validate using plugin assertions
        that(user_data["email"]).is_email()
        that(user_data["website"]).is_url()
        that(user_data["age"]).is_positive()
        that(user_data["age"]).is_even()
        
        # Combine with built-in assertions
        that(user_data).has_key("id")
        that(user_data["id"]).is_greater_than(0)

    @test("performance with plugins")
    def test_plugin_performance():
        """Demonstrate that plugins don't significantly impact performance."""
        import time
        
        start_time = time.perf_counter()
        
        # Perform multiple assertions using plugin methods
        for i in range(100):
            that(f"user{i}@example.com").is_email()
            that(i).is_even() if i % 2 == 0 else that(i).is_odd()
            that(f"test{i}").has_length_between(5, 10)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Should complete quickly even with plugin assertions
        that(duration).is_less_than(0.1)  # Less than 100ms


# Lifecycle plugin will track all these tests if enabled
# It will show:
# - Total test count
# - Suite count  
# - Any failed tests
# - Slow tests (if any exceed the threshold)

if __name__ == "__main__":
    print("🔌 Plugin System Showcase")
    print("=" * 50)
    print()
    print("This example demonstrates:")
    print("✨ Decorator plugins (time freezing & HTTP recording)")
    print("🔍 Assertion plugins (custom validation methods)")
    print("📊 Lifecycle plugins (test execution tracking)")
    print()
    print("Run with: uv run python -m that examples/plugin_showcase.py")
    print()
    print("To enable lifecycle plugin output, add to pyproject.toml:")
    print("[tool.that.plugins.example_lifecycle]")
    print("enabled = true")
    print("verbose = true")
    print()
    print("Available plugin assertions:")
    print("- .is_email() - Validate email addresses")
    print("- .is_url() - Validate URLs")
    print("- .is_positive() - Check positive numbers")
    print("- .is_even() / .is_odd() - Check even/odd numbers")
    print("- .has_length_between(min, max) - Validate length ranges")
