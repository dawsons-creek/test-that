"""
IDE integration module for the That testing library.

This module provides integration with various IDEs and development environments.
Currently supports:
- PyCharm (via pytest compatibility)
- VS Code (future)
- Other IDEs (future)
"""

# PyCharm integration
from .pycharm import setup_pycharm_integration

__all__ = [
    "setup_pycharm_integration"
]
