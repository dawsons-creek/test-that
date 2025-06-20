"""
Comprehensive showcase of the That testing library plugin system.

This example demonstrates all three types of plugins working together:
- Decorator plugins (replay functionality)
- Assertion plugins (custom assertion methods)
- Lifecycle plugins (test execution hooks)
"""

import datetime
import requests
from test_that import test, suite, that, replay


# Enable lifecycle plugin for this demo
# (You can enable it in pyproject.toml: [tool.that.plugins.lifecycle] enabled = true)

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

    @test("assertion plugin: JSON parsing")
    def test_json_parsing():
        """Demonstrate assertion plugin with JSON parsing."""
        # These methods come from the JSON schema plugin
        json_string = '{"name": "John", "age": 30, "active": true}'
        parsed_data = that(json_string).as_json()

        # Chain assertions on parsed JSON
        that(parsed_data.value).has_key("name")
        that(parsed_data.value["name"]).equals("John")
        that(parsed_data.value["age"]).equals(30)
        that(parsed_data.value["active"]).is_true()

    @test("assertion plugin: JSON schema validation")
    def test_json_schema_validation():
        """Demonstrate assertion plugin with JSON schema validation."""
        user_data = {
            "name": "Alice Smith",
            "age": 28,
            "email": "alice@example.com",
            "preferences": {
                "theme": "dark",
                "notifications": True
            }
        }

        user_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "email": {"type": "string"},
                "preferences": {
                    "type": "object",
                    "properties": {
                        "theme": {"enum": ["light", "dark"]},
                        "notifications": {"type": "boolean"}
                    }
                }
            },
            "required": ["name", "age", "email"]
        }

        # Validate complex nested schema
        that(user_data).matches_schema(user_schema)

    @test("assertion plugin: array schema validation")
    def test_array_schema_validation():
        """Demonstrate assertion plugin with array schema validation."""
        products = [
            {"id": 1, "name": "Laptop", "price": 999.99},
            {"id": 2, "name": "Mouse", "price": 29.99}
        ]

        products_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "integer", "minimum": 1},
                    "name": {"type": "string", "minLength": 1},
                    "price": {"type": "number", "minimum": 0}
                },
                "required": ["id", "name", "price"]
            },
            "minItems": 1
        }

        that(products).matches_schema(products_schema)

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
        
        # Use JSON schema plugin for validation
        post_data = response.json()

        # Validate the response structure
        response_schema = {
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string", "minLength": 1},
                "body": {"type": "string"},
                "timestamp": {"type": "string"}
            },
            "required": ["id", "title"]
        }

        that(post_data).matches_schema(response_schema)

    @test("plugin extensibility demonstration")
    def test_plugin_extensibility():
        """Show how plugins extend the framework capabilities."""
        # Without plugins, you'd need to write custom JSON parsing and validation
        # With plugins, you get powerful JSON schema validation

        api_response = '{"user": {"id": 123, "name": "John Doe", "email": "john@example.com"}, "status": "success"}'

        # Parse JSON and validate complex nested structure
        api_schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "integer", "minimum": 1},
                        "name": {"type": "string", "minLength": 1},
                        "email": {"type": "string", "pattern": r"^[^@]+@[^@]+\.[^@]+$"}
                    },
                    "required": ["id", "name", "email"]
                },
                "status": {"enum": ["success", "error", "pending"]}
            },
            "required": ["user", "status"]
        }

        # Validate using plugin functionality
        that(api_response).as_json().matches_schema(api_schema)

        # Combine with built-in assertions
        parsed = that(api_response).as_json()
        that(parsed.value["user"]["id"]).is_greater_than(0)
        that(parsed.value["status"]).equals("success")

    @test("performance with plugins")
    def test_plugin_performance():
        """Demonstrate that plugins don't significantly impact performance."""
        import time

        start_time = time.perf_counter()

        # Perform multiple JSON operations using plugin methods
        for i in range(50):  # Reduced iterations since JSON parsing is more expensive
            json_data = f'{{"id": {i}, "name": "user{i}", "active": true}}'
            that(json_data).as_json().has_key("id")

            # Schema validation
            simple_schema = {"type": "object", "properties": {"id": {"type": "integer"}}}
            that(json_data).as_json().matches_schema(simple_schema)

        end_time = time.perf_counter()
        duration = end_time - start_time

        # Should complete reasonably quickly even with JSON parsing and validation
        that(duration).is_less_than(1.0)  # Less than 1 second


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
    print("[tool.that.plugins.lifecycle]")
    print("enabled = true")
    print("verbose = true")
    print()
    print("Available plugin assertions:")
    print("- .as_json() - Parse JSON strings into Python objects")
    print("- .matches_schema(schema) - Validate data against JSON schema")
    print("- Supports complex nested schemas with arrays and objects")
    print("- Falls back to built-in validation if jsonschema library not available")
    print("- Demonstrates real-world plugin development patterns")
