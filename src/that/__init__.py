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
from .time_freeze import frozen_at
from .http_recording import recorded

__version__ = "0.1.0"
__all__ = ["test", "suite", "that", "frozen_at", "recorded"]
