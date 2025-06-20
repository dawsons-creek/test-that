"""
Assertion API for the That testing library.

Provides a fluent interface for making assertions about values.
"""

import re
import json
from typing import Any, Callable, Pattern, Type, Union, List, Dict


class ThatAssertionError(AssertionError):
    """Custom assertion error with detailed information."""

    def __init__(
        self,
        message: str,
        expected: Any = None,
        actual: Any = None,
        diff_lines: List[str] = None,
    ):
        super().__init__(message)
        self.expected = expected
        self.actual = actual
        self.message = message
        self.diff_lines = diff_lines or []


def create_intelligent_diff(expected: Any, actual: Any) -> List[str]:
    """Create intelligent diff based on the types of expected and actual values."""

    # Handle None values
    if expected is None or actual is None:
        return [f"Expected: {repr(expected)}", f"Got: {repr(actual)}"]

    # Dictionary/Object differences
    if isinstance(expected, dict) and isinstance(actual, dict):
        return _create_dict_diff(expected, actual)

    # List/Array differences
    if isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        return _create_list_diff(expected, actual)

    # String differences
    if isinstance(expected, str) and isinstance(actual, str):
        return _create_string_diff(expected, actual)

    # Number differences
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return _create_number_diff(expected, actual)

    # Default fallback
    return [f"Expected: {repr(expected)}", f"Got: {repr(actual)}"]


def _create_dict_diff(expected: dict, actual: dict, path: str = "") -> List[str]:
    """Create detailed diff for dictionaries with nested path support."""
    lines = ["Dictionary differences:"] if not path else []
    all_keys = set(expected.keys()) | set(actual.keys())

    for key in sorted(all_keys):
        current_path = f"{path}.{key}" if path else key
        
        if key in expected and key in actual:
            lines.extend(_process_common_key(key, expected, actual, current_path))
        elif key in expected:
            lines.append(f"  - {current_path} (expected but not found)")
        else:
            lines.extend(_process_added_key(key, actual, current_path))

    return lines


def _process_common_key(key: str, expected: dict, actual: dict, path: str) -> List[str]:
    """Process a key that exists in both dictionaries."""
    expected_val = expected[key]
    actual_val = actual[key]

    if expected_val == actual_val:
        return [_format_matching_value(path, actual_val)]
    
    # Handle nested dictionaries recursively
    if isinstance(expected_val, dict) and isinstance(actual_val, dict):
        return _create_dict_diff(expected_val, actual_val, path)
    else:
        return [f"  ✗ {path}: expected {repr(expected_val)}, got {repr(actual_val)}"]


def _format_matching_value(path: str, value: Any) -> str:
    """Format a matching value with appropriate simplification."""
    if isinstance(value, dict) and len(value) > 3:
        return f"  ✓ {path}: {{...}}"
    elif isinstance(value, (list, tuple)) and len(value) > 3:
        return f"  ✓ {path}: [...] ({len(value)} items)"
    else:
        return f"  ✓ {path}: {repr(value)}"


def _process_added_key(key: str, actual: dict, path: str) -> List[str]:
    """Process a key that only exists in actual."""
    actual_val = actual[key]
    if isinstance(actual_val, dict):
        return [f"  + {path}: {{...}} (not in expected)"]
    elif isinstance(actual_val, (list, tuple)) and len(actual_val) > 3:
        return [f"  + {path}: [...] ({len(actual_val)} items) (not in expected)"]
    else:
        return [f"  + {path}: {repr(actual_val)} (not in expected)"]


def _create_list_diff(expected: list, actual: list) -> List[str]:
    """Create detailed diff for lists."""
    lines = ["List differences:"]

    if len(expected) != len(actual):
        lines.append(f"Length: expected {len(expected)} items, got {len(actual)}")
        lines.append("")

    max_len = max(len(expected), len(actual))

    for i in range(max_len):
        if i < len(expected) and i < len(actual):
            if expected[i] == actual[i]:
                lines.append(f"  [{i}] ✓ {repr(actual[i])}")
            else:
                lines.append(
                    f"  [{i}] ✗ expected {repr(expected[i])}, got {repr(actual[i])}"
                )
        elif i < len(expected):
            lines.append(f"  [{i}] - {repr(expected[i])} (expected but missing)")
        else:
            lines.append(f"  [{i}] + {repr(actual[i])} (unexpected)")

    return lines


def _create_string_diff(expected: str, actual: str) -> List[str]:
    """Create detailed diff for strings."""
    lines = [f'Expected: "{expected}"', f'Got:      "{actual}"']

    # Find first difference
    for i, (e_char, a_char) in enumerate(zip(expected, actual)):
        if e_char != a_char:
            pointer = " " * (10 + i) + "^"  # 10 chars for "Got:      \""
            lines.append(pointer)
            lines.append(
                f"First difference at position {i}: expected '{e_char}' but got '{a_char}'"
            )
            break
    else:
        # No differences in common part, check lengths
        if len(expected) != len(actual):
            if len(expected) > len(actual):
                lines.append(
                    f"Expected string is longer by {len(expected) - len(actual)} characters"
                )
            else:
                lines.append(
                    f"Actual string is longer by {len(actual) - len(expected)} characters"
                )

    return lines


def _create_number_diff(
    expected: Union[int, float], actual: Union[int, float]
) -> List[str]:
    """Create detailed diff for numbers."""
    lines = [f"Expected: {expected}", f"Got: {actual}"]

    difference = actual - expected
    if difference > 0:
        lines.append(f"Difference: +{difference}")
    else:
        lines.append(f"Difference: {difference}")

    return lines


class ThatAssertion:
    """Fluent assertion interface."""

    def __init__(self, value: Any, expression: str = ""):
        self.value = value
        self.expression = expression or f"that({repr(value)})"

    def equals(self, expected: Any) -> "ThatAssertion":
        """Assert that the value equals the expected value."""
        # Fast path for None comparison
        if expected is None and self.value is not None:
            raise ThatAssertionError(
                f"{self.expression}.equals(None)",
                expected=None,
                actual=self.value,
            )
        
        if self.value != expected:
            diff_lines = create_intelligent_diff(expected, self.value)
            raise ThatAssertionError(
                f"{self.expression}.equals({repr(expected)})",
                expected=expected,
                actual=self.value,
                diff_lines=diff_lines,
            )
        return self

    def does_not_equal(self, expected: Any) -> "ThatAssertion":
        """Assert that the value does not equal the expected value."""
        if self.value == expected:
            raise ThatAssertionError(
                f"{self.expression}.does_not_equal({repr(expected)})",
                expected=f"not {repr(expected)}",
                actual=self.value,
            )
        return self

    def is_true(self) -> "ThatAssertion":
        """Assert that the value is True."""
        if self.value is not True:
            raise ThatAssertionError(
                f"{self.expression}.is_true()", expected=True, actual=self.value
            )
        return self

    def is_false(self) -> "ThatAssertion":
        """Assert that the value is False."""
        if self.value is not False:
            raise ThatAssertionError(
                f"{self.expression}.is_false()", expected=False, actual=self.value
            )
        return self

    def is_none(self) -> "ThatAssertion":
        """Assert that the value is None."""
        if self.value is not None:
            raise ThatAssertionError(
                f"{self.expression}.is_none()", expected=None, actual=self.value
            )
        return self

    def is_not_none(self) -> "ThatAssertion":
        """Assert that the value is not None."""
        if self.value is None:
            raise ThatAssertionError(
                f"{self.expression}.is_not_none()", expected="not None", actual=None
            )
        return self

    def contains(self, item: Any) -> "ThatAssertion":
        """Assert that the collection contains the item."""
        try:
            if item not in self.value:
                raise ThatAssertionError(
                    f"{self.expression}.contains({repr(item)})",
                    expected=f"collection containing {repr(item)}",
                    actual=self.value,
                )
        except TypeError:
            raise ThatAssertionError(
                f"{self.expression}.contains({repr(item)})",
                expected=f"collection containing {repr(item)}",
                actual=f"{type(self.value).__name__} (not iterable)",
            )
        return self

    def does_not_contain(self, item: Any) -> "ThatAssertion":
        """Assert that the collection does not contain the item."""
        try:
            if item in self.value:
                raise ThatAssertionError(
                    f"{self.expression}.does_not_contain({repr(item)})",
                    expected=f"collection not containing {repr(item)}",
                    actual=self.value,
                )
        except TypeError:
            # If not iterable, it doesn't contain the item
            pass
        return self

    def is_empty(self) -> "ThatAssertion":
        """Assert that the collection is empty."""
        try:
            if len(self.value) != 0:
                raise ThatAssertionError(
                    f"{self.expression}.is_empty()",
                    expected="empty collection",
                    actual=f"collection with {len(self.value)} items",
                )
        except TypeError:
            raise ThatAssertionError(
                f"{self.expression}.is_empty()",
                expected="empty collection",
                actual=f"{type(self.value).__name__} (no length)",
            )
        return self

    def has_length(self, expected_length: int) -> "ThatAssertion":
        """Assert that the collection has the expected length."""
        try:
            actual_length = len(self.value)
            if actual_length != expected_length:
                raise ThatAssertionError(
                    f"{self.expression}.has_length({expected_length})",
                    expected=f"length {expected_length}",
                    actual=f"length {actual_length}",
                )
        except TypeError:
            raise ThatAssertionError(
                f"{self.expression}.has_length({expected_length})",
                expected=f"length {expected_length}",
                actual=f"{type(self.value).__name__} (no length)",
            )
        return self

    def matches(self, pattern: Union[str, Pattern]) -> "ThatAssertion":
        """Assert that the string matches the regex pattern."""
        if not isinstance(self.value, str):
            raise ThatAssertionError(
                f"{self.expression}.matches({repr(pattern)})",
                expected="string value",
                actual=f"{type(self.value).__name__}",
            )

        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        if not pattern.search(self.value):
            raise ThatAssertionError(
                f"{self.expression}.matches({repr(pattern.pattern)})",
                expected=f"string matching {repr(pattern.pattern)}",
                actual=repr(self.value),
            )
        return self

    def starts_with(self, prefix: str) -> "ThatAssertion":
        """Assert that the string starts with the prefix."""
        if not isinstance(self.value, str):
            raise ThatAssertionError(
                f"{self.expression}.starts_with({repr(prefix)})",
                expected="string value",
                actual=f"{type(self.value).__name__}",
            )

        if not self.value.startswith(prefix):
            raise ThatAssertionError(
                f"{self.expression}.starts_with({repr(prefix)})",
                expected=f"string starting with {repr(prefix)}",
                actual=repr(self.value),
            )
        return self

    def ends_with(self, suffix: str) -> "ThatAssertion":
        """Assert that the string ends with the suffix."""
        if not isinstance(self.value, str):
            raise ThatAssertionError(
                f"{self.expression}.ends_with({repr(suffix)})",
                expected="string value",
                actual=f"{type(self.value).__name__}",
            )

        if not self.value.endswith(suffix):
            raise ThatAssertionError(
                f"{self.expression}.ends_with({repr(suffix)})",
                expected=f"string ending with {repr(suffix)}",
                actual=repr(self.value),
            )
        return self

    def raises(self, exception_type: Type[Exception]) -> "ThatAssertion":
        """Assert that the callable raises the expected exception type."""
        if not callable(self.value):
            raise ThatAssertionError(
                f"{self.expression}.raises({exception_type.__name__})",
                expected="callable",
                actual=f"{type(self.value).__name__}",
            )

        try:
            self.value()
            raise ThatAssertionError(
                f"{self.expression}.raises({exception_type.__name__})",
                expected=f"{exception_type.__name__}",
                actual="no exception raised",
            )
        except exception_type:
            # Expected exception was raised
            pass
        except Exception as e:
            raise ThatAssertionError(
                f"{self.expression}.raises({exception_type.__name__})",
                expected=f"{exception_type.__name__}",
                actual=f"{type(e).__name__}({repr(str(e))})",
            )
        return self

    def does_not_raise(self) -> "ThatAssertion":
        """Assert that the callable does not raise any exception."""
        if not callable(self.value):
            raise ThatAssertionError(
                f"{self.expression}.does_not_raise()",
                expected="callable",
                actual=f"{type(self.value).__name__}",
            )

        try:
            result = self.value()
            # Return a new assertion for the result
            return ThatAssertion(result, f"{self.expression}()")
        except Exception as e:
            raise ThatAssertionError(
                f"{self.expression}.does_not_raise()",
                expected="no exception",
                actual=f"{type(e).__name__}({repr(str(e))})",
            )

    def is_greater_than(self, value: Union[int, float]) -> "ThatAssertion":
        """Assert that the number is greater than the given value."""
        if not isinstance(self.value, (int, float)):
            raise ThatAssertionError(
                f"{self.expression}.is_greater_than({value})",
                expected="numeric value",
                actual=f"{type(self.value).__name__}",
            )

        if not self.value > value:
            raise ThatAssertionError(
                f"{self.expression}.is_greater_than({value})",
                expected=f"value > {value}",
                actual=self.value,
            )
        return self

    def is_less_than(self, value: Union[int, float]) -> "ThatAssertion":
        """Assert that the number is less than the given value."""
        if not isinstance(self.value, (int, float)):
            raise ThatAssertionError(
                f"{self.expression}.is_less_than({value})",
                expected="numeric value",
                actual=f"{type(self.value).__name__}",
            )

        if not self.value < value:
            raise ThatAssertionError(
                f"{self.expression}.is_less_than({value})",
                expected=f"value < {value}",
                actual=self.value,
            )
        return self

    def is_between(
        self, min_val: Union[int, float], max_val: Union[int, float]
    ) -> "ThatAssertion":
        """Assert that the number is between min_val and max_val (inclusive)."""
        if not isinstance(self.value, (int, float)):
            raise ThatAssertionError(
                f"{self.expression}.is_between({min_val}, {max_val})",
                expected="numeric value",
                actual=f"{type(self.value).__name__}",
            )

        if not (min_val <= self.value <= max_val):
            raise ThatAssertionError(
                f"{self.expression}.is_between({min_val}, {max_val})",
                expected=f"value between {min_val} and {max_val}",
                actual=self.value,
            )
        return self

    def is_instance_of(self, expected_type: Type) -> "ThatAssertion":
        """Assert that the value is an instance of the expected type."""
        if not isinstance(self.value, expected_type):
            raise ThatAssertionError(
                f"{self.expression}.is_instance_of({expected_type.__name__})",
                expected=f"instance of {expected_type.__name__}",
                actual=f"instance of {type(self.value).__name__}",
            )
        return self

    def has_type(self, expected_type: Type) -> "ThatAssertion":
        """Assert that the value has the exact expected type."""
        if type(self.value) is not expected_type:
            raise ThatAssertionError(
                f"{self.expression}.has_type({expected_type.__name__})",
                expected=f"type {expected_type.__name__}",
                actual=f"type {type(self.value).__name__}",
            )
        return self

    def approximately_equals(
        self, expected: Union[int, float], tolerance: float = 1e-9
    ) -> "ThatAssertion":
        """Assert that the numeric value is approximately equal to expected within tolerance."""
        if not isinstance(self.value, (int, float)) or not isinstance(
            expected, (int, float)
        ):
            raise ThatAssertionError(
                f"{self.expression}.approximately_equals({expected}, tolerance={tolerance})",
                expected=f"numeric value approximately equal to {expected}",
                actual=f"non-numeric value {repr(self.value)}",
            )

        diff = abs(self.value - expected)
        if diff > tolerance:
            raise ThatAssertionError(
                f"{self.expression}.approximately_equals({expected}, tolerance={tolerance})",
                expected=expected,
                actual=self.value,
                diff_lines=[
                    f"Expected: {expected} (±{tolerance})",
                    f"Got: {self.value}",
                    f"Difference: {diff} (exceeds tolerance)",
                ],
            )
        return self

    def all_satisfy(self, predicate: Callable[[Any], bool]) -> "ThatAssertion":
        """Assert that all items in the collection satisfy the predicate."""
        try:
            items = list(self.value)
        except TypeError:
            raise ThatAssertionError(
                f"{self.expression}.all_satisfy(<predicate>)",
                expected="iterable collection",
                actual=f"{type(self.value).__name__} (not iterable)",
            )

        failing_items = []
        for i, item in enumerate(items):
            try:
                if not predicate(item):
                    failing_items.append((i, item))
            except Exception as e:
                failing_items.append((i, f"Error: {e}"))

        if failing_items:
            failure_details = []
            for i, item in failing_items[:5]:  # Show first 5 failures
                failure_details.append(f"  [{i}]: {repr(item)}")
            if len(failing_items) > 5:
                failure_details.append(f"  ... and {len(failing_items) - 5} more")

            raise ThatAssertionError(
                f"{self.expression}.all_satisfy(<predicate>)",
                expected="all items to satisfy predicate",
                actual=f"{len(failing_items)} items failed",
                diff_lines=["Items that failed:"] + failure_details,
            )
        return self

    def are_unique(self) -> "ThatAssertion":
        """Assert that all items in the collection are unique."""
        try:
            items = list(self.value)
        except TypeError:
            raise ThatAssertionError(
                f"{self.expression}.are_unique()",
                expected="iterable collection",
                actual=f"{type(self.value).__name__} (not iterable)",
            )

        seen = set()
        duplicates = []
        for i, item in enumerate(items):
            if item in seen:
                duplicates.append((i, item))
            else:
                seen.add(item)

        if duplicates:
            duplicate_details = []
            for i, item in duplicates[:5]:  # Show first 5 duplicates
                duplicate_details.append(f"  [{i}]: {repr(item)}")
            if len(duplicates) > 5:
                duplicate_details.append(f"  ... and {len(duplicates) - 5} more")

            raise ThatAssertionError(
                f"{self.expression}.are_unique()",
                expected="all unique items",
                actual=f"{len(duplicates)} duplicate items found",
                diff_lines=["Duplicate items:"] + duplicate_details,
            )
        return self

    def are_sorted_by(
        self, key_func: Union[str, Callable[[Any], Any]], reverse: bool = False
    ) -> "ThatAssertion":
        """Assert that items in the collection are sorted by the given key."""
        items = _validate_iterable_for_sorting(self.value, self.expression, key_func)
        
        if len(items) <= 1:
            return self

        get_key = _create_key_function(key_func)
        sorted_items = _sort_items_safely(items, get_key, reverse, self.expression, key_func)
        
        if items != sorted_items:
            _raise_sorting_error(items, sorted_items, reverse, self.expression, key_func)
        
        return self

    def has_key(self, key: str) -> "ThatAssertion":
        """Assert that the dictionary contains the given key."""
        if not isinstance(self.value, dict):
            raise ThatAssertionError(
                f"{self.expression}.has_key({repr(key)})",
                expected="dictionary",
                actual=f"{type(self.value).__name__}",
            )
        
        if key not in self.value:
            available_keys = list(self.value.keys())
            raise ThatAssertionError(
                f"{self.expression}.has_key({repr(key)})",
                expected=f"dictionary with key {repr(key)}",
                actual=f"dictionary with keys {available_keys}",
            )
        return self

    def has_keys(self, *keys: str) -> "ThatAssertion":
        """Assert that the dictionary contains all given keys."""
        if not isinstance(self.value, dict):
            raise ThatAssertionError(
                f"{self.expression}.has_keys({', '.join(repr(k) for k in keys)})",
                expected="dictionary",
                actual=f"{type(self.value).__name__}",
            )
        
        missing_keys = [key for key in keys if key not in self.value]
        if missing_keys:
            available_keys = list(self.value.keys())
            raise ThatAssertionError(
                f"{self.expression}.has_keys({', '.join(repr(k) for k in keys)})",
                expected=f"dictionary with keys {list(keys)}",
                actual=f"dictionary missing keys {missing_keys} (available: {available_keys})",
            )
        return self

    def has_value(self, key: str, expected_value: Any) -> "ThatAssertion":
        """Assert that the dictionary has the given key with the expected value."""
        self.has_key(key)
        actual_value = self.value[key]
        if actual_value != expected_value:
            raise ThatAssertionError(
                f"{self.expression}.has_value({repr(key)}, {repr(expected_value)})",
                expected=f"key {repr(key)} with value {repr(expected_value)}",
                actual=f"key {repr(key)} with value {repr(actual_value)}",
            )
        return self

    def has_path(self, path: str) -> "ThatAssertion":
        """Assert that the nested path exists in the data structure."""
        try:
            _get_nested_value(self.value, path)
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise ThatAssertionError(
                f"{self.expression}.has_path({repr(path)})",
                expected=f"path {repr(path)} to exist",
                actual=f"path not found: {str(e)}",
            )
        return self

    def path(self, path: str) -> "ThatAssertion":
        """Get a nested value by path and return new assertion for it."""
        try:
            nested_value = _get_nested_value(self.value, path)
            return ThatAssertion(nested_value, f"{self.expression}.path({repr(path)})")
        except (KeyError, IndexError, TypeError, ValueError) as e:
            raise ThatAssertionError(
                f"{self.expression}.path({repr(path)})",
                expected=f"path {repr(path)} to exist",
                actual=f"path not found: {str(e)}",
            )

    def as_json(self) -> "ThatAssertion":
        """Parse value as JSON and return assertion for parsed data."""
        if not isinstance(self.value, str):
            raise ThatAssertionError(
                f"{self.expression}.as_json()",
                expected="JSON string",
                actual=f"{type(self.value).__name__}",
            )
        
        try:
            parsed = json.loads(self.value)
            return ThatAssertion(parsed, f"{self.expression}.as_json()")
        except json.JSONDecodeError as e:
            raise ThatAssertionError(
                f"{self.expression}.as_json()",
                expected="valid JSON string",
                actual=f"invalid JSON: {str(e)}",
            )

    def matches_schema(self, schema: Dict[str, Any]) -> "ThatAssertion":
        """Assert that the value matches the given JSON schema."""
        validation_errors = _validate_json_schema(self.value, schema)
        if validation_errors:
            error_details = "\n  ".join(validation_errors)
            raise ThatAssertionError(
                f"{self.expression}.matches_schema(...)",
                expected="data matching schema",
                actual="data with schema violations",
                diff_lines=["Schema validation errors:", f"  {error_details}"]
            )
        return self

    def has_structure(self, expected_structure: Dict[str, Any]) -> "ThatAssertion":
        """Assert that the dictionary has the expected structure (keys and types)."""
        if not isinstance(self.value, dict):
            raise ThatAssertionError(
                f"{self.expression}.has_structure(...)",
                expected="dictionary",
                actual=f"{type(self.value).__name__}",
            )
        
        structure_errors = _validate_structure(self.value, expected_structure)
        if structure_errors:
            error_details = "\n  ".join(structure_errors)
            raise ThatAssertionError(
                f"{self.expression}.has_structure(...)",
                expected="data matching structure",
                actual="data with structure violations",
                diff_lines=["Structure validation errors:", f"  {error_details}"]
            )
        return self


def _get_nested_value(data: Any, path: str) -> Any:
    """Get nested value using dot notation path (e.g., 'user.address.city')."""
    current = data
    parts = path.split('.')
    traversed_path = []

    for part in parts:
        traversed_path.append(part)

        # Handle array indexing like 'items[0]' or 'users[*]'
        if '[' in part and part.endswith(']'):
            try:
                key, index_part = part.split('[', 1)
                index = index_part[:-1]  # Remove closing ]

                if key:  # Get the array first
                    if isinstance(current, dict):
                        if key not in current:
                            available_keys = list(current.keys())
                            raise KeyError(f"Key '{key}' not found. Available keys: {available_keys}")
                        current = current[key]
                    else:
                        raise TypeError(f"Cannot access key '{key}' on {type(current).__name__}")

                if index == '*':
                    # Return the array itself for wildcard
                    continue
                else:
                    # Validate and get specific index
                    if not isinstance(current, (list, tuple)):
                        raise TypeError(f"Cannot index into {type(current).__name__} at '{'.'.join(traversed_path)}'")

                    try:
                        index_int = int(index)
                    except ValueError:
                        raise ValueError(f"Invalid array index '{index}' at '{'.'.join(traversed_path)}'. Must be an integer.")

                    # Support negative indices
                    if index_int < 0:
                        index_int = len(current) + index_int

                    if index_int < 0 or index_int >= len(current):
                        raise IndexError(f"Array index {index} out of range for array of length {len(current)} at '{'.'.join(traversed_path)}'")

                    current = current[index_int]
            except (ValueError, IndexError, KeyError, TypeError) as e:
                # Re-raise with more context about where the error occurred
                raise type(e)(f"Error at path '{'.'.join(traversed_path)}': {str(e)}")
        else:
            if isinstance(current, dict):
                if part not in current:
                    available_keys = list(current.keys())
                    raise KeyError(f"Key '{part}' not found at '{'.'.join(traversed_path[:-1]) or 'root'}'. Available keys: {available_keys}")
                current = current[part]
            else:
                raise TypeError(f"Cannot access key '{part}' on {type(current).__name__} at '{'.'.join(traversed_path[:-1]) or 'root'}'")

    return current


def _validate_json_schema(data: Any, schema: Dict[str, Any]) -> List[str]:
    """Validate data against a simple JSON schema. Returns list of errors."""
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
        expected_type = _get_python_type(schema_type)
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
                prop_errors = _validate_json_schema(data[key], prop_schema)
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
                item_errors = _validate_json_schema(item, items_schema)
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


def _get_python_type(schema_type: str) -> type:
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


def _validate_structure(data: Dict[str, Any], expected_structure: Dict[str, Any]) -> List[str]:
    """Validate dictionary structure (keys and types). Returns list of errors."""
    errors = []
    
    for key, expected_type in expected_structure.items():
        if key not in data:
            errors.append(f"Missing key '{key}'")
            continue
        
        value = data[key]
        if not isinstance(value, expected_type):
            errors.append(f"Key '{key}': expected {expected_type.__name__}, got {type(value).__name__}")
    
    return errors


def _validate_iterable_for_sorting(value: Any, expression: str, key_func) -> list:
    """Validate that value is iterable for sorting."""
    try:
        return list(value)
    except TypeError:
        raise ThatAssertionError(
            f"{expression}.are_sorted_by({repr(key_func)})",
            expected="iterable collection",
            actual=f"{type(value).__name__} (not iterable)",
        )


def _create_key_function(key_func: Union[str, Callable]):
    """Create appropriate key function from string or callable."""
    if isinstance(key_func, str):
        def get_key(item):
            if isinstance(item, dict):
                return item[key_func]
            else:
                return getattr(item, key_func)
        return get_key
    else:
        return key_func


def _sort_items_safely(items: list, get_key: Callable, reverse: bool, expression: str, key_func) -> list:
    """Sort items safely with error handling."""
    try:
        return sorted(items, key=get_key, reverse=reverse)
    except Exception as e:
        raise ThatAssertionError(
            f"{expression}.are_sorted_by({repr(key_func)})",
            expected="sortable items",
            actual=f"Error sorting: {e}",
        )


def _raise_sorting_error(items: list, sorted_items: list, reverse: bool, expression: str, key_func):
    """Raise assertion error for unsorted items."""
    first_diff_index = _find_first_difference(items, sorted_items)
    direction = "descending" if reverse else "ascending"
    
    raise ThatAssertionError(
        f"{expression}.are_sorted_by({repr(key_func)})",
        expected=f"items sorted {direction}",
        actual=f"item at index {first_diff_index} is out of order",
        diff_lines=[
            f"Expected order: {repr(sorted_items[:5])}{'...' if len(sorted_items) > 5 else ''}",
            f"Actual order:   {repr(items[:5])}{'...' if len(items) > 5 else ''}",
            f"First difference at index {first_diff_index}",
        ],
    )


def _find_first_difference(items: list, sorted_items: list) -> int:
    """Find index of first difference between lists."""
    for i in range(len(items)):
        if items[i] != sorted_items[i]:
            return i
    return 0


def that(value: Any) -> ThatAssertion:
    """Create a new assertion for the given value."""
    return ThatAssertion(value)
