"""
Pytest compatibility layer for That testing framework.

This module makes That tests discoverable and runnable by pytest,
which enables PyCharm integration since PyCharm has built-in pytest support.
"""

import pytest
from pathlib import Path
from typing import Generator

from ..runner import get_registry, clear_registry, TestRunner
from ..assertions import ThatAssertionError
from ..__main__ import load_test_file


class ThatTestItem(pytest.Item):
    """Pytest test item for That tests."""

    def __init__(self, name: str, parent, test_func=None, test_description: str = ""):
        super().__init__(name, parent)
        self.test_func = test_func
        self.test_description = test_description
        self._nodeid = f"{parent.path}::{name}"

    @classmethod
    def from_parent(cls, parent, *, name: str, test_func, test_description: str):
        """Create ThatTestItem using modern pytest API."""
        item = cls.__new__(cls)
        super(ThatTestItem, item).__init__(name, parent)
        item.test_func = test_func
        item.test_description = test_description
        item._nodeid = f"{parent.path}::{name}"
        return item
    
    def runtest(self):
        """Run the That test."""
        # Ensure clean state for each test
        from ..with_fixtures import clear_fixture_cache
        from ..mocking import cleanup_mocks

        clear_fixture_cache()
        cleanup_mocks()

        runner = TestRunner()
        result = runner.run_test(self.test_description, self.test_func)

        if not result.passed and result.error:
            # Convert That assertion errors to pytest-compatible format
            if isinstance(result.error, ThatAssertionError):
                # Create a more detailed pytest failure
                pytest.fail(self._format_that_error(result.error), pytrace=False)
            else:
                raise result.error
    
    def _format_that_error(self, error: ThatAssertionError) -> str:
        """Format That assertion error for pytest display."""
        lines = [error.message]
        
        if hasattr(error, 'diff_lines') and error.diff_lines:
            lines.append("")
            lines.extend(error.diff_lines)
        elif hasattr(error, 'expected') and hasattr(error, 'actual'):
            lines.append("")
            lines.append(f"Expected: {error.expected}")
            lines.append(f"Actual:   {error.actual}")
        
        return "\n".join(lines)
    
    def repr_failure(self, excinfo):
        """Custom failure representation."""
        if hasattr(excinfo, 'value') and isinstance(excinfo.value, pytest.fail.Exception):
            return str(excinfo.value)
        return super().repr_failure(excinfo)


class ThatTestFile(pytest.File):
    """Pytest file collector for That test files."""

    def collect(self) -> Generator[ThatTestItem, None, None]:
        """Collect That tests from this file."""
        # Clear registry and load this specific file
        clear_registry()

        try:
            load_test_file(Path(self.path))
        except Exception:
            # If file can't be loaded, skip it
            return
        
        registry = get_registry()
        
        # Collect standalone tests
        for test_name, test_func, line_number in registry.standalone_tests:
            if self._is_from_this_file(test_func):
                yield ThatTestItem.from_parent(
                    parent=self,
                    name=test_func.__name__,
                    test_func=test_func,
                    test_description=test_name
                )
        
        # Collect suite tests
        for suite_name, suite in registry.suites.items():
            for test_name, test_func, line_number in suite.tests:
                if self._is_from_this_file(test_func):
                    # Create a nested item name for suite tests
                    item_name = f"{suite_name}::{test_func.__name__}"
                    yield ThatTestItem.from_parent(
                        parent=self,
                        name=item_name,
                        test_func=test_func,
                        test_description=test_name
                    )
    
    def _is_from_this_file(self, test_func) -> bool:
        """Check if test function is from this file."""
        try:
            import inspect
            func_file = inspect.getfile(test_func)
            return Path(func_file).resolve() == Path(self.path).resolve()
        except (OSError, TypeError):
            return False


def pytest_collect_file(file_path, parent):
    """Pytest hook to collect That test files."""
    if file_path.suffix == ".py":
        # Check if file contains That tests
        if _is_that_test_file(str(file_path)):
            return ThatTestFile.from_parent(parent, path=file_path)
    return None


def pytest_pycollect_makemodule(module_path, parent):
    """Override module collection to prevent duplicate collection."""
    # If this is a That test file, don't collect it as a regular module
    if _is_that_test_file(str(module_path)):
        # Return a custom module that doesn't collect functions
        return ThatModule.from_parent(parent, path=module_path)
    # Let pytest handle regular modules normally
    return None


class ThatModule(pytest.Module):
    """Custom module collector that prevents function collection for That test files."""

    def collect(self):
        """Don't collect any functions - That tests are handled by ThatTestFile."""
        return []


def _is_that_test_file(file_path: str) -> bool:
    """Check if a file contains That tests."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(1000)  # Read first 1000 chars
            return ('from test_that import' in content or 
                   'import test_that' in content or
                   '@test(' in content)
    except (IOError, UnicodeDecodeError):
        return False


def pytest_configure(config):
    """Configure pytest for That integration."""
    # Add custom markers for That tests
    config.addinivalue_line(
        "markers", "that_test: mark test as a That framework test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify collected items to add That-specific markers."""
    for item in items:
        if isinstance(item, ThatTestItem):
            item.add_marker(pytest.mark.that_test)


# Pytest plugin entry point
def pytest_plugins():
    """Return list of pytest plugins."""
    return []


# Make this module discoverable as a pytest plugin
__all__ = [
    'pytest_collect_file',
    'pytest_configure', 
    'pytest_collection_modifyitems',
    'ThatTestItem',
    'ThatTestFile'
]
