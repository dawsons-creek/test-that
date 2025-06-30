"""
Fixture system for test-that testing framework.

Provides dependency injection for test setup and teardown with
context isolation for parallel test execution.
"""

import inspect
from typing import Any, Callable, Dict, Generator, Literal, Optional, Set

Scope = Literal["function", "suite"]


class Fixture:
    """Represents a test fixture with setup and optional teardown."""

    def __init__(self, name: str, func: Callable[..., Any], scope: Scope = "function"):
        self.name = name
        self.func = func
        self.scope: Scope = scope
        self.cached_value: Optional[Any] = None
        self.is_cached = False
        self._generator: Optional[Generator] = None

    def get_value(self) -> Any:
        """Get the fixture value, handling generators for teardown."""
        if self.scope == "suite" and self.is_cached:
            return self.cached_value

        if inspect.isgeneratorfunction(self.func):
            generator = self.func()
            value = next(generator)
            self._generator = generator

            if self.scope == "suite":
                self.cached_value = value
                self.is_cached = True

            return value
        else:
            value = self.func()
            if self.scope == "suite":
                self.cached_value = value
                self.is_cached = True
            return value

    def teardown(self):
        """Run teardown if this is a generator fixture."""
        if self._generator:
            try:
                next(self._generator)
            except StopIteration:
                pass
            finally:
                self._generator = None

        if self.scope == "suite":
            self.cached_value = None
            self.is_cached = False


class FixtureRegistry:
    """Registry for managing fixtures."""

    def __init__(self):
        self.fixtures: Dict[str, Fixture] = {}
        self._resolution_cache: Dict[str, Any] = {}
        self._active_fixtures: Set[str] = set()

    def register(self, name: str, func: Callable, scope: str = "function"):
        """Register a fixture."""
        if name in self.fixtures:
            raise ValueError(f"Fixture with name '{name}' already exists.")
        if scope not in ("function", "suite"):
            raise ValueError(
                f"Invalid fixture scope: '{scope}'. Must be 'function' or 'suite'."
            )
        self.fixtures[name] = Fixture(name, func, scope)

    def resolve_fixtures(self, func: Callable) -> Dict[str, Any]:
        """Resolve fixture dependencies for a test function."""
        sig = inspect.signature(func)
        resolved = {}

        for param_name in sig.parameters:
            if param_name in self.fixtures:
                resolved[param_name] = self._get_fixture_value(param_name)

        return resolved

    def _get_fixture_value(self, name: str) -> Any:
        """Get a fixture value, resolving dependencies."""
        if name not in self.fixtures:
            raise ValueError(
                f"Unknown fixture: '{name}'. Available fixtures: {list(self.fixtures.keys())}"
            )

        if name in self._active_fixtures:
            raise ValueError(
                f"Circular dependency detected: {' -> '.join(list(self._active_fixtures) + [name])}"
            )

        fixture = self.fixtures[name]

        # For suite fixtures, check cache first
        if fixture.scope == "suite" and fixture.is_cached:
            return fixture.cached_value

        # For function fixtures, check if we're in the same test context
        if fixture.scope == "function" and hasattr(fixture, "_current_test_value"):
            return fixture._current_test_value

        # Resolve fixture dependencies
        self._active_fixtures.add(name)
        try:
            # Check if fixture function needs other fixtures
            fixture_deps = self.resolve_fixtures(fixture.func)

            if fixture_deps:
                # Create a wrapper that injects dependencies
                original_func = fixture.func

                def wrapper():
                    return original_func(**fixture_deps)

                # Temporarily replace the function
                fixture.func = wrapper
                value = fixture.get_value()
                fixture.func = original_func
            else:
                value = fixture.get_value()

            # Cache function-scoped fixtures for the current test
            if fixture.scope == "function":
                fixture._current_test_value = value

            return value
        finally:
            self._active_fixtures.remove(name)

    def teardown_function_fixtures(self):
        """Teardown all function-scoped fixtures."""
        for fixture in self.fixtures.values():
            if fixture.scope == "function":
                fixture.teardown()
                # Clear test-level cache
                if hasattr(fixture, "_current_test_value"):
                    delattr(fixture, "_current_test_value")

    def teardown_suite_fixtures(self):
        """Teardown all suite-scoped fixtures."""
        for fixture in self.fixtures.values():
            if fixture.scope == "suite":
                fixture.teardown()

    def clear(self):
        """Clear all fixtures."""
        for fixture in self.fixtures.values():
            fixture.teardown()
        self.fixtures.clear()
        self._resolution_cache.clear()
        self._active_fixtures.clear()


# Legacy global fixture registry (for backwards compatibility)
_legacy_fixture_registry = FixtureRegistry()


def fixture(scope: Scope = "function", *, context_aware: bool = True):
    """
    Decorator to register a test fixture.

    Args:
        scope: "function" (default) or "suite"
        context_aware: If True, uses current context for isolation (default: True)

    Usage:
        @fixture()
        def database():
            db = Database()
            yield db
            db.cleanup()

        @fixture(scope="suite")
        def shared_resource():
            return expensive_setup()

        @test("uses database")
        def test_with_db(database):
            that(database.is_connected()).is_true()

        # For legacy compatibility (uses global registry)
        @fixture(context_aware=False)
        def legacy_fixture():
            return "legacy"
    """

    def decorator(func: Callable[..., Any]):
        name = func.__name__

        if context_aware:
            # Use current context (thread/async safe) - import here to avoid circular imports
            from .context import get_current_context

            registry = get_current_context().fixture_registry
        else:
            # Use legacy global registry
            registry = _legacy_fixture_registry

        registry.register(name, func, scope)
        return func

    return decorator


def get_fixture_registry(*, context_aware: bool = True) -> FixtureRegistry:
    """Get the fixture registry.

    Args:
        context_aware: If True, uses current context registry (default: True)
                      If False, uses legacy global registry
    """
    if context_aware:
        from .context import get_current_context

        return get_current_context().fixture_registry
    else:
        return _legacy_fixture_registry


def get_legacy_fixture_registry() -> FixtureRegistry:
    """Get the legacy global fixture registry (backwards compatibility)."""
    return _legacy_fixture_registry


def clear_fixture_registry(*, context_aware: bool = True):
    """Clear the fixture registry.

    Args:
        context_aware: If True, clears current context registry (default: True)
                      If False, clears legacy global registry
    """
    if context_aware:
        from .context import get_current_context

        get_current_context().fixture_registry.clear()
    else:
        _legacy_fixture_registry.clear()


def clear_all_fixture_registries():
    """Clear all fixture registries (useful for testing)."""
    from .context import get_current_context, get_default_context

    _legacy_fixture_registry.clear()
    get_current_context().fixture_registry.clear()
    get_default_context().fixture_registry.clear()
