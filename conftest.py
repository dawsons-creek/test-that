"""
Project conftest.py - enables That test discovery through pytest.
"""

# Import the pytest compatibility hooks directly
from that.ide.pytest_compat import (
    pytest_collect_file,
    pytest_configure,
    pytest_collection_modifyitems,
    pytest_pycollect_makemodule
)
