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
from .context import with_isolated_context
from .fixtures import fixture
from .mocking import mock, mock_that
from .parametrize import parametrize
from .replay import replay
from .runner import suite, test

__version__ = "0.2.0"
__all__ = ["test", "suite", "that", "fixture", "parametrize", "replay", "mock", "mock_that", "with_isolated_context"]
