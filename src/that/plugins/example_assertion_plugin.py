"""
Example assertion plugin to demonstrate plugin extensibility.

This plugin adds custom assertion methods for common testing patterns.
"""

from typing import Dict, Callable, Any
from .base import AssertionPlugin, PluginInfo


class ExampleAssertionPlugin(AssertionPlugin):
    """Example plugin that adds custom assertion methods."""

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="example_assertions",
            version="1.0.0",
            description="Example assertion methods for demonstration",
            dependencies=[],
            optional_dependencies=[]
        )

    def get_assertion_methods(self) -> Dict[str, Callable]:
        """Return custom assertion methods."""
        return {
            'is_email': self._is_email,
            'is_url': self._is_url,
            'is_positive': self._is_positive,
            'is_even': self._is_even,
            'is_odd': self._is_odd,
            'has_length_between': self._has_length_between,
        }

    def _is_email(self, assertion_instance):
        """Assert that the value is a valid email address."""
        import re
        
        value = assertion_instance.value
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        if not isinstance(value, str):
            from ..assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{assertion_instance.expression}.is_email()",
                expected="email string",
                actual=f"{type(value).__name__}: {repr(value)}"
            )
        
        if not re.match(email_pattern, value):
            from ..assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{assertion_instance.expression}.is_email()",
                expected="valid email address",
                actual=value
            )
        
        return assertion_instance

    def _is_url(self, assertion_instance):
        """Assert that the value is a valid URL."""
        import re
        
        value = assertion_instance.value
        url_pattern = r'^https?://[^\s/$.?#].[^\s]*$'
        
        if not isinstance(value, str):
            from ..assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{assertion_instance.expression}.is_url()",
                expected="URL string",
                actual=f"{type(value).__name__}: {repr(value)}"
            )
        
        if not re.match(url_pattern, value):
            from ..assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{assertion_instance.expression}.is_url()",
                expected="valid URL",
                actual=value
            )
        
        return assertion_instance

    def _is_positive(self, assertion_instance):
        """Assert that the value is a positive number."""
        value = assertion_instance.value
        
        if not isinstance(value, (int, float)):
            from ..assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{assertion_instance.expression}.is_positive()",
                expected="number",
                actual=f"{type(value).__name__}: {repr(value)}"
            )
        
        if value <= 0:
            from ..assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{assertion_instance.expression}.is_positive()",
                expected="positive number",
                actual=value
            )
        
        return assertion_instance

    def _is_even(self, assertion_instance):
        """Assert that the value is an even number."""
        value = assertion_instance.value
        
        if not isinstance(value, int):
            from ..assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{assertion_instance.expression}.is_even()",
                expected="integer",
                actual=f"{type(value).__name__}: {repr(value)}"
            )
        
        if value % 2 != 0:
            from ..assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{assertion_instance.expression}.is_even()",
                expected="even number",
                actual=value
            )
        
        return assertion_instance

    def _is_odd(self, assertion_instance):
        """Assert that the value is an odd number."""
        value = assertion_instance.value
        
        if not isinstance(value, int):
            from ..assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{assertion_instance.expression}.is_odd()",
                expected="integer",
                actual=f"{type(value).__name__}: {repr(value)}"
            )
        
        if value % 2 == 0:
            from ..assertions import ThatAssertionError
            raise ThatAssertionError(
                f"{assertion_instance.expression}.is_odd()",
                expected="odd number",
                actual=value
            )
        
        return assertion_instance

    def _has_length_between(self, assertion_instance):
        """Create a method that checks if length is between min and max."""
        def length_between_method(min_length: int, max_length: int):
            value = assertion_instance.value

            if not hasattr(value, '__len__'):
                from ..assertions import ThatAssertionError
                raise ThatAssertionError(
                    f"{assertion_instance.expression}.has_length_between({min_length}, {max_length})",
                    expected="object with length",
                    actual=f"{type(value).__name__}: {repr(value)}"
                )

            actual_length = len(value)
            if not (min_length <= actual_length <= max_length):
                from ..assertions import ThatAssertionError
                raise ThatAssertionError(
                    f"{assertion_instance.expression}.has_length_between({min_length}, {max_length})",
                    expected=f"length between {min_length} and {max_length}",
                    actual=f"length {actual_length}"
                )

            return assertion_instance

        # Return the method directly, not a function that returns a function
        return length_between_method
