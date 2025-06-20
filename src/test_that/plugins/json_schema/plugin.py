"""
JSON Schema validation plugin for the That testing library.

This plugin provides JSON parsing and schema validation capabilities as optional
functionality that can be enabled when needed. It demonstrates how to handle
optional dependencies in plugins.
"""

import json
import re
from typing import Dict, Callable, Any, List
from ..base import AssertionPlugin, PluginInfo


class JSONSchemaPlugin(AssertionPlugin):
    """Plugin providing JSON parsing and schema validation capabilities."""

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="json_schema",
            version="1.0.0",
            description="JSON parsing and schema validation for testing",
            dependencies=[],
            optional_dependencies=['jsonschema']
        )

    def get_assertion_methods(self) -> Dict[str, Callable]:
        """Return JSON-related assertion methods."""
        methods = {
            'as_json': self._as_json,
        }
        
        # Only add schema validation if we have the capability
        # (either built-in implementation or jsonschema library)
        methods['matches_schema'] = self._matches_schema
        
        return methods

    def _as_json(self, assertion_instance):
        """Parse value as JSON and return assertion for parsed data."""
        value = assertion_instance.value
        expression = assertion_instance.expression
        
        if not isinstance(value, str):
            from ...assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{expression}.as_json()",
                expected="JSON string",
                actual=f"{type(value).__name__}",
            )
        
        try:
            parsed = json.loads(value)
            # Create a new assertion instance for the parsed data
            from ...assertions import ThatAssertion
            return ThatAssertion(parsed, f"{expression}.as_json()")
        except json.JSONDecodeError as e:
            from ...assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{expression}.as_json()",
                expected="valid JSON string",
                actual=f"invalid JSON: {str(e)}",
            )

    def _matches_schema(self, assertion_instance):
        """Return a function that validates against a JSON schema."""
        def schema_validator(schema: Dict[str, Any]):
            value = assertion_instance.value
            expression = assertion_instance.expression
            
            # Try to use jsonschema library first (more comprehensive)
            try:
                import jsonschema
                try:
                    jsonschema.validate(value, schema)
                    return assertion_instance
                except jsonschema.ValidationError as e:
                    from ...assertions import ThatAssertionError
                    raise ThatAssertionError(
                        f"{expression}.matches_schema(...)",
                        expected="data matching schema",
                        actual="data with schema violations",
                        diff_lines=["Schema validation error:", f"  {str(e)}"]
                    )
                except jsonschema.SchemaError as e:
                    from ...assertions import ThatAssertionError
                    raise ThatAssertionError(
                        f"{expression}.matches_schema(...)",
                        expected="valid JSON schema",
                        actual="invalid schema",
                        diff_lines=["Schema error:", f"  {str(e)}"]
                    )
            except ImportError:
                # Fall back to built-in validation
                validation_errors = self._validate_json_schema_builtin(value, schema)
                if validation_errors:
                    error_details = "\n  ".join(validation_errors)
                    from ...assertions import ThatAssertionError
                    raise ThatAssertionError(
                        f"{expression}.matches_schema(...)",
                        expected="data matching schema",
                        actual="data with schema violations",
                        diff_lines=["Schema validation errors:", f"  {error_details}"]
                    )
                return assertion_instance
        
        return schema_validator

    def _validate_json_schema_builtin(self, data: Any, schema: Dict[str, Any]) -> List[str]:
        """Built-in JSON schema validation (subset of JSON Schema spec)."""
        errors = []

        # Check enum constraint first (applies to any type)
        enum_values = schema.get('enum')
        if enum_values is not None:
            if data not in enum_values:
                errors.append(f"Value {repr(data)} not in allowed values {enum_values}")
                return errors  # If enum fails, other validations are irrelevant

        # Check type
        schema_type = schema.get('type')
        if schema_type:
            expected_type = self._get_python_type(schema_type)
            if not isinstance(data, expected_type):
                errors.append(f"Expected type {schema_type}, got {type(data).__name__}")
                return errors  # Can't validate further if type is wrong

        # Check const constraint
        const_value = schema.get('const')
        if const_value is not None:
            if data != const_value:
                errors.append(f"Expected constant value {repr(const_value)}, got {repr(data)}")
                return errors

        # Check required properties (for objects)
        if schema_type == 'object' and isinstance(data, dict):
            required = schema.get('required', [])
            for req_key in required:
                if req_key not in data:
                    errors.append(f"Missing required property '{req_key}'")

            # Check properties
            properties = schema.get('properties', {})
            for key, prop_schema in properties.items():
                if key in data:
                    prop_errors = self._validate_json_schema_builtin(data[key], prop_schema)
                    for error in prop_errors:
                        errors.append(f"Property '{key}': {error}")

            # Check additional properties
            additional_properties = schema.get('additionalProperties')
            if additional_properties is False:
                allowed_keys = set(properties.keys())
                extra_keys = set(data.keys()) - allowed_keys
                if extra_keys:
                    errors.append(f"Additional properties not allowed: {sorted(extra_keys)}")

        # Check array items
        elif schema_type == 'array' and isinstance(data, list):
            items_schema = schema.get('items')
            if items_schema:
                for i, item in enumerate(data):
                    item_errors = self._validate_json_schema_builtin(item, items_schema)
                    for error in item_errors:
                        errors.append(f"Item [{i}]: {error}")

            # Check array length constraints
            min_items = schema.get('minItems')
            if min_items is not None and len(data) < min_items:
                errors.append(f"Array too short: {len(data)} < {min_items}")

            max_items = schema.get('maxItems')
            if max_items is not None and len(data) > max_items:
                errors.append(f"Array too long: {len(data)} > {max_items}")

            # Check uniqueness
            unique_items = schema.get('uniqueItems')
            if unique_items and len(data) != len(set(str(item) for item in data)):
                errors.append("Array items must be unique")

        # Check string constraints
        elif schema_type == 'string' and isinstance(data, str):
            min_length = schema.get('minLength')
            if min_length is not None and len(data) < min_length:
                errors.append(f"String too short: {len(data)} < {min_length}")

            max_length = schema.get('maxLength')
            if max_length is not None and len(data) > max_length:
                errors.append(f"String too long: {len(data)} > {max_length}")

            pattern = schema.get('pattern')
            if pattern and not re.match(pattern, data):
                errors.append(f"String does not match pattern: {pattern}")

        # Check number constraints
        elif schema_type in ('number', 'integer') and isinstance(data, (int, float)):
            minimum = schema.get('minimum')
            if minimum is not None and data < minimum:
                errors.append(f"Number too small: {data} < {minimum}")

            maximum = schema.get('maximum')
            if maximum is not None and data > maximum:
                errors.append(f"Number too large: {data} > {maximum}")

            exclusive_minimum = schema.get('exclusiveMinimum')
            if exclusive_minimum is not None and data <= exclusive_minimum:
                errors.append(f"Number must be greater than {exclusive_minimum}, got {data}")

            exclusive_maximum = schema.get('exclusiveMaximum')
            if exclusive_maximum is not None and data >= exclusive_maximum:
                errors.append(f"Number must be less than {exclusive_maximum}, got {data}")

            multiple_of = schema.get('multipleOf')
            if multiple_of is not None and data % multiple_of != 0:
                errors.append(f"Number {data} is not a multiple of {multiple_of}")

        return errors

    def _get_python_type(self, schema_type: str) -> type:
        """Convert JSON schema type to Python type."""
        type_map = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict,
            'null': type(None)
        }
        return type_map.get(schema_type, object)
