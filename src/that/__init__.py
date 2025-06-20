"""
That - A Python Testing Library

Because test output should tell you what failed, not make you guess.

Usage:
    from that import test, suite, that

    @test("user age is correct")
    def test_user_age():
        user = {"name": "John", "age": 30}
        that(user["age"]).equals(30)
"""

from .assertions import that
from .runner import test, suite
from .features.replay import replay
from .mocking import mock, mock_that
from .with_fixtures import provide

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
__all__ = ["test", "suite", "that", "replay", "mock", "mock_that", "provide"] + __all_ide__
