"""
Unified replay functionality for deterministic testing.

Provides time freezing and HTTP recording/replay through a single, clean API.
"""

import datetime
import functools
import warnings
from pathlib import Path
from typing import Any, Callable, Optional, Union

from .time_freeze import TimeFreeze
from .http_recording import HTTPRecorder


class ReplayConfig:
    """Configuration for the replay system."""

    def __init__(self, recordings_dir: str = "tests/recordings"):
        self.recordings_dir = recordings_dir
        self.time_format = "iso"
        self.http_timeout = 30

    def get_recordings_path(self) -> Path:
        """Get the recordings directory as a Path object."""
        return Path(self.recordings_dir)


class TimeContextOrDecorator:
    """Dual-purpose object that can be used as both decorator and context manager."""

    def __init__(self, replay_instance, frozen_time: Union[str, Any]):
        self.replay = replay_instance
        self.frozen_time = frozen_time
        self.old_time = None
        self._time_freezer = None

    def __call__(self, func: Callable) -> Callable:
        """When used as decorator: @replay.time(...)"""
        return self.replay._time_decorator(self.frozen_time)(func)

    def __enter__(self):
        """When used as context manager: with replay.time(...)"""
        try:
            self._setup_context_state()
            self._setup_time_freezing()
            return self
        except Exception as e:
            raise RuntimeError(f"Failed to enter time context: {e}") from e

    def _setup_context_state(self):
        """Setup the context state for the replay system."""
        self.old_time = self.replay._context_time
        self.replay._context_time = self.frozen_time
        self.replay._context_stack.append(self.frozen_time)

    def _setup_time_freezing(self):
        """Setup time freezing patches."""
        self._time_freezer = TimeFreeze(self.frozen_time)
        dt = self._time_freezer.frozen_time

        mock_values = self._create_mock_time_values(dt)
        self._create_and_start_patches(mock_values)
        self._configure_datetime_mocks(mock_values)

    def _create_mock_time_values(self, dt: datetime.datetime) -> dict:
        """Create mock time values for patching."""
        return {
            'now': dt,
            'utcnow': (
                dt.astimezone(datetime.timezone.utc) if dt.tzinfo
                else dt.replace(tzinfo=datetime.timezone.utc)
            ),
            'timestamp': dt.timestamp()
        }

    def _create_and_start_patches(self, mock_values: dict):
        """Create and start all time-related patches."""
        from unittest.mock import patch
        from that.time_freeze import NANOSECONDS_PER_SECOND

        self._datetime_patch = patch("datetime.datetime")
        self._date_patch = patch("datetime.date")
        self._time_patch = patch("time.time", return_value=mock_values['timestamp'])
        self._time_ns_patch = patch(
            "time.time_ns", 
            return_value=int(mock_values['timestamp'] * NANOSECONDS_PER_SECOND)
        )
        self._gmtime_patch = patch("time.gmtime", return_value=mock_values['utcnow'].timetuple())
        self._localtime_patch = patch("time.localtime", return_value=mock_values['now'].timetuple())

        # Start all patches
        self._mock_datetime = self._datetime_patch.start()
        self._mock_date = self._date_patch.start()
        self._time_patch.start()
        self._time_ns_patch.start()
        self._gmtime_patch.start()
        self._localtime_patch.start()

    def _configure_datetime_mocks(self, mock_values: dict):
        """Configure datetime and date mocks with proper forwarding."""
        import datetime as dt_module

        # Store originals to avoid recursion
        original_datetime = dt_module.datetime
        original_date = dt_module.date

        # Configure datetime mock
        self._mock_datetime.now.return_value = mock_values['now']
        self._mock_datetime.utcnow.return_value = mock_values['utcnow']
        self._mock_datetime.today.return_value = mock_values['now'].date()

        # Forward constructor and methods
        self._mock_datetime.side_effect = lambda *a, **k: original_datetime(*a, **k)
        self._mock_datetime.fromisoformat = original_datetime.fromisoformat
        self._mock_datetime.fromtimestamp = original_datetime.fromtimestamp
        self._mock_datetime.strptime = original_datetime.strptime
        self._mock_datetime.min = original_datetime.min
        self._mock_datetime.max = original_datetime.max

        # Configure date mock
        self._mock_date.today.return_value = mock_values['now'].date()
        self._mock_date.side_effect = lambda *a, **k: original_date(*a, **k)
        self._mock_date.fromisoformat = original_date.fromisoformat
        self._mock_date.fromordinal = original_date.fromordinal
        self._mock_date.min = original_date.min
        self._mock_date.max = original_date.max

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context manager."""
        try:
            # Stop all patches
            if hasattr(self, '_datetime_patch'):
                self._datetime_patch.stop()
            if hasattr(self, '_date_patch'):
                self._date_patch.stop()
            if hasattr(self, '_time_patch'):
                self._time_patch.stop()
            if hasattr(self, '_time_ns_patch'):
                self._time_ns_patch.stop()
            if hasattr(self, '_gmtime_patch'):
                self._gmtime_patch.stop()
            if hasattr(self, '_localtime_patch'):
                self._localtime_patch.stop()

            if self.replay._context_stack:
                self.replay._context_stack.pop()
            self.replay._context_time = self.old_time
        except Exception as e:
            # Don't raise in __exit__ unless it's critical
            warnings.warn(f"Error exiting time context: {e}", RuntimeWarning)


class Replay:
    """
    Main replay interface providing time and HTTP control.

    Usage patterns:
        @replay.time("2024-01-01T00:00:00Z")
        @replay.http("user_fetch")
        @replay(time="2024-01-01T00:00:00Z", http="user_signup")

        with replay.time("2024-01-01T00:00:00Z"):
            # Multiple tests at same frozen time
    """

    def __init__(self, config: Optional[ReplayConfig] = None):
        self._context_time = None
        self._context_stack = []
        self.config = config or ReplayConfig()
    
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
        # Check if being used in a 'with' statement context by looking at the call stack
        # For simplicity, we'll return a special object that can be both decorator and context manager
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
        return self._http_decorator(cassette_name, mode)
    
    def __call__(self, time: Optional[Union[str, Any]] = None, 
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
                decorated_func = self._time_decorator(time)(decorated_func)
            
            if http is not None:
                decorated_func = self._http_decorator(http, mode)(decorated_func)
                
            return decorated_func
        
        return decorator
    
    def _time_decorator(self, frozen_time: Union[str, Any]):
        """Create time freezing decorator."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    # Use context time if available, otherwise use specified time
                    effective_time = self._context_time if self._context_time else frozen_time
                    freezer = TimeFreeze(effective_time)
                    frozen_func = freezer.freeze_during(func)
                    return frozen_func(*args, **kwargs)
                except Exception as e:
                    raise RuntimeError(f"Time freezing failed for {func.__name__}: {e}") from e
            return wrapper
        return decorator
    
    def _http_decorator(self, cassette_name: str, mode: str = "once"):
        """Create HTTP recording decorator."""
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    recorder = HTTPRecorder(
                        cassette_name,
                        mode,
                        recordings_dir=self.config.recordings_dir
                    )
                    recorded_func = recorder.record_during(func)

                    # Check for context time at execution time
                    if self._context_time:
                        freezer = TimeFreeze(self._context_time)
                        time_frozen_func = freezer.freeze_during(recorded_func)
                        return time_frozen_func(*args, **kwargs)
                    else:
                        return recorded_func(*args, **kwargs)
                except Exception as e:
                    raise RuntimeError(f"HTTP recording failed for {func.__name__}: {e}") from e
            return wrapper
        return decorator
    


# Create singleton instance
replay = Replay()


