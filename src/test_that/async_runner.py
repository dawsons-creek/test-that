"""
Async-aware test runner for the That testing library.

This module provides an improved async test execution system that avoids
the ThreadPoolExecutor workaround from the original implementation.
"""

import asyncio
import inspect
from typing import Any, Callable, Dict, List, Optional

from .runner import TestResult, TestRunner


class AsyncTestRunner(TestRunner):
    """Test runner with improved async support."""

    def __init__(self, verbose: bool = False):
        super().__init__(verbose)
        self._event_loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        """Get existing event loop or create a new one."""
        if self._event_loop is None:
            try:
                # Try to get the running loop
                self._event_loop = asyncio.get_running_loop()
            except RuntimeError:
                # No loop running, create a new one
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
        return self._event_loop

    async def _run_async_test(self, test_func: Callable, fixtures: Dict[str, Any]) -> None:
        """Run an async test function."""
        await test_func(**fixtures)

    def _execute_test_function(self, test_func: Callable, fixtures: Dict[str, Any]) -> None:
        """Execute a test function (sync or async) with fixtures."""
        if inspect.iscoroutinefunction(test_func):
            # Async test
            loop = self._get_or_create_loop()

            # Check if loop is already running
            if loop.is_running():
                # Schedule the coroutine as a task
                _ = asyncio.create_task(self._run_async_test(test_func, fixtures))
                # We can't wait synchronously in a running loop
                # This is a limitation - async tests need async runner
                raise RuntimeError(
                    "Cannot run async tests synchronously in an already running event loop. "
                    "Use AsyncTestRunner.run_async() instead."
                )
            else:
                # Run the async test in the loop
                loop.run_until_complete(self._run_async_test(test_func, fixtures))
        else:
            # Sync test - run normally
            test_func(**fixtures)

    async def run_test_async(self, test_name: str, test_func: Callable) -> TestResult:
        """Run a single test asynchronously."""
        import time

        from .fixtures import get_fixture_registry

        start_time = time.time()
        passed = False
        error = None

        try:
            # Get fixtures
            fixture_registry = get_fixture_registry()
            fixtures = fixture_registry.resolve_fixtures(test_func)

            # Setup function-scoped fixtures
            fixture_registry.setup_function_fixtures()

            try:
                # Execute test
                if inspect.iscoroutinefunction(test_func):
                    await test_func(**fixtures)
                else:
                    test_func(**fixtures)

                passed = True
            finally:
                # Cleanup function-scoped fixtures
                fixture_registry.teardown_function_fixtures()

        except Exception as e:
            error = e

        duration = time.time() - start_time

        return TestResult(
            test_name=test_name,
            passed=passed,
            error=error,
            duration=duration
        )

    async def run_all_async(self) -> List[TestResult]:
        """Run all tests asynchronously."""
        from .runner import get_registry

        all_results = []
        _registry = get_registry()

        # Create tasks for all standalone tests
        tasks = []
        for test_name, test_func, _ in _registry.standalone_tests:
            task = self.run_test_async(test_name, test_func)
            tasks.append(task)

        # Run standalone tests concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, TestResult):
                    all_results.append(result)
                elif isinstance(result, Exception):
                    # Handle unexpected errors
                    all_results.append(
                        TestResult(
                            test_name="Unknown",
                            passed=False,
                            error=result,
                            duration=0.0
                        )
                    )

        # Run suite tests (sequentially for now to maintain suite coherence)
        for _suite_name, suite in _registry.suites.items():
            # Setup suite fixtures
            from .fixtures import get_fixture_registry
            fixture_registry = get_fixture_registry()
            fixture_registry.setup_suite_fixtures()

            # Run tests in suite
            for test_name, test_func, _ in suite.tests:
                result = await self.run_test_async(test_name, test_func)
                all_results.append(result)

            # Cleanup suite fixtures
            fixture_registry.teardown_suite_fixtures()

        self.results = all_results
        return all_results

    def run_all(self) -> List[TestResult]:
        """Run all tests, handling async tests properly."""
        # Check if any tests are async
        from .runner import get_registry
        _registry = get_registry()

        has_async = any(
            inspect.iscoroutinefunction(test_func)
            for _, test_func, _ in _registry.standalone_tests
        )

        if not has_async:
            # Check suites too
            for _, suite in _registry.suites.items():
                if any(inspect.iscoroutinefunction(test_func)
                       for _, test_func, _ in suite.tests):
                    has_async = True
                    break

        if has_async:
            # Use async execution
            loop = self._get_or_create_loop()
            if loop.is_running():
                raise RuntimeError(
                    "Cannot run async tests from within an existing event loop. "
                    "Use run_all_async() or run tests from outside async context."
                )
            return loop.run_until_complete(self.run_all_async())
        else:
            # All tests are sync, use parent implementation
            return super().run_all()

