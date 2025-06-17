"""
Assertion API for the That testing library.

Provides a fluent interface for making assertions about values.
"""

import re
from typing import Any, Callable, Pattern, Type, Union, List


class AssertionError(Exception):
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
            expected_val = expected[key]
            actual_val = actual[key]

            if expected_val == actual_val:
                # For nested objects, show a simplified representation
                if isinstance(actual_val, dict) and len(actual_val) > 3:
                    lines.append(f"  ✓ {current_path}: {{...}}")
                elif isinstance(actual_val, (list, tuple)) and len(actual_val) > 3:
                    lines.append(f"  ✓ {current_path}: [...] ({len(actual_val)} items)")
                else:
                    lines.append(f"  ✓ {current_path}: {repr(actual_val)}")
            else:
                # Handle nested dictionaries recursively
                if isinstance(expected_val, dict) and isinstance(actual_val, dict):
                    nested_lines = _create_dict_diff(
                        expected_val, actual_val, current_path
                    )
                    lines.extend(nested_lines)  # Include nested differences
                else:
                    lines.append(
                        f"  ✗ {current_path}: expected {repr(expected_val)}, got {repr(actual_val)}"
                    )
        elif key in expected:
            lines.append(f"  - {current_path} (expected but not found)")
        else:
            # For added keys, show simplified representation for complex objects
            actual_val = actual[key]
            if isinstance(actual_val, dict):
                lines.append(f"  + {current_path}: {{...}} (not in expected)")
            elif isinstance(actual_val, (list, tuple)) and len(actual_val) > 3:
                lines.append(
                    f"  + {current_path}: [...] ({len(actual_val)} items) (not in expected)"
                )
            else:
                lines.append(
                    f"  + {current_path}: {repr(actual_val)} (not in expected)"
                )

    return lines


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
        if self.value != expected:
            diff_lines = create_intelligent_diff(expected, self.value)
            raise AssertionError(
                f"{self.expression}.equals({repr(expected)})",
                expected=expected,
                actual=self.value,
                diff_lines=diff_lines,
            )
        return self

    def does_not_equal(self, expected: Any) -> "ThatAssertion":
        """Assert that the value does not equal the expected value."""
        if self.value == expected:
            raise AssertionError(
                f"{self.expression}.does_not_equal({repr(expected)})",
                expected=f"not {repr(expected)}",
                actual=self.value,
            )
        return self

    def is_true(self) -> "ThatAssertion":
        """Assert that the value is True."""
        if self.value is not True:
            raise AssertionError(
                f"{self.expression}.is_true()", expected=True, actual=self.value
            )
        return self

    def is_false(self) -> "ThatAssertion":
        """Assert that the value is False."""
        if self.value is not False:
            raise AssertionError(
                f"{self.expression}.is_false()", expected=False, actual=self.value
            )
        return self

    def is_none(self) -> "ThatAssertion":
        """Assert that the value is None."""
        if self.value is not None:
            raise AssertionError(
                f"{self.expression}.is_none()", expected=None, actual=self.value
            )
        return self

    def is_not_none(self) -> "ThatAssertion":
        """Assert that the value is not None."""
        if self.value is None:
            raise AssertionError(
                f"{self.expression}.is_not_none()", expected="not None", actual=None
            )
        return self

    def contains(self, item: Any) -> "ThatAssertion":
        """Assert that the collection contains the item."""
        try:
            if item not in self.value:
                raise AssertionError(
                    f"{self.expression}.contains({repr(item)})",
                    expected=f"collection containing {repr(item)}",
                    actual=self.value,
                )
        except TypeError:
            raise AssertionError(
                f"{self.expression}.contains({repr(item)})",
                expected=f"collection containing {repr(item)}",
                actual=f"{type(self.value).__name__} (not iterable)",
            )
        return self

    def does_not_contain(self, item: Any) -> "ThatAssertion":
        """Assert that the collection does not contain the item."""
        try:
            if item in self.value:
                raise AssertionError(
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
                raise AssertionError(
                    f"{self.expression}.is_empty()",
                    expected="empty collection",
                    actual=f"collection with {len(self.value)} items",
                )
        except TypeError:
            raise AssertionError(
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
                raise AssertionError(
                    f"{self.expression}.has_length({expected_length})",
                    expected=f"length {expected_length}",
                    actual=f"length {actual_length}",
                )
        except TypeError:
            raise AssertionError(
                f"{self.expression}.has_length({expected_length})",
                expected=f"length {expected_length}",
                actual=f"{type(self.value).__name__} (no length)",
            )
        return self

    def matches(self, pattern: Union[str, Pattern]) -> "ThatAssertion":
        """Assert that the string matches the regex pattern."""
        if not isinstance(self.value, str):
            raise AssertionError(
                f"{self.expression}.matches({repr(pattern)})",
                expected="string value",
                actual=f"{type(self.value).__name__}",
            )

        if isinstance(pattern, str):
            pattern = re.compile(pattern)

        if not pattern.search(self.value):
            raise AssertionError(
                f"{self.expression}.matches({repr(pattern.pattern)})",
                expected=f"string matching {repr(pattern.pattern)}",
                actual=repr(self.value),
            )
        return self

    def starts_with(self, prefix: str) -> "ThatAssertion":
        """Assert that the string starts with the prefix."""
        if not isinstance(self.value, str):
            raise AssertionError(
                f"{self.expression}.starts_with({repr(prefix)})",
                expected="string value",
                actual=f"{type(self.value).__name__}",
            )

        if not self.value.startswith(prefix):
            raise AssertionError(
                f"{self.expression}.starts_with({repr(prefix)})",
                expected=f"string starting with {repr(prefix)}",
                actual=repr(self.value),
            )
        return self

    def ends_with(self, suffix: str) -> "ThatAssertion":
        """Assert that the string ends with the suffix."""
        if not isinstance(self.value, str):
            raise AssertionError(
                f"{self.expression}.ends_with({repr(suffix)})",
                expected="string value",
                actual=f"{type(self.value).__name__}",
            )

        if not self.value.endswith(suffix):
            raise AssertionError(
                f"{self.expression}.ends_with({repr(suffix)})",
                expected=f"string ending with {repr(suffix)}",
                actual=repr(self.value),
            )
        return self

    def raises(self, exception_type: Type[Exception]) -> "ThatAssertion":
        """Assert that the callable raises the expected exception type."""
        if not callable(self.value):
            raise AssertionError(
                f"{self.expression}.raises({exception_type.__name__})",
                expected="callable",
                actual=f"{type(self.value).__name__}",
            )

        try:
            self.value()
            raise AssertionError(
                f"{self.expression}.raises({exception_type.__name__})",
                expected=f"{exception_type.__name__}",
                actual="no exception raised",
            )
        except exception_type:
            # Expected exception was raised
            pass
        except Exception as e:
            raise AssertionError(
                f"{self.expression}.raises({exception_type.__name__})",
                expected=f"{exception_type.__name__}",
                actual=f"{type(e).__name__}({repr(str(e))})",
            )
        return self

    def does_not_raise(self) -> "ThatAssertion":
        """Assert that the callable does not raise any exception."""
        if not callable(self.value):
            raise AssertionError(
                f"{self.expression}.does_not_raise()",
                expected="callable",
                actual=f"{type(self.value).__name__}",
            )

        try:
            result = self.value()
            # Return a new assertion for the result
            return ThatAssertion(result, f"{self.expression}()")
        except Exception as e:
            raise AssertionError(
                f"{self.expression}.does_not_raise()",
                expected="no exception",
                actual=f"{type(e).__name__}({repr(str(e))})",
            )

    def is_greater_than(self, value: Union[int, float]) -> "ThatAssertion":
        """Assert that the number is greater than the given value."""
        if not isinstance(self.value, (int, float)):
            raise AssertionError(
                f"{self.expression}.is_greater_than({value})",
                expected="numeric value",
                actual=f"{type(self.value).__name__}",
            )

        if not self.value > value:
            raise AssertionError(
                f"{self.expression}.is_greater_than({value})",
                expected=f"value > {value}",
                actual=self.value,
            )
        return self

    def is_less_than(self, value: Union[int, float]) -> "ThatAssertion":
        """Assert that the number is less than the given value."""
        if not isinstance(self.value, (int, float)):
            raise AssertionError(
                f"{self.expression}.is_less_than({value})",
                expected="numeric value",
                actual=f"{type(self.value).__name__}",
            )

        if not self.value < value:
            raise AssertionError(
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
            raise AssertionError(
                f"{self.expression}.is_between({min_val}, {max_val})",
                expected="numeric value",
                actual=f"{type(self.value).__name__}",
            )

        if not (min_val <= self.value <= max_val):
            raise AssertionError(
                f"{self.expression}.is_between({min_val}, {max_val})",
                expected=f"value between {min_val} and {max_val}",
                actual=self.value,
            )
        return self

    def is_instance_of(self, expected_type: Type) -> "ThatAssertion":
        """Assert that the value is an instance of the expected type."""
        if not isinstance(self.value, expected_type):
            raise AssertionError(
                f"{self.expression}.is_instance_of({expected_type.__name__})",
                expected=f"instance of {expected_type.__name__}",
                actual=f"instance of {type(self.value).__name__}",
            )
        return self

    def has_type(self, expected_type: Type) -> "ThatAssertion":
        """Assert that the value has the exact expected type."""
        if type(self.value) is not expected_type:
            raise AssertionError(
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
            raise AssertionError(
                f"{self.expression}.approximately_equals({expected}, tolerance={tolerance})",
                expected=f"numeric value approximately equal to {expected}",
                actual=f"non-numeric value {repr(self.value)}",
            )

        diff = abs(self.value - expected)
        if diff > tolerance:
            raise AssertionError(
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
            raise AssertionError(
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

            raise AssertionError(
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
            raise AssertionError(
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

            raise AssertionError(
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
        try:
            items = list(self.value)
        except TypeError:
            raise AssertionError(
                f"{self.expression}.are_sorted_by({repr(key_func)})",
                expected="iterable collection",
                actual=f"{type(self.value).__name__} (not iterable)",
            )

        if len(items) <= 1:
            return self  # Single item or empty is always sorted

        # Handle string key (attribute name or dict key) or callable
        if isinstance(key_func, str):

            def get_key(item):
                if isinstance(item, dict):
                    return item[key_func]
                else:
                    return getattr(item, key_func)

        else:
            get_key = key_func

        try:
            sorted_items = sorted(items, key=get_key, reverse=reverse)
        except Exception as e:
            raise AssertionError(
                f"{self.expression}.are_sorted_by({repr(key_func)})",
                expected="sortable items",
                actual=f"Error sorting: {e}",
            )

        if items != sorted_items:
            # Find first out-of-order item
            for i in range(len(items)):
                if items[i] != sorted_items[i]:
                    direction = "descending" if reverse else "ascending"
                    raise AssertionError(
                        f"{self.expression}.are_sorted_by({repr(key_func)})",
                        expected=f"items sorted {direction}",
                        actual=f"item at index {i} is out of order",
                        diff_lines=[
                            f"Expected order: {repr(sorted_items[:5])}{'...' if len(sorted_items) > 5 else ''}",
                            f"Actual order:   {repr(items[:5])}{'...' if len(items) > 5 else ''}",
                            f"First difference at index {i}",
                        ],
                    )
        return self


def that(value: Any) -> ThatAssertion:
    """Create a new assertion for the given value."""
    return ThatAssertion(value)
