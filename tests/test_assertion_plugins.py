"""
Test assertion plugin functionality.
"""

import json
from test_that import test, suite, that


with suite("Assertion Plugin System"):

    @test("assertion plugins are loaded")
    def test_assertion_plugins_loaded():
        """Test that assertion plugins are loaded and available."""
        from test_that.plugins.registry import plugin_registry

        # Should have assertion methods from plugins
        assertion_methods = plugin_registry.get_assertion_methods()
        that(len(assertion_methods)).is_greater_than(0)

    @test("JSON assertion methods are available")
    def test_json_assertion_methods():
        """Test that JSON assertion methods are dynamically added."""
        # These methods should be available from the JSON schema plugin
        test_assertion = that('{"test": "value"}')

        # Check if the methods exist (they should be added dynamically)
        that(hasattr(test_assertion, 'as_json')).is_true()
        that(hasattr(test_assertion, 'matches_schema')).is_true()


with suite("JSON Schema Plugin"):

    @test("as_json parses JSON strings")
    def test_as_json():
        """Test JSON parsing assertion."""
        json_string = '{"name": "John", "age": 30, "active": true}'
        parsed = that(json_string).as_json()

        # Should be able to chain assertions on parsed data
        that(parsed.value).has_key("name")
        that(parsed.value["name"]).equals("John")
        that(parsed.value["age"]).equals(30)
        that(parsed.value["active"]).is_true()

        # Test failure cases
        def invalid_json():
            that("not valid json").as_json()
        that(invalid_json).raises(Exception)

    @test("matches_schema validates JSON schemas")
    def test_matches_schema():
        """Test JSON schema validation."""
        user_data = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com",
            "active": True
        }

        user_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0},
                "email": {"type": "string"},
                "active": {"type": "boolean"}
            },
            "required": ["name", "age"]
        }

        # Should pass validation
        that(user_data).matches_schema(user_schema)

        # Test failure cases
        def invalid_data():
            invalid_user = {"name": "John", "age": -5}  # Negative age
            that(invalid_user).matches_schema(user_schema)
        that(invalid_data).raises(Exception)

    @test("combined JSON parsing and schema validation")
    def test_json_parsing_and_schema():
        """Test combining JSON parsing with schema validation."""
        json_string = '{"name": "Alice", "age": 25, "email": "alice@example.com"}'

        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "age": {"type": "integer", "minimum": 0, "maximum": 150},
                "email": {"type": "string", "pattern": r"^[^@]+@[^@]+\.[^@]+$"}
            },
            "required": ["name", "age", "email"]
        }

        # Parse JSON and validate schema in one chain
        that(json_string).as_json().matches_schema(schema)

    @test("schema validation with arrays")
    def test_schema_validation_arrays():
        """Test schema validation with array data."""
        users_data = [
            {"name": "John", "age": 30},
            {"name": "Jane", "age": 25}
        ]

        users_schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0}
                },
                "required": ["name", "age"]
            },
            "minItems": 1
        }

        that(users_data).matches_schema(users_schema)

    @test("schema validation with enum constraints")
    def test_schema_validation_enum():
        """Test schema validation with enum constraints."""
        status_data = {"status": "active", "priority": "high"}

        status_schema = {
            "type": "object",
            "properties": {
                "status": {"enum": ["active", "inactive", "pending"]},
                "priority": {"enum": ["low", "medium", "high"]}
            }
        }

        that(status_data).matches_schema(status_schema)

        # Test invalid enum value
        def invalid_enum():
            invalid_data = {"status": "unknown"}
            that(invalid_data).matches_schema(status_schema)
        that(invalid_enum).raises(Exception)
