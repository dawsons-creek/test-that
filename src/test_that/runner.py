"""
Test runner and discovery for the That testing library.

Handles test registration, discovery, and execution.
"""

import asyncio
import inspect
import time
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from .fixtures import get_fixture_registry


class TestResult:
    """Represents the result of running a single test."""

    def __init__(
        self,
        name: str,
        passed: bool,
        error: Optional[Exception] = None,
        duration: float = 0.0,
    ):
        self.name = name
        self.passed = passed
        self.error = error
        self.duration = duration

    def is_slow(self, threshold: float = 1.0) -> bool:
        """Check if this test is considered slow (default: > 1 second)."""
        return self.duration > threshold


class TestSuite:
    """Represents a collection of related tests."""

    def __init__(self, name: str):
        self.name = name
        self.tests: List[Tuple[str, Callable, int]] = []  # Added line number

    def add_test(self, name: str, func: Callable, line_number: int):
        """Add a test to this suite with its line number."""
        self.tests.append((name, func, line_number))


class TestRegistry:
    """Global registry for tests and suites."""

    def __init__(self):
        self.suites: Dict[str, TestSuite] = {}
        self.current_suite: Optional[TestSuite] = None
        self.standalone_tests: List[Tuple[str, Callable, int]] = []  # Added line number
        self.test_file_map: Dict[str, List[Tuple[str, int, Optional[str]]]] = (
            {}
        )  # file -> [(test_name, line, suite)]

    def add_test(self, name: str, func: Callable, line_number: int, file_path: str):
        """Add a test to the current suite or standalone tests with line info."""
        suite_name = self.current_suite.name if self.current_suite else None

        # Store in file map for line number lookup
        if file_path not in self.test_file_map:
            self.test_file_map[file_path] = []
        self.test_file_map[file_path].append((name, line_number, suite_name))

        if self.current_suite:
            self.current_suite.add_test(name, func, line_number)
        else:
            self.standalone_tests.append((name, func, line_number))

    def create_suite(self, name: str) -> TestSuite:
        """Create a new test suite."""
        suite = TestSuite(name)
        self.suites[name] = suite
        return suite

    def set_current_suite(self, suite: Optional[TestSuite]):
        """Set the current active suite."""
        self.current_suite = suite

    def get_all_tests(self) -> List[Tuple[Optional[str], str, Callable]]:
        """Get all tests as (suite_name, test_name, test_func) tuples."""
        tests = []

        # Add standalone tests
        for name, func, _ in self.standalone_tests:
            tests.append((None, name, func))

        # Add suite tests
        for suite_name, suite in self.suites.items():
            for test_name, test_func, _ in suite.tests:
                tests.append((suite_name, test_name, test_func))

        return tests

    def get_tests_by_line(self, file_path: str, line_numbers: Set[int]) -> List[str]:
        """Get test names that match the given line numbers in a file."""
        if file_path not in self.test_file_map:
            return []

        matching_tests = []
        file_tests = sorted(
            self.test_file_map[file_path], key=lambda x: x[1]
        )  # Sort by line

        for line in line_numbers:
            # Find the test at or just before this line
            best_match = None
            for test_name, test_line, suite_name in file_tests:
                if test_line <= line:
                    best_match = (test_name, test_line, suite_name)
                else:
                    break

            if best_match:
                matching_tests.append(best_match[0])

        return list(set(matching_tests))  # Remove duplicates

    def clear(self):
        """Clear all registered tests and suites."""
        self.suites.clear()
        self.current_suite = None
        self.standalone_tests.clear()
        self.test_file_map.clear()


# Global test registry
_registry = TestRegistry()


def test(description: str):
    """Decorator to register a test function."""

    def decorator(func: Callable):
        # Store description on function for parametrize decorator
        func._test_description = description
        
        # Get the line number where the decorator was applied
        frame = inspect.currentframe()
        if frame and frame.f_back:
            line_number = frame.f_back.f_lineno
            file_path = frame.f_back.f_code.co_filename
        else:
            line_number = 0
            file_path = "<unknown>"

        # Check if this is a method (has __qualname__ with '.')
        # If so, don't register it yet - wait for the suite decorator
        if hasattr(func, '__qualname__') and '.' in func.__qualname__:
            # This is a method, store the registration info but don't register yet
            func._test_line = line_number
            func._test_file = file_path
        else:
            # This is a regular function, register immediately
            _registry.add_test(description, func, line_number, file_path)
        
        return func

    return decorator


class SuiteContext:
    """Context manager for test suites."""

    def __init__(self, name: str):
        self.name = name
        self.suite = None
        self.old_suite = None

    def __enter__(self):
        self.suite = _registry.create_suite(self.name)
        self.old_suite = _registry.current_suite
        _registry.set_current_suite(self.suite)
        return self.suite

    def __exit__(self, exc_type, exc_val, exc_tb):
        _registry.set_current_suite(self.old_suite)


def suite(name_or_class=None, *, name=None):
    """
    Create a test suite either as a decorator or context manager.
    """
    if isinstance(name_or_class, str):
        return SuiteContext(name_or_class)
    
    def decorator(cls):
        suite_name = name if name else cls.__name__
        return _create_class_suite(cls, suite_name)

    if name_or_class is None:
        return decorator
    else:
        return decorator(name_or_class)


def _create_class_suite(cls, suite_name: str):
    """Create a suite from a test class."""
    _remove_class_tests_from_registry(cls)
    suite_obj = _registry.create_suite(suite_name)

    for attr_name in dir(cls):
        attr_value = getattr(cls, attr_name)
        if callable(attr_value) and hasattr(attr_value, '_test_description'):
            _add_method_as_test(cls, suite_obj, attr_value)
    
    return cls

def _add_method_as_test(cls, suite_obj, method):
    """Adds a method from a class to a test suite."""
    test_description = method._test_description
    wrapped_test = _create_test_wrapper(cls, method)
    line_number = getattr(method, '_test_line', 
                        getattr(method, '__code__', type('', (), {'co_firstlineno': 0})).co_firstlineno)
    suite_obj.add_test(test_description, wrapped_test, line_number)

def _create_test_wrapper(cls, method):
    """Create a wrapper that handles instance creation and fixture injection."""
    def test_wrapper(**fixtures):
        instance = cls()
        sig = inspect.signature(method)
        params = list(sig.parameters.keys())

        if params and params[0] == 'self':
            filtered_fixtures = {k: v for k, v in fixtures.items() if k in params[1:]}
            return method(instance, **filtered_fixtures)
        else:
            return method(**fixtures)

    test_wrapper._original_func = method
    return test_wrapper


def _remove_class_tests_from_registry(cls):
    """Remove any tests from a class that were already registered."""
    # Remove standalone tests that belong to this class
    _registry.standalone_tests = [
        (name, func, line) for name, func, line in _registry.standalone_tests
        if not (hasattr(func, '__self__') and isinstance(func.__self__, cls))
    ]


class TestRunner:
    """Runs tests and collects results."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results: List[TestResult] = []

    def run_test(self, test_name: str, test_func: Callable) -> TestResult:
        """Run a single test function with fixture injection."""
        from .mocking import cleanup_mocks

        start_time = time.perf_counter()
        fixture_registry = get_fixture_registry()

        try:
            # Resolve fixtures for this test - use original function if parametrized
            func_for_fixtures = getattr(test_func, '_original_func', test_func)
            fixtures = fixture_registry.resolve_fixtures(func_for_fixtures)

            if asyncio.iscoroutinefunction(test_func):
                _execute_async_test(test_func, fixtures)
            else:
                test_func(**fixtures)

            duration = time.perf_counter() - start_time
            return TestResult(test_name, True, duration=duration)

        except Exception as e:
            duration = time.perf_counter() - start_time
            return TestResult(test_name, False, error=e, duration=duration)
        finally:
            # Cleanup function-scoped fixtures after each test
            fixture_registry.teardown_function_fixtures()
            cleanup_mocks()

    def run_suite(self, suite: TestSuite) -> List[TestResult]:
        """Run all tests in a suite."""
        results = []
        
        for test_name, test_func, _ in suite.tests:
            result = self.run_test(test_name, test_func)
            results.append(result)
        
        # Cleanup suite-scoped fixtures after all tests in suite
        fixture_registry = get_fixture_registry()
        fixture_registry.teardown_suite_fixtures()

        return results

    def run_all(self) -> List[TestResult]:
        """Run all registered tests."""
        all_results = []

        # Run standalone tests
        for test_name, test_func, _ in _registry.standalone_tests:
            result = self.run_test(test_name, test_func)
            all_results.append(result)

        # Run suite tests
        for _suite_name, suite in _registry.suites.items():
            suite_results = self.run_suite(suite)
            all_results.extend(suite_results)

        self.results = all_results
        return all_results

    def get_summary(self) -> Tuple[int, int, int, float]:
        """Get test summary: (total, passed, failed, total_time)."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        total_time = sum(r.duration for r in self.results)

        return total, passed, failed, total_time


def _execute_async_test(test_func: Callable, fixtures: Dict[str, Any]):
    """Execute async test function with proper event loop handling.
    
    This is a simplified version that handles the common case where tests
    are run from a synchronous context. For more advanced async handling,
    use AsyncTestRunner from async_runner module.
    """
    # Always create a new event loop for test isolation
    # This avoids issues with nested loops and ensures clean state
    asyncio.run(test_func(**fixtures))




def get_registry() -> TestRegistry:
    """Get the global test registry."""
    return _registry


def clear_registry():
    """Clear the global test registry."""
    _registry.clear()
