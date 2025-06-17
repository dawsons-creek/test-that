"""
Time freezing functionality for deterministic testing.

Provides the @frozen_at decorator to freeze time during test execution.
"""

import datetime
import functools
from typing import Callable, Union
from unittest.mock import patch


def frozen_at(frozen_time: Union[str, datetime.datetime]):
    """
    Decorator to freeze time during test execution.

    Args:
        frozen_time: Either an ISO string like "2024-01-01T00:00:00Z"
                    or a datetime object

    Example:
        @test("user created at midnight")
        @frozen_at("2024-01-01T00:00:00Z")
        def test_user_creation():
            user = create_user()
            that(user.created_at).equals(datetime(2024, 1, 1, 0, 0, 0))
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Convert string to datetime if needed
            if isinstance(frozen_time, str):
                # Parse ISO format
                if frozen_time.endswith("Z"):
                    dt = datetime.datetime.fromisoformat(frozen_time[:-1] + "+00:00")
                else:
                    dt = datetime.datetime.fromisoformat(frozen_time)
            else:
                dt = frozen_time

            # Create mock return values
            mock_now = dt
            mock_utcnow = (
                dt.replace(tzinfo=datetime.timezone.utc) if dt.tzinfo is None else dt
            )
            mock_timestamp = dt.timestamp()

            # Store original datetime class to avoid recursion
            original_datetime = datetime.datetime
            original_date = datetime.date

            # Patch all the common time functions
            with patch("datetime.datetime") as mock_datetime, patch(
                "datetime.date"
            ) as mock_date, patch("time.time", return_value=mock_timestamp), patch(
                "time.time_ns", return_value=int(mock_timestamp * 1_000_000_000)
            ):

                # Configure datetime mock to avoid recursion
                mock_datetime.now.return_value = mock_now
                mock_datetime.utcnow.return_value = mock_utcnow
                mock_datetime.today.return_value = mock_now.date()

                # Forward constructor and other methods to original class
                def datetime_constructor(*args, **kwargs):
                    return original_datetime(*args, **kwargs)

                mock_datetime.side_effect = datetime_constructor
                mock_datetime.fromisoformat = original_datetime.fromisoformat
                mock_datetime.fromtimestamp = original_datetime.fromtimestamp
                mock_datetime.strptime = original_datetime.strptime
                mock_datetime.min = original_datetime.min
                mock_datetime.max = original_datetime.max

                # Configure date mock
                mock_date.today.return_value = mock_now.date()

                def date_constructor(*args, **kwargs):
                    return original_date(*args, **kwargs)

                mock_date.side_effect = date_constructor
                mock_date.fromisoformat = original_date.fromisoformat
                mock_date.fromordinal = original_date.fromordinal
                mock_date.min = original_date.min
                mock_date.max = original_date.max

                return func(*args, **kwargs)

        return wrapper

    return decorator
