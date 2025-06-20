# Plugin System

The That testing library features a powerful plugin system that allows you to extend its functionality with custom decorators, assertion methods, and lifecycle hooks.

## Overview

The plugin system supports three types of plugins:

- **Decorator Plugins**: Add custom test decorators (like `@replay.time()`)
- **Assertion Plugins**: Add custom assertion methods (like `.is_email()`)
- **Lifecycle Plugins**: Hook into test execution events for logging, metrics, etc.

## Built-in Plugins

### Replay Plugin

The replay plugin provides time freezing and HTTP recording capabilities:

```python
from test_that import test, that, replay
import datetime
import requests

@test("time freezing example")
@replay.time("2024-01-01T12:00:00Z")
def test_with_frozen_time():
    current_time = datetime.datetime.now()
    that(current_time.year).equals(2024)

@test("HTTP recording example")
@replay.http("api_call")
def test_with_http_recording():
    response = requests.get("https://api.example.com/data")
    that(response.status_code).equals(200)

@test("combined example")
@replay(time="2024-01-01T12:00:00Z", http="api_call")
def test_combined():
    # Both time freezing and HTTP recording active
    pass
```

### JSON Schema Plugin

Adds JSON parsing and schema validation capabilities:

```python
from test_that import test, that

@test("JSON parsing and validation")
def test_json():
    # Parse JSON strings
    json_data = '{"name": "John", "age": 30}'
    that(json_data).as_json().has_key("name")

    # Validate against JSON schema
    user_schema = {
        "type": "object",
        "properties": {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0}
        },
        "required": ["name", "age"]
    }
    that(json_data).as_json().matches_schema(user_schema)
```

## Configuration

Configure plugins in your `pyproject.toml`:

```toml
[tool.that.plugins]
# Enable/disable plugins (empty list means all available plugins are enabled)
enabled = []
disabled = []
auto_discover = true
fail_on_plugin_error = false

# Plugin-specific configuration
[tool.that.plugins.replay]
recordings_dir = "tests/recordings"
default_http_mode = "once"
time_format = "iso"
http_timeout = 30

[tool.that.plugins.json_schema]
prefer_jsonschema_library = true

[tool.that.plugins.example_lifecycle]
enabled = false
verbose = false
slow_threshold = 0.1
```

## Creating Custom Plugins

### Decorator Plugin

Create a plugin that adds custom test decorators:

```python
from that.plugins.base import DecoratorPlugin, PluginInfo
from typing import Dict, Callable

class DatabasePlugin(DecoratorPlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="database",
            version="1.0.0",
            description="Database transaction management",
            dependencies=['sqlalchemy']
        )

    def get_decorators(self) -> Dict[str, Callable]:
        return {
            'transaction': self._create_transaction_decorator
        }

    def _create_transaction_decorator(self, rollback=True):
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Start transaction
                with database.transaction() as tx:
                    try:
                        result = func(*args, **kwargs)
                        if rollback:
                            tx.rollback()
                        else:
                            tx.commit()
                        return result
                    except Exception:
                        tx.rollback()
                        raise
            return wrapper
        return decorator
```

Usage:
```python
@test("database test")
@database.transaction(rollback=True)
def test_user_creation():
    user = create_user("test@example.com")
    that(user.id).is_not_none()
```

### Assertion Plugin

Create a plugin that adds custom assertion methods:

```python
from that.plugins.base import AssertionPlugin, PluginInfo
from typing import Dict, Callable
import json

class JSONSchemaPlugin(AssertionPlugin):
    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="json_schema",
            version="1.0.0",
            description="JSON parsing and schema validation",
            optional_dependencies=['jsonschema']
        )

    def get_assertion_methods(self) -> Dict[str, Callable]:
        return {
            'as_json': self._as_json,
            'matches_schema': self._matches_schema,
        }

    def _as_json(self, assertion_instance):
        """Parse value as JSON and return assertion for parsed data."""
        value = assertion_instance.value

        try:
            parsed = json.loads(value)
            from that.assertions import ThatAssertion
            return ThatAssertion(parsed, f"{assertion_instance.expression}.as_json()")
        except json.JSONDecodeError as e:
            from that.assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{assertion_instance.expression}.as_json()",
                expected="valid JSON string",
                actual=f"invalid JSON: {str(e)}"
            )

    def _matches_schema(self, assertion_instance):
        """Return a function that validates against a JSON schema."""
        def schema_validator(schema: dict):
            # Try jsonschema library first, fall back to built-in validation
            try:
                import jsonschema
                jsonschema.validate(assertion_instance.value, schema)
            except ImportError:
                # Use built-in validation logic here
                pass
            return assertion_instance
        return schema_validator
```

Usage:
```python
@test("JSON validation")
def test_json():
    json_data = '{"name": "John", "age": 30}'
    that(json_data).as_json().has_key("name")

    schema = {"type": "object", "properties": {"name": {"type": "string"}}}
    that(json_data).as_json().matches_schema(schema)
```

### Lifecycle Plugin

Create a plugin that hooks into test execution:

```python
from that.plugins.base import LifecyclePlugin, PluginInfo
from typing import Dict, Any

class MetricsPlugin(LifecyclePlugin):
    def __init__(self):
        self.metrics = {}

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="metrics",
            version="1.0.0",
            description="Collect test execution metrics"
        )

    def before_test_run(self) -> None:
        self.metrics = {
            'start_time': time.time(),
            'test_count': 0,
            'failures': 0
        }

    def after_test_run(self) -> None:
        duration = time.time() - self.metrics['start_time']
        print(f"Test run completed in {duration:.2f}s")
        print(f"Tests: {self.metrics['test_count']}")
        print(f"Failures: {self.metrics['failures']}")

    def before_test(self, test_name: str) -> None:
        self.metrics['test_count'] += 1

    def after_test(self, test_name: str, result: Any) -> None:
        if hasattr(result, 'passed') and not result.passed:
            self.metrics['failures'] += 1
```

## Plugin Distribution

### Entry Points

Distribute plugins via Python packages using entry points:

```toml
# In your plugin package's pyproject.toml
[project.entry-points."that.plugins"]
my_plugin = "my_package.plugins:MyPlugin"
```

### Installation

Users can install and use your plugin:

```bash
pip install my-that-plugin
```

The plugin will be automatically discovered and loaded.

## Best Practices

1. **Error Handling**: Always handle errors gracefully in plugins
2. **Dependencies**: Use optional dependencies when possible
3. **Configuration**: Support configuration through `pyproject.toml`
4. **Documentation**: Provide clear documentation and examples
5. **Testing**: Include comprehensive tests for your plugin
6. **Naming**: Use descriptive names for plugins and methods
7. **Performance**: Keep plugin overhead minimal

## Plugin Development Tips

- Use the `initialize()` method to set up plugin state
- Implement `cleanup()` for resource cleanup
- Check for optional dependencies before registering features
- Use meaningful error messages in custom assertions
- Follow the existing code style and patterns
- Test your plugin with different Python versions
