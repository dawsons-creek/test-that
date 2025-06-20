"""
Unified replay API backed by the replay plugin.
"""

from typing import Union, Optional, Any, Callable
from ..registry import plugin_registry


class TimeContextOrDecorator:
    """Helper class that can be used as both context manager and decorator."""

    def __init__(self, replay_instance, frozen_time):
        self.replay_instance = replay_instance
        self.frozen_time = frozen_time
        self._time_freezer = None

    def __call__(self, func):
        """Use as decorator."""
        return self.replay_instance._get_time_decorator()(self.frozen_time)(func)

    def __enter__(self):
        """Use as context manager."""
        from .time_freeze import TimeFreeze
        self._time_freezer = TimeFreeze(self.frozen_time)

        # Apply the time freeze patches
        import datetime
        from unittest.mock import patch

        dt = self._time_freezer.frozen_time
        mock_now = dt
        mock_utcnow = (
            dt.astimezone(datetime.timezone.utc) if dt.tzinfo
            else dt.replace(tzinfo=datetime.timezone.utc)
        )
        mock_timestamp = dt.timestamp()

        # Store original classes to avoid recursion
        original_datetime = datetime.datetime
        original_date = datetime.date

        # Create mock classes
        class MockDateTime(original_datetime):
            @classmethod
            def now(cls, tz=None):
                if tz is None:
                    return mock_now
                return mock_now.astimezone(tz)

            @classmethod
            def utcnow(cls):
                return mock_utcnow

            @classmethod
            def today(cls):
                return mock_now.date()

            def timestamp(self):
                return mock_timestamp

        class MockDate(original_date):
            @classmethod
            def today(cls):
                return mock_now.date()

        # Apply patches
        self._patches = [
            patch('datetime.datetime', MockDateTime),
            patch('datetime.date', MockDate),
        ]

        for p in self._patches:
            p.start()

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        if self._patches:
            for p in self._patches:
                p.stop()
            self._patches = None


class Replay:
    """Unified replay API backed by plugins."""

    def __init__(self):
        self._decorators = {}
        self._context_time = None
        self._load_decorators()

    def _load_decorators(self):
        """Load decorators from plugins."""
        # Ensure plugins are initialized
        plugin_registry.initialize()
        self._decorators = plugin_registry.get_decorators()

    def _get_time_decorator(self):
        """Get the time decorator from plugins."""
        if 'time' not in self._decorators:
            self._load_decorators()  # Try reloading in case plugins weren't ready
        
        if 'time' in self._decorators:
            return self._decorators['time']
        else:
            raise RuntimeError("Time freeze functionality not available - replay plugin not loaded")

    def _get_http_decorator(self):
        """Get the HTTP decorator from plugins."""
        if 'http' not in self._decorators:
            self._load_decorators()  # Try reloading in case plugins weren't ready
            
        if 'http' in self._decorators:
            return self._decorators['http']
        else:
            raise RuntimeError("HTTP recording functionality not available - replay plugin not loaded or missing dependencies (pyyaml, requests)")

    def time(self, frozen_time: Union[str, Any]):
        """
        Freeze time during test execution.
        
        Can be used as decorator or context manager.
        
        Args:
            frozen_time: ISO string like "2024-01-01T00:00:00Z" or datetime object
            
        Example:
            @test("user created at midnight")
            @replay.time("2024-01-01T00:00:00Z")
            def test_user_creation():
                user = create_user()
                that(user.created_at).equals(datetime(2024, 1, 1, 0, 0, 0))
                
            # Or as context manager:
            with replay.time("2024-01-01T00:00:00Z"):
                # tests here run at frozen time
        """
        return TimeContextOrDecorator(self, frozen_time)

    def http(self, cassette_name: str, mode: str = "once"):
        """
        Record/replay HTTP requests during test execution.
        
        Args:
            cassette_name: Name of the recording file (without .yaml extension)
            mode: "once" (default), "record", or "replay_only"
            
        Example:
            @test("fetches user from API")
            @replay.http("user_fetch")
            def test_fetch_user():
                response = requests.get("https://api.example.com/user/123")
                that(response.json()["name"]).equals("John Doe")
        """
        http_decorator = self._get_http_decorator()
        return http_decorator(cassette_name, mode)

    def __call__(self, *, time: Optional[Union[str, Any]] = None, 
                 http: Optional[str] = None, mode: str = "once"):
        """
        Combined time and HTTP control.
        
        Args:
            time: Time to freeze (ISO string or datetime)
            http: HTTP cassette name
            mode: Recording mode for HTTP
            
        Example:
            @test("complete user signup flow")
            @replay(time="2024-01-01T12:00:00Z", http="user_signup")
            def test_signup_flow():
                response = signup_user("john@example.com")
                user = User.from_api_response(response)
                that(user.created_at).equals(datetime(2024, 1, 1, 12, 0, 0))
        """
        def decorator(func: Callable) -> Callable:
            # Apply decorators in order (time first, then http)
            decorated_func = func
            
            if time is not None:
                time_decorator = self._get_time_decorator()
                decorated_func = time_decorator(time)(decorated_func)
            
            if http is not None:
                http_decorator = self._get_http_decorator()
                decorated_func = http_decorator(http, mode)(decorated_func)
                
            return decorated_func
        
        return decorator


# Create singleton instance
replay = Replay()
