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

        _registry = get_registry()
        
        standalone_results = await self._run_standalone_tests_async(_registry)
        suite_results = await self._run_suite_tests_async(_registry)

        self.results = standalone_results + suite_results
        return self.results

    async def _run_standalone_tests_async(self, registry) -> List[TestResult]:
        """Run standalone tests concurrently."""
        tasks = [
            self.run_test_async(name, func)
            for name, func, _ in registry.standalone_tests
        ]
        
        if not tasks:
            return []

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [self._handle_result(r) for r in results]

    async def _run_suite_tests_async(self, registry) -> List[TestResult]:
        """Run suite tests sequentially."""
        all_results = []
        from .fixtures import get_fixture_registry
        
        for _suite_name, suite in registry.suites.items():
            fixture_registry = get_fixture_registry()
            fixture_registry.setup_suite_fixtures()

            for test_name, test_func, _ in suite.tests:
                result = await self.run_test_async(test_name, test_func)
                all_results.append(result)

            fixture_registry.teardown_suite_fixtures()
            
        return all_results

    def _handle_result(self, result: Any) -> TestResult:
        """Handle results from asyncio.gather, converting exceptions to TestResult."""
        if isinstance(result, TestResult):
            return result
        elif isinstance(result, Exception):
            return TestResult(
                test_name="Unknown",
                passed=False,
                error=result,
                duration=0.0
            )
        return TestResult(
            test_name="Unknown",
            passed=False,
            error=TypeError(f"Unexpected result type: {type(result)}"),
            duration=0.0
        )

    def run_all(self) -> List[TestResult]:
        """Run all tests, handling async tests properly."""
        if self._has_async_tests():
            return self._run_all_with_async()
        else:
            return super().run_all()

    def _has_async_tests(self) -> bool:
        """Check if there are any asynchronous tests registered."""
        from .runner import get_registry
        _registry = get_registry()

        if any(inspect.iscoroutinefunction(f) for _, f, _ in _registry.standalone_tests):
            return True

        for suite in _registry.suites.values():
            if any(inspect.iscoroutinefunction(f) for _, f, _ in suite.tests):
                return True

        return False

    def _run_all_with_async(self) -> List[TestResult]:
        """Run all tests using an async event loop."""
        loop = self._get_or_create_loop()
        if loop.is_running():
            raise RuntimeError(
                "Cannot run async tests from within an existing event loop. "
                "Use run_all_async() or run tests from outside async context."
            )
        return loop.run_until_complete(self.run_all_async())

