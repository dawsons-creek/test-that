"""
@with_ decorator for creating test fixtures - simplified approach.

Provides a clear, explicit way to create mocks and test data without magic.
"""

import sys
from typing import Any, Callable, Dict


class FixtureRegistry:
    """Global registry for fixtures."""

    def __init__(self):
        self._fixtures: Dict[str, Callable] = {}
        self._cache: Dict[str, Any] = {}

    def register_fixture(self, name: str, factory: Callable):
        """Register a fixture factory function."""
        self._fixtures[name] = factory

    def get_fixture_value(self, name: str) -> Any:
        """Get fixture value, creating it if needed (once per test)."""
        if name not in self._cache:
            if name not in self._fixtures:
                raise NameError(f"Fixture '{name}' not found. Did you forget @with_?")
            
            factory = self._fixtures[name]
            self._cache[name] = factory()
        
        return self._cache[name]

    def clear_cache(self):
        """Clear fixture cache (called before each test)."""
        self._cache.clear()

    def clear_all(self):
        """Clear all fixtures and cache."""
        self._fixtures.clear()
        self._cache.clear()


# Global fixture registry
_fixture_registry = FixtureRegistry()


class FixtureProxy:
    """Proxy object that lazily evaluates fixtures when accessed."""
    
    def __init__(self, name: str):
        self.name = name

    def __getattr__(self, attr):
        """Forward attribute access to the fixture value."""
        value = _fixture_registry.get_fixture_value(self.name)
        return getattr(value, attr)
    
    def __getitem__(self, key):
        """Forward item access to the fixture value."""
        value = _fixture_registry.get_fixture_value(self.name)
        return value[key]
    
    def __setitem__(self, key, value):
        """Forward item assignment to the fixture value."""
        fixture_value = _fixture_registry.get_fixture_value(self.name)
        fixture_value[key] = value
    
    def __iter__(self):
        """Forward iteration to the fixture value."""
        value = _fixture_registry.get_fixture_value(self.name)
        return iter(value)
    
    def __len__(self):
        """Forward len() to the fixture value."""
        value = _fixture_registry.get_fixture_value(self.name)
        return len(value)
    
    def __call__(self, *args, **kwargs):
        """Forward function calls to the fixture value."""
        value = _fixture_registry.get_fixture_value(self.name)
        return value(*args, **kwargs)
    
    def __str__(self):
        """Forward string representation to the fixture value."""
        value = _fixture_registry.get_fixture_value(self.name)
        return str(value)
    
    def __repr__(self):
        """Forward repr to the fixture value."""
        value = _fixture_registry.get_fixture_value(self.name)
        return repr(value)
    
    def __eq__(self, other):
        """Forward equality comparison to the fixture value."""
        value = _fixture_registry.get_fixture_value(self.name)
        return value == other
    
    def __ne__(self, other):
        """Forward inequality comparison to the fixture value."""
        value = _fixture_registry.get_fixture_value(self.name)
        return value != other
    
    def __bool__(self):
        """Forward boolean evaluation to the fixture value."""
        value = _fixture_registry.get_fixture_value(self.name)
        return bool(value)


def provide(func: Callable) -> FixtureProxy:
    """
    Decorator to provide test data/fixtures.
    
    Usage:
        @provide
        def mock_user():
            return {"name": "John", "email": "john@example.com"}
        
        @test("should create user")
        def test_user_creation():
            # mock_user is available here - fresh instance per test
            that(mock_user["name"]).equals("John")
    """
    # Get the fixture name from the function
    fixture_name = func.__name__
    
    # Register the fixture factory
    _fixture_registry.register_fixture(fixture_name, func)
    
    # Create a proxy and install it in the calling module's namespace
    proxy = FixtureProxy(fixture_name)
    
    # Install the proxy in the calling module's globals
    frame = sys._getframe(1)
    calling_module = frame.f_globals
    calling_module[fixture_name] = proxy
    
    # Also try to update locals if we're in a function/suite context
    if frame.f_locals is not calling_module:
        frame.f_locals[fixture_name] = proxy
    
    return proxy


def clear_fixture_cache():
    """Clear fixture cache (called before each test)."""
    _fixture_registry.clear_cache()


def clear_all_fixtures():
    """Clear all fixtures and cache."""
    _fixture_registry.clear_all()