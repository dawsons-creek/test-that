"""
Time freezing functionality for deterministic testing.

Provides both the legacy @frozen_at decorator and the new TimeFreeze class.
"""

import datetime
import functools
from typing import Callable, Union
from unittest.mock import patch

# Constants
NANOSECONDS_PER_SECOND = 1_000_000_000


class TimeFreeze:
    """
    Core time freezing functionality that can be reused by different APIs.
    """
    
    def __init__(self, frozen_time: Union[str, datetime.datetime]):
        """
        Initialize time freezer.
        
        Args:
            frozen_time: Either an ISO string like "2024-01-01T00:00:00Z"
                        or a datetime object
        """
        self.frozen_time = self._parse_time(frozen_time)
    
    def _parse_time(self, frozen_time: Union[str, datetime.datetime]) -> datetime.datetime:
        """Convert string to datetime if needed."""
        if isinstance(frozen_time, str):
            try:
                # Parse ISO format
                if frozen_time.endswith("Z"):
                    return datetime.datetime.fromisoformat(frozen_time[:-1] + "+00:00")
                else:
                    return datetime.datetime.fromisoformat(frozen_time)
            except ValueError as e:
                raise ValueError(f"Invalid ISO datetime string: {frozen_time}") from e
        elif isinstance(frozen_time, datetime.datetime):
            return frozen_time
        else:
            raise TypeError(f"Expected str or datetime, got {type(frozen_time)}")
    
    def freeze_during(self, func: Callable) -> Callable:
        """
        Return a wrapped version of func that executes with frozen time.
        
        Args:
            func: Function to execute with frozen time
            
        Returns:
            Wrapped function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            dt = self.frozen_time
            
            # Create mock return values
            mock_now = dt
            # Fix timezone conversion logic
            mock_utcnow = (
                dt.astimezone(datetime.timezone.utc) if dt.tzinfo
                else dt.replace(tzinfo=datetime.timezone.utc)
            )
            mock_timestamp = dt.timestamp()

            # Store original classes to avoid recursion
            original_datetime = datetime.datetime
            original_date = datetime.date

            # Patch all the common time functions
            with patch("datetime.datetime") as mock_datetime, patch(
                "datetime.date"
            ) as mock_date, patch("time.time", return_value=mock_timestamp), patch(
                "time.time_ns", return_value=int(mock_timestamp * NANOSECONDS_PER_SECOND)
            ), patch("time.gmtime", return_value=mock_utcnow.timetuple()), patch(
                "time.localtime", return_value=mock_now.timetuple()
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



