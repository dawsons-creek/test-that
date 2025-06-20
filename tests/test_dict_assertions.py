"""Tests for dictionary and JSON assertions."""

from that import test, suite, that


with suite("Dictionary Key Assertions"):
    
    @test("has_key checks for key existence")
    def test_has_key():
        user = {"name": "Alice", "age": 30}
        that(user).has_key("name")
        that(user).has_key("age")
    
    @test("has_key fails when key missing")
    def test_has_key_missing():
        user = {"name": "Alice"}
        that(lambda: that(user).has_key("age")).raises(AssertionError)
    
    @test("has_key fails on non-dict")
    def test_has_key_non_dict():
        that(lambda: that("string").has_key("x")).raises(AssertionError)
    
    @test("has_keys checks multiple keys")
    def test_has_keys():
        user = {"name": "Alice", "age": 30, "email": "alice@example.com"}
        that(user).has_keys("name", "age", "email")
    
    @test("has_keys fails when any key missing")
    def test_has_keys_missing():
        user = {"name": "Alice", "age": 30}
        that(lambda: that(user).has_keys("name", "email")).raises(AssertionError)
    
    @test("has_value checks key and value")
    def test_has_value():
        user = {"name": "Alice", "age": 30}
        that(user).has_value("name", "Alice")
        that(user).has_value("age", 30)
    
    @test("has_value fails when value wrong")
    def test_has_value_wrong():
        user = {"name": "Alice", "age": 30}
        that(lambda: that(user).has_value("name", "Bob")).raises(AssertionError)


with suite("Nested Path Assertions"):
    
    @test("has_path checks nested existence")
    def test_has_path():
        data = {
            "user": {
                "name": "Alice",
                "address": {
                    "city": "NYC",
                    "zip": "10001"
                }
            }
        }
        that(data).has_path("user")
        that(data).has_path("user.name")
        that(data).has_path("user.address")
        that(data).has_path("user.address.city")
    
    @test("has_path fails when path missing")
    def test_has_path_missing():
        data = {"user": {"name": "Alice"}}
        that(lambda: that(data).has_path("user.age")).raises(AssertionError)
        that(lambda: that(data).has_path("missing.path")).raises(AssertionError)
    
    @test("path returns nested value assertion")
    def test_path():
        data = {
            "user": {
                "name": "Alice",
                "address": {
                    "city": "NYC",
                    "zip": "10001"
                }
            }
        }
        that(data).path("user.name").equals("Alice")
        that(data).path("user.address.city").equals("NYC")
        that(data).path("user.address.zip").equals("10001")
    
    @test("path works with arrays")
    def test_path_arrays():
        data = {
            "users": [
                {"name": "Alice", "age": 30},
                {"name": "Bob", "age": 25}
            ]
        }
        that(data).path("users[0].name").equals("Alice")
        that(data).path("users[1].age").equals(25)


with suite("JSON Assertions"):
    
    @test("as_json parses JSON string")
    def test_as_json():
        json_str = '{"name": "Alice", "age": 30}'
        that(json_str).as_json().has_key("name")
        that(json_str).as_json().has_value("name", "Alice")
    
    @test("as_json fails on invalid JSON")
    def test_as_json_invalid():
        invalid_json = '{"name": "Alice", "age":}'
        that(lambda: that(invalid_json).as_json()).raises(AssertionError)
    
    @test("as_json fails on non-string")
    def test_as_json_non_string():
        that(lambda: that({"name": "Alice"}).as_json()).raises(AssertionError)
    
    @test("nested JSON parsing")
    def test_nested_json():
        json_str = '{"user": {"name": "Alice", "address": {"city": "NYC"}}}'
        that(json_str).as_json().path("user.name").equals("Alice")
        that(json_str).as_json().path("user.address.city").equals("NYC")


with suite("Schema Validation"):
    
    @test("matches_schema validates basic types")
    def test_schema_basic_types():
        # String schema
        that("hello").matches_schema({"type": "string"})
        
        # Number schema
        that(42).matches_schema({"type": "integer"})
        that(3.14).matches_schema({"type": "number"})
        
        # Boolean schema
        that(True).matches_schema({"type": "boolean"})
        
        # Array schema
        that([1, 2, 3]).matches_schema({"type": "array"})
    
    @test("matches_schema validates object properties")
    def test_schema_object():
        user = {"name": "Alice", "age": 30, "email": "alice@example.com"}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"},
                "email": {"type": "string"}
            },
            "required": ["name", "email"]
        }
        that(user).matches_schema(schema)
    
    @test("matches_schema fails on missing required")
    def test_schema_missing_required():
        user = {"name": "Alice"}  # Missing required email
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "email": {"type": "string"}
            },
            "required": ["name", "email"]
        }
        that(lambda: that(user).matches_schema(schema)).raises(AssertionError)
    
    @test("matches_schema validates nested objects")
    def test_schema_nested():
        data = {
            "user": {
                "name": "Alice",
                "address": {
                    "city": "NYC",
                    "zip": "10001"
                }
            }
        }
        schema = {
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "address": {
                            "type": "object",
                            "properties": {
                                "city": {"type": "string"},
                                "zip": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
        that(data).matches_schema(schema)
    
    @test("matches_schema validates arrays")
    def test_schema_arrays():
        users = [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
        schema = {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer"}
                },
                "required": ["name", "age"]
            }
        }
        that(users).matches_schema(schema)


with suite("Structure Validation"):
    
    @test("has_structure validates types")
    def test_structure_validation():
        user = {"name": "Alice", "age": 30, "active": True}
        expected = {
            "name": str,
            "age": int,
            "active": bool
        }
        that(user).has_structure(expected)
    
    @test("has_structure fails on wrong types")
    def test_structure_wrong_type():
        user = {"name": "Alice", "age": "30"}  # age should be int
        expected = {"name": str, "age": int}
        that(lambda: that(user).has_structure(expected)).raises(AssertionError)
    
    @test("has_structure fails on missing keys")
    def test_structure_missing_keys():
        user = {"name": "Alice"}  # missing age
        expected = {"name": str, "age": int}
        that(lambda: that(user).has_structure(expected)).raises(AssertionError)


with suite("Enhanced Path Navigation"):

    @test("path handles negative array indices")
    def test_path_negative_indices():
        data = {"items": [1, 2, 3, 4, 5]}
        that(data).path("items[-1]").equals(5)
        that(data).path("items[-2]").equals(4)

    @test("path provides detailed error context")
    def test_path_detailed_errors():
        data = {"user": {"profile": {"settings": {}}}}
        that(lambda: that(data).path("user.profile.preferences.theme")).raises(AssertionError)

        # Test malformed array index
        data_with_array = {"items": [1, 2, 3]}
        that(lambda: that(data_with_array).path("items[abc]")).raises(AssertionError)

        # Test out of bounds
        that(lambda: that(data_with_array).path("items[10]")).raises(AssertionError)

    @test("path handles complex nested structures")
    def test_path_complex_nesting():
        data = {
            "api": {
                "v1": {
                    "endpoints": [
                        {"path": "/users", "methods": ["GET", "POST"]},
                        {"path": "/posts", "methods": ["GET", "PUT", "DELETE"]}
                    ]
                }
            }
        }
        that(data).path("api.v1.endpoints[0].path").equals("/users")
        that(data).path("api.v1.endpoints[1].methods[2]").equals("DELETE")


with suite("Enhanced Schema Validation"):

    @test("matches_schema validates enum constraints")
    def test_schema_enum():
        data = {"status": "active", "priority": "high"}
        schema = {
            "type": "object",
            "properties": {
                "status": {"enum": ["active", "inactive", "pending"]},
                "priority": {"enum": ["low", "medium", "high"]}
            }
        }
        that(data).matches_schema(schema)

        # Test enum failure
        invalid_data = {"status": "unknown"}
        invalid_schema = {
            "type": "object",
            "properties": {
                "status": {"enum": ["active", "inactive"]}
            }
        }
        that(lambda: that(invalid_data).matches_schema(invalid_schema)).raises(AssertionError)

    @test("matches_schema validates const constraints")
    def test_schema_const():
        data = {"version": "1.0", "type": "user"}
        schema = {
            "type": "object",
            "properties": {
                "version": {"const": "1.0"},
                "type": {"const": "user"}
            }
        }
        that(data).matches_schema(schema)

    @test("matches_schema validates additional properties")
    def test_schema_additional_properties():
        data = {"name": "Alice", "age": 30}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "additionalProperties": False
        }
        that(lambda: that(data).matches_schema(schema)).raises(AssertionError)

    @test("matches_schema validates array uniqueness")
    def test_schema_unique_items():
        data = {"tags": ["python", "testing", "python"]}
        schema = {
            "type": "object",
            "properties": {
                "tags": {
                    "type": "array",
                    "uniqueItems": True
                }
            }
        }
        that(lambda: that(data).matches_schema(schema)).raises(AssertionError)

    @test("matches_schema validates number constraints")
    def test_schema_number_constraints():
        data = {"score": 85, "percentage": 0.85}
        schema = {
            "type": "object",
            "properties": {
                "score": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 100,
                    "multipleOf": 5
                },
                "percentage": {
                    "type": "number",
                    "exclusiveMinimum": 0,
                    "exclusiveMaximum": 1
                }
            }
        }
        that(data).matches_schema(schema)


with suite("Real World Examples"):

    @test("API response validation")
    def test_api_response():
        response = {
            "status": "success",
            "data": {
                "user": {
                    "id": 123,
                    "name": "Alice",
                    "email": "alice@example.com",
                    "preferences": {
                        "notifications": True,
                        "theme": "dark"
                    }
                }
            },
            "metadata": {
                "timestamp": "2024-01-01T12:00:00Z",
                "version": "1.0"
            }
        }

        # Check overall structure
        that(response).has_keys("status", "data", "metadata")
        that(response).has_value("status", "success")

        # Check nested paths
        that(response).path("data.user.id").equals(123)
        that(response).path("data.user.name").equals("Alice")
        that(response).path("data.user.preferences.theme").equals("dark")

        # Validate with schema
        schema = {
            "type": "object",
            "properties": {
                "status": {"type": "string"},
                "data": {
                    "type": "object",
                    "properties": {
                        "user": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "integer"},
                                "name": {"type": "string"},
                                "email": {"type": "string"}
                            },
                            "required": ["id", "name", "email"]
                        }
                    }
                }
            },
            "required": ["status", "data"]
        }
        that(response).matches_schema(schema)

    @test("JSON API testing")
    def test_json_api():
        json_response = '''
        {
            "users": [
                {"id": 1, "name": "Alice", "role": "admin"},
                {"id": 2, "name": "Bob", "role": "user"}
            ],
            "pagination": {
                "page": 1,
                "total": 2,
                "hasMore": false
            }
        }
        '''

        parsed = that(json_response).as_json()

        # Check structure
        parsed.has_keys("users", "pagination")
        parsed.path("users").has_length(2)
        parsed.path("users[0].name").equals("Alice")
        parsed.path("users[1].role").equals("user")
        parsed.path("pagination.hasMore").is_false()

        # Validate schema
        schema = {
            "type": "object",
            "properties": {
                "users": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "role": {"type": "string"}
                        },
                        "required": ["id", "name", "role"]
                    }
                },
                "pagination": {
                    "type": "object",
                    "properties": {
                        "page": {"type": "integer"},
                        "total": {"type": "integer"},
                        "hasMore": {"type": "boolean"}
                    }
                }
            }
        }
        parsed.matches_schema(schema)