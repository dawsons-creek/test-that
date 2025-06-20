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
from .mocking import mock, mock_that
from .replay import replay
from .runner import suite, test
from .tags import integration, requires_db, requires_network, slow, smoke, tag, unit

__version__ = "0.2.0"
__all__ = ["test", "suite", "that", "replay", "tag", "slow", "integration", "unit", "requires_network", "requires_db", "smoke", "mock", "mock_that"]
