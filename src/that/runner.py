"""
Test runner and discovery for the That testing library.

Handles test registration, discovery, and execution.
"""

import asyncio
import inspect
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Set


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
        self.setup_func: Optional[Callable] = None
        self.teardown_func: Optional[Callable] = None
        self.setup_result: Any = None

    def add_test(self, name: str, func: Callable, line_number: int):
        """Add a test to this suite with its line number."""
        self.tests.append((name, func, line_number))

    def set_setup(self, func: Callable):
        """Set the setup function for this suite."""
        self.setup_func = func

    def set_teardown(self, func: Callable):
        """Set the teardown function for this suite."""
        self.teardown_func = func


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
        # Get the line number where the decorator was applied
        frame = inspect.currentframe()
        if frame and frame.f_back:
            line_number = frame.f_back.f_lineno
            file_path = frame.f_back.f_code.co_filename
        else:
            line_number = 0
            file_path = "<unknown>"

        _registry.add_test(description, func, line_number, file_path)
        return func

    return decorator


class SuiteContext:
    """Context manager for test suites that captures setup/teardown functions."""

    def __init__(self, name: str):
        self.name = name
        self.suite = None
        self.old_suite = None
        self.frame = None
        self.original_locals = None

    def __enter__(self):
        self.suite = _registry.create_suite(self.name)
        self.old_suite = _registry.current_suite
        _registry.set_current_suite(self.suite)

        # Capture the calling frame to monitor for setup/teardown functions
        self.frame = inspect.currentframe().f_back
        self.original_locals = set(self.frame.f_locals.keys())

        return self.suite

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            # Check for new functions that were defined in the suite block
            current_locals = self.frame.f_locals
            new_names = set(current_locals.keys()) - self.original_locals

            for name in new_names:
                value = current_locals[name]
                if callable(value):
                    if name == "setup":
                        self.suite.set_setup(value)
                    elif name == "teardown":
                        self.suite.set_teardown(value)
        finally:
            _registry.set_current_suite(self.old_suite)


def suite(name: str):
    """Context manager to group tests into a suite."""
    return SuiteContext(name)


class TestRunner:
    """Runs tests and collects results."""

    def __init__(self, verbose: bool = False, include_tags: Set[str] = None, 
                 exclude_tags: Set[str] = None):
        self.verbose = verbose
        self.results: List[TestResult] = []
        self.include_tags = include_tags
        self.exclude_tags = exclude_tags

    def run_test(
        self, test_name: str, test_func: Callable, setup_result: Any = None
    ) -> TestResult:
        """Run a single test function (supports both sync and async)."""
        start_time = time.time()

        try:
            args = _prepare_test_arguments(test_func, setup_result)
            
            if asyncio.iscoroutinefunction(test_func):
                _execute_async_test(test_func, args)
            else:
                test_func(*args)

            duration = time.time() - start_time
            return TestResult(test_name, True, duration=duration)

        except Exception as e:
            duration = time.time() - start_time
            return TestResult(test_name, False, error=e, duration=duration)

    def run_suite(self, suite: TestSuite) -> List[TestResult]:
        """Run all tests in a suite."""
        setup_result = _run_suite_setup(suite)
        if setup_result is False:
            return _create_setup_failure_results(suite)

        results = _run_suite_tests(suite, setup_result, self)
        _run_suite_teardown(suite, setup_result, self.verbose)

        return results

    def run_all(self) -> List[TestResult]:
        """Run all registered tests."""
        from .tags import get_tag_registry
        tag_registry = get_tag_registry()
        
        all_results = []

        # Run standalone tests
        for test_name, test_func, _ in _registry.standalone_tests:
            # Check if test should run based on tags
            if tag_registry.should_run(test_func, self.include_tags, self.exclude_tags):
                result = self.run_test(test_name, test_func)
                all_results.append(result)

        # Run suite tests
        for suite_name, suite in _registry.suites.items():
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


def _prepare_test_arguments(test_func: Callable, setup_result: Any) -> tuple:
    """Prepare arguments for test function based on signature."""
    sig = inspect.signature(test_func)
    params = list(sig.parameters.values())

    if len(params) > 0 and setup_result is not None:
        return (setup_result,)
    else:
        return ()


def _execute_async_test(test_func: Callable, args: tuple):
    """Execute async test function with proper event loop handling."""
    try:
        # Try to get existing event loop
        asyncio.get_running_loop()
        # We're already in an async context, run in thread
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, test_func(*args))
            future.result()
    except RuntimeError:
        # No event loop running, create one
        asyncio.run(test_func(*args))


def _run_suite_setup(suite: TestSuite) -> Any:
    """Run suite setup and return result or False if failed."""
    if not suite.setup_func:
        return None

    try:
        setup_result = suite.setup_func()
        suite.setup_result = setup_result
        return setup_result
    except Exception:
        return False


def _create_setup_failure_results(suite: TestSuite) -> List[TestResult]:
    """Create failure results for all tests when setup fails."""
    results = []
    for test_name, _, _ in suite.tests:
        results.append(
            TestResult(test_name, False, error=Exception("Setup failed"))
        )
    return results


def _run_suite_tests(suite: TestSuite, setup_result: Any, runner) -> List[TestResult]:
    """Run all tests in the suite that pass tag filtering."""
    from .tags import get_tag_registry
    tag_registry = get_tag_registry()
    
    results = []
    for test_name, test_func, _ in suite.tests:
        if tag_registry.should_run(test_func, runner.include_tags, runner.exclude_tags):
            result = runner.run_test(test_name, test_func, setup_result)
            results.append(result)
    
    return results


def _run_suite_teardown(suite: TestSuite, setup_result: Any, verbose: bool):
    """Run suite teardown with proper error handling."""
    if not suite.teardown_func:
        return

    try:
        if setup_result is not None:
            sig = inspect.signature(suite.teardown_func)
            if len(sig.parameters) > 0:
                suite.teardown_func(setup_result)
            else:
                suite.teardown_func()
        else:
            suite.teardown_func()
    except Exception as e:
        if verbose:
            print(f"Warning: Teardown failed: {e}")




def get_registry() -> TestRegistry:
    """Get the global test registry."""
    return _registry


def clear_registry():
    """Clear the global test registry."""
    _registry.clear()
