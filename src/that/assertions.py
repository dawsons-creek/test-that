"""
Assertion API for the That testing library.

Provides a fluent interface for making assertions about values.
"""

import re
from typing import Any, Pattern, Type, Union, List


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


def _create_dict_diff(expected: dict, actual: dict) -> List[str]:
    """Create detailed diff for dictionaries."""
    lines = ["Dictionary differences:"]

    all_keys = set(expected.keys()) | set(actual.keys())

    for key in sorted(all_keys):
        if key in expected and key in actual:
            if expected[key] == actual[key]:
                lines.append(f"  ✓ {key}: {repr(actual[key])}")
            else:
                lines.append(
                    f"  ✗ {key}: expected {repr(expected[key])}, got {repr(actual[key])}"
                )
        elif key in expected:
            lines.append(f"  - {key} (expected but not found)")
        else:
            lines.append(f"  + {key}: {repr(actual[key])} (not in expected)")

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


def that(value: Any) -> ThatAssertion:
    """Create a new assertion for the given value."""
    return ThatAssertion(value)
