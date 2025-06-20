"""
Advanced features module for the That testing library.

This module contains optional advanced features like:
- HTTP recording and replay
- Time freezing utilities  
- Snapshot testing
- Other experimental features
"""

# Import advanced features
from .replay import replay
from .http_recording import HTTPRecorder
from .time_freeze import TimeFreeze

__all__ = [
    "replay",
    "HTTPRecorder",
    "TimeFreeze",
]
