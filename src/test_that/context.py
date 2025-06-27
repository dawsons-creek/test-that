"""
Context management for test-that framework.

Provides thread-safe and async-safe context isolation for fixtures and test registries,
enabling parallel test execution without global state conflicts.
"""

import contextvars
import threading
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .fixtures import FixtureRegistry
    from .runner import TestRegistry


class TestContext:
    """Encapsulates all test execution context for isolation."""
    
    def __init__(self):
        # Import here to avoid circular imports
        from .fixtures import FixtureRegistry
        from .runner import TestRegistry
        
        self.fixture_registry: 'FixtureRegistry' = FixtureRegistry()
        # Note: TestRegistry is currently global, but this provides
        # the structure for future isolation
    
    def isolated_copy(self) -> 'TestContext':
        """Create an isolated copy for parallel execution."""
        return TestContext()
    
    def clear(self):
        """Clear all context state."""
        self.fixture_registry.clear()


# Context variable for async-safe context tracking
_current_context: contextvars.ContextVar[Optional[TestContext]] = contextvars.ContextVar(
    'test_context', 
    default=None
)


class ContextManager:
    """Manages test contexts for different execution environments."""
    
    def __init__(self):
        self._thread_local = threading.local()
        self._default_context = TestContext()
    
    def get_context(self) -> TestContext:
        """Get the current test context (thread and async safe)."""
        # Try context variable first (async-safe)
        ctx = _current_context.get()
        if ctx:
            return ctx
            
        # Fall back to thread-local storage
        if not hasattr(self._thread_local, 'context'):
            self._thread_local.context = TestContext()
        return self._thread_local.context
    
    def get_default_context(self) -> TestContext:
        """Get the default global context."""
        return self._default_context
    
    def with_isolated_context(self) -> 'IsolatedContextManager':
        """Create an isolated context for test execution."""
        return IsolatedContextManager(TestContext())


class IsolatedContextManager:
    """Context manager for isolated test execution."""
    
    def __init__(self, context: TestContext):
        self.context = context
        self.token = None
    
    def __enter__(self) -> TestContext:
        self.token = _current_context.set(self.context)
        return self.context
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.token:
            _current_context.reset(self.token)


# Global context manager
_context_manager = ContextManager()


def get_current_context() -> TestContext:
    """Get the current test context (context-aware)."""
    return _context_manager.get_context()


def get_default_context() -> TestContext:
    """Get the default global context."""
    return _context_manager.get_default_context()


def with_isolated_context() -> IsolatedContextManager:
    """Create an isolated context for parallel test execution.
    
    Usage:
        with with_isolated_context() as ctx:
            # All fixture registrations and test execution
            # happen in isolation
            runner = TestRunner(context=ctx)
            results = runner.run_all()
    """
    return _context_manager.with_isolated_context()


def clear_all_contexts():
    """Clear all context state (useful for testing the framework itself)."""
    _context_manager.get_default_context().clear()
    # Clear thread-local contexts
    if hasattr(_context_manager._thread_local, 'context'):
        _context_manager._thread_local.context.clear()