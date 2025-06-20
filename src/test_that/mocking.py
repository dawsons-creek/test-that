"""
Simple mocking functionality for the That testing library.

Encourages dependency injection and good testing practices.
"""

import functools
from typing import Any, Callable, List, Optional, Union


class MockCall:
    """Represents a single call to a mocked method."""

    def __init__(self, args: tuple, kwargs: dict):
        self.args = args
        self.kwargs = kwargs

    def __eq__(self, other):
        if isinstance(other, MockCall):
            return self.args == other.args and self.kwargs == other.kwargs
        return False

    def __repr__(self):
        args_str = ", ".join(repr(arg) for arg in self.args)
        kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in self.kwargs.items())
        all_args = ", ".join(filter(None, [args_str, kwargs_str]))
        return f"MockCall({all_args})"


class Mock:
    """A mock object that tracks calls and provides verification."""

    def __init__(self, name: str, return_value: Any = None,
                 side_effect: Union[List[Any], Exception, Callable] = None,
                 raises: Optional[Exception] = None):
        self.name = name
        self.return_value = return_value
        self.side_effect = side_effect
        self.raises = raises
        self.calls: List[MockCall] = []
        self._side_effect_iter = None

        if isinstance(side_effect, list):
            self._side_effect_iter = iter(side_effect)

    def __call__(self, *args, **kwargs):
        """Record the call and return configured value."""
        self.calls.append(MockCall(args, kwargs))

        if self.raises:
            raise self.raises

        if self._side_effect_iter:
            try:
                return next(self._side_effect_iter)
            except StopIteration:
                raise ValueError(f"Mock '{self.name}' exhausted side_effect values")

        if callable(self.side_effect):
            return self.side_effect(*args, **kwargs)

        return self.return_value

    def assert_called_with(self, *args, **kwargs):
        """Assert the mock was called with specific arguments."""
        expected = MockCall(args, kwargs)

        if not self.calls:
            raise AssertionError(f"Mock '{self.name}' was never called")

        if expected not in self.calls:
            calls_str = "\n  ".join(str(call) for call in self.calls)
            raise AssertionError(
                f"Mock '{self.name}' was not called with {expected}\n"
                f"Actual calls:\n  {calls_str}"
            )

        return self

    def assert_not_called(self):
        """Assert the mock was never called."""
        if self.calls:
            calls_str = "\n  ".join(str(call) for call in self.calls)
            raise AssertionError(
                f"Mock '{self.name}' was called {len(self.calls)} time(s):\n  {calls_str}"
            )

        return self

    @property
    def call_count(self) -> int:
        """Number of times the mock was called."""
        return len(self.calls)

    def assert_called_once(self):
        """Assert the mock was called exactly once."""
        if self.call_count != 1:
            raise AssertionError(
                f"Mock '{self.name}' was called {self.call_count} time(s), expected 1"
            )
        return self

    def assert_called_times(self, count: int):
        """Assert the mock was called exactly 'count' times."""
        if self.call_count != count:
            raise AssertionError(
                f"Mock '{self.name}' was called {self.call_count} time(s), expected {count}"
            )
        return self

    @property
    def last_call(self) -> Optional[MockCall]:
        """Get the arguments from the most recent call."""
        return self.calls[-1] if self.calls else None

    @property
    def first_call(self) -> Optional[MockCall]:
        """Get the arguments from the first call."""
        return self.calls[0] if self.calls else None

    def get_call(self, index: int) -> MockCall:
        """Get the arguments from a specific call by index."""
        if not self.calls:
            raise IndexError(f"Mock '{self.name}' has no calls")

        try:
            return self.calls[index]
        except IndexError:
            raise IndexError(
                f"Mock '{self.name}' call index {index} out of range (0-{len(self.calls)-1})"
            )


class MockContext:
    """Context for tracking active mocks for cleanup."""

    def __init__(self):
        self.active_mocks: List[tuple] = []

    def add_mock(self, obj: Any, attr_name: str, original: Any):
        """Track a mock for later cleanup."""
        self.active_mocks.append((obj, attr_name, original))

    def cleanup(self):
        """Restore all mocked attributes."""
        for obj, attr_name, original in self.active_mocks:
            if original is _DELETED:
                delattr(obj, attr_name)
            else:
                setattr(obj, attr_name, original)
        self.active_mocks.clear()


# Sentinel for deleted attributes
_DELETED = object()

# Global mock context
_mock_context = MockContext()


def mock(obj: Any, attr_name: str, *,
         return_value: Any = None,
         side_effect: Union[List[Any], Exception, Callable] = None,
         raises: Optional[Exception] = None) -> Mock:
    """
    Replace an attribute with a mock object.
    
    Args:
        obj: The object to mock an attribute on
        attr_name: Name of the attribute to replace
        return_value: Value to return when mock is called
        side_effect: List of values to return in sequence, callable, or exception
        raises: Exception to raise when mock is called
    
    Returns:
        Mock object for verification (supports method chaining)
    
    Example:
        # Common pattern: Mock an injected dependency
        from test_that import test, that, mock
        
        @test("user service fetches data correctly")
        def test_user_service():
            service = UserService(api_client)
            
            # Mock the dependency and chain verifications
            api_mock = mock(api_client, 'get_user', return_value={'id': 1, 'name': 'John'})
            
            result = service.get_user_profile(1)
            
            # Fluent verification
            api_mock.assert_called_once().assert_called_with('/users/1')
            that(result['name']).equals('John')
    """
    # Get original value for cleanup
    original = getattr(obj, attr_name, _DELETED)

    # Create mock
    mock_obj = Mock(
        name=f"{obj.__class__.__name__}.{attr_name}",
        return_value=return_value,
        side_effect=side_effect,
        raises=raises
    )

    # Replace attribute
    setattr(obj, attr_name, mock_obj)

    # Track for cleanup
    _mock_context.add_mock(obj, attr_name, original)

    return mock_obj


def cleanup_mocks():
    """Clean up all active mocks. Called automatically after each test."""
    _mock_context.cleanup()


def mock_that(mock_obj: Mock):
    """
    Create assertion wrapper for a mock object that integrates with that() API.
    
    Args:
        mock_obj: The mock object to create assertions for
    
    Returns:
        Object with assertion methods that integrate with that()
    
    Example:
        api_mock = mock(client, 'get', return_value={'data': 'test'})
        client.get('/users')
        
        # Can use with that() for more complex assertions
        from test_that import that
        that(mock_that(api_mock).call_count).equals(1)
        that(mock_that(api_mock).last_call.args).contains('/users')
    """

    class MockAssertions:
        def __init__(self, mock_obj: Mock):
            self._mock = mock_obj

        @property
        def call_count(self) -> int:
            return self._mock.call_count

        @property
        def calls(self) -> List[MockCall]:
            return self._mock.calls

        @property
        def last_call(self) -> Optional[MockCall]:
            return self._mock.last_call

        @property
        def first_call(self) -> Optional[MockCall]:
            return self._mock.first_call

        def get_call(self, index: int) -> MockCall:
            return self._mock.get_call(index)

    return MockAssertions(mock_obj)


# Integration with test runner
def _wrap_test_for_mocking(test_func: Callable) -> Callable:
    """Wrap a test function to ensure mock cleanup."""
    @functools.wraps(test_func)
    def wrapped(*args, **kwargs):
        try:
            return test_func(*args, **kwargs)
        finally:
            cleanup_mocks()

    return wrapped
