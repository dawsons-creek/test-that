"""
That - A Python Testing Library

Because test output should tell you what failed, not make you guess.

Usage:
    from test_that import test, suite, that

    @test("user age is correct")
    def test_user_age():
        user = {"name": "John", "age": 30}
        that(user["age"]).equals(30)
"""

from .assertions import that
from .runner import test, suite
from .mocking import mock, mock_that
from .with_fixtures import provide

# Initialize plugin system
from .plugins.registry import plugin_registry

def _initialize_plugins():
    """Initialize plugin system."""
    plugin_registry.initialize()

# Initialize plugins on import
_initialize_plugins()

# Import replay API from plugin (will be available if plugin loads successfully)
try:
    from .plugins.replay import replay
    __replay_available__ = ["replay"]
except ImportError:
    __replay_available__ = []

# IDE integration (optional import)
try:
    import importlib.util
    if importlib.util.find_spec("that.ide") is not None:
        from .ide import setup_pycharm_integration  # noqa: F401
        __all_ide__ = ["setup_pycharm_integration"]
    else:
        __all_ide__ = []
except ImportError:
    __all_ide__ = []

__version__ = "0.2.0"
__all__ = ["test", "suite", "that", "mock", "mock_that", "provide"] + __replay_available__ + __all_ide__
