"""
Output formatting for the That testing library.

Handles formatting and display of test results.
"""

import os
import sys
from typing import Dict, List, Optional, Tuple

from .assertions import AssertionError
from .runner import TestRegistry, TestResult


class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"

    @classmethod
    def disable(cls):
        """Disable colors by setting all to empty strings."""
        cls.GREEN = ""
        cls.RED = ""
        cls.YELLOW = ""
        cls.BLUE = ""
        cls.BOLD = ""
        cls.RESET = ""


class TestFormatter:
    """Formats test results for display."""

    def __init__(
        self, use_color: bool = True, verbose: bool = False, focus_mode: bool = False
    ):
        self.use_color = use_color
        self.verbose = verbose
        self.focus_mode = focus_mode

        if not use_color or not self._supports_color():
            Colors.disable()

    def _supports_color(self) -> bool:
        """Check if the terminal supports color output."""
        return (
            hasattr(sys.stdout, "isatty")
            and sys.stdout.isatty()
            and "TERM" in os.environ
            and os.environ["TERM"] != "dumb"
        )

    def format_results(self, results: List[TestResult], registry: TestRegistry) -> str:
        """Format all test results for display."""
        output = []

        # In focus mode, show only failures with context
        if self.focus_mode:
            return self._format_focused_results(results, registry)

        # Group results by suite
        suite_results = self._group_by_suite(results, registry)

        # Format each suite
        for suite_name, suite_tests in suite_results.items():
            if suite_name:
                output.append(f"{Colors.BOLD}{suite_name}{Colors.RESET}")

            for result in suite_tests:
                output.append(self._format_test_result(result))

        # Add summary
        output.append(self._format_summary(results))

        return "\n".join(output)

    def _group_by_suite(
        self, results: List[TestResult], registry: TestRegistry
    ) -> Dict[Optional[str], List[TestResult]]:
        """Group test results by their suite."""
        # Create a mapping from test name to suite name
        test_to_suite = {}

        # Map standalone tests
        for test_name, _, _ in registry.standalone_tests:
            test_to_suite[test_name] = None

        # Map suite tests
        for suite_name, suite in registry.suites.items():
            for test_name, _, _ in suite.tests:
                test_to_suite[test_name] = suite_name

        # Group results
        grouped = {}
        for result in results:
            suite_name = test_to_suite.get(result.name)
            if suite_name not in grouped:
                grouped[suite_name] = []
            grouped[suite_name].append(result)

        return grouped

    def _format_test_result(self, result: TestResult) -> str:
        """Format a single test result."""
        if result.passed:
            status = f"{Colors.GREEN}✓{Colors.RESET}"
            line = f"  {status} {result.name}"

            # Always show timing for slow tests, optionally for all tests in verbose mode
            if result.is_slow():
                line += f" ({self._format_duration(result.duration)}) {Colors.YELLOW}[SLOW]{Colors.RESET}"
            elif self.verbose:
                line += f" ({self._format_duration(result.duration)})"

            return line
        else:
            status = f"{Colors.RED}✗{Colors.RESET}"
            lines = [f"  {status} {result.name}"]

            if result.error:
                lines.append("")
                lines.extend(self._format_error(result.error))

            return "\n".join(lines)

    def _format_error(self, error: Exception) -> List[str]:
        """Format an error for display."""
        lines = []

        if isinstance(error, AssertionError):
            # Format assertion errors with clear expected/actual
            lines.append(f"    {error.message}")
            lines.append("")

            # Use intelligent diff if available
            if hasattr(error, "diff_lines") and error.diff_lines:
                for diff_line in error.diff_lines:
                    lines.append(f"    {diff_line}")
            elif hasattr(error, "expected") and hasattr(error, "actual"):
                lines.append(f"    Expected: {self._format_value(error.expected)}")
                lines.append(f"    Actual:   {self._format_value(error.actual)}")

        else:
            # Format other exceptions
            lines.append(f"    {type(error).__name__}: {str(error)}")

            if self.verbose:
                import traceback

                tb_lines = traceback.format_exception(
                    type(error), error, error.__traceback__
                )
                lines.extend(f"    {line.rstrip()}" for line in tb_lines)

        return lines

    def _format_value(self, value) -> str:
        """Format a value for display in error messages."""
        if value is None:
            return "None"
        elif isinstance(value, str):
            return repr(value)
        elif isinstance(value, (list, tuple, dict, set)):
            # For collections, show a compact representation
            repr_str = repr(value)
            if len(repr_str) > 60:
                return f"{type(value).__name__} with {len(value)} items"
            return repr_str
        else:
            return str(value)

    def _format_duration(self, duration: float) -> str:
        """Format duration with appropriate precision and units."""
        if duration >= 1.0:
            return f"{duration:.3f}s"
        elif duration >= 0.001:
            return f"{duration * 1000:.1f}ms"
        else:
            return f"{duration * 1000000:.0f}μs"

    def _format_summary(self, results: List[TestResult]) -> str:
        """Format the test summary."""
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        total_time = sum(r.duration for r in results)

        lines = []
        lines.append("─" * 40)
        lines.append(f"Ran {total} tests in {self._format_duration(total_time)}")

        if failed == 0:
            lines.append(f"{Colors.GREEN}{passed} passed{Colors.RESET}")
            lines.append("")
            lines.append(f"{Colors.GREEN}{Colors.BOLD}PASSED{Colors.RESET}")
        else:
            status_parts = []
            if passed > 0:
                status_parts.append(f"{Colors.GREEN}{passed} passed{Colors.RESET}")
            if failed > 0:
                status_parts.append(f"{Colors.RED}{failed} failed{Colors.RESET}")

            lines.append(", ".join(status_parts))
            lines.append("")
            lines.append(f"{Colors.RED}{Colors.BOLD}FAILED{Colors.RESET}")

        return "\n".join(lines)

    def _format_focused_results(
        self, results: List[TestResult], registry: TestRegistry
    ) -> str:
        """Format results in focus mode - show only failures with context."""
        passed, failed = _separate_results(results)

        output = []
        if passed:
            output.extend(_format_passed_summary(passed))

        if failed:
            if passed:
                output.append("")
            output.extend(_format_failed_details(failed, self))

        output.append(self._format_summary(results))
        return "\n".join(output)


def _separate_results(
    results: List[TestResult],
) -> Tuple[List[TestResult], List[TestResult]]:
    """Separate results into passed and failed lists."""
    passed = []
    failed = []
    for result in results:
        if result.passed:
            passed.append(result)
        else:
            failed.append(result)
    return passed, failed


def _format_passed_summary(passed: List[TestResult]) -> List[str]:
    """Format brief summary of passed tests."""
    return [f"{Colors.GREEN}✓{Colors.RESET} {result.name}" for result in passed]


def _format_failed_details(failed: List[TestResult], formatter) -> List[str]:
    """Format detailed failure information."""
    output = []
    for result in failed:
        output.append(f"{Colors.RED}✗{Colors.RESET} {result.name}")
        output.append("")

        if result.error:
            output.extend(_format_failure_context(result.error, formatter))
            output.append("")

    return output


def _format_failure_context(error: Exception, formatter) -> List[str]:
    """Format failure context including assertion and traceback."""
    output = []

    # Show the assertion that failed
    if isinstance(error, AssertionError) and hasattr(error, "message"):
        output.append(f"  {error.message}")
        output.append("")

    # Show error details
    error_lines = formatter._format_error(error)
    output.extend(error_lines)

    # Add context section
    output.append("")
    output.append("  Context:")
    output.extend(_extract_test_context(error))

    return output


def _extract_test_context(error: Exception) -> List[str]:
    """Extract test context from traceback."""
    import traceback

    output = []

    tb = traceback.extract_tb(error.__traceback__)
    for frame in tb:
        if "test_" in frame.filename:
            output.append(f"    File: {frame.filename}:{frame.lineno}")
            output.append(f"    Function: {frame.name}")
            if frame.locals:
                for var, value in frame.locals.items():
                    if not var.startswith("_"):
                        output.append(f"    {var} = {repr(value)}")
            break

    return output


def format_diff(expected, actual) -> List[str]:
    """Format a diff between expected and actual values."""
    lines = []

    if isinstance(expected, dict) and isinstance(actual, dict):
        lines.append("Dictionary differences:")

        # Find added, removed, and changed keys
        expected_keys = set(expected.keys())
        actual_keys = set(actual.keys())

        # Missing keys
        for key in expected_keys - actual_keys:
            lines.append(f"  - {key}: {repr(expected[key])} (missing)")

        # Extra keys
        for key in actual_keys - expected_keys:
            lines.append(f"  + {key}: {repr(actual[key])} (extra)")

        # Changed values
        for key in expected_keys & actual_keys:
            if expected[key] != actual[key]:
                lines.append(f"  ~ {key}: {repr(actual[key])} → {repr(expected[key])}")

    elif isinstance(expected, (list, tuple)) and isinstance(actual, (list, tuple)):
        lines.append(f"{type(expected).__name__} differences:")

        max_len = max(len(expected), len(actual))
        for i in range(max_len):
            exp_val = expected[i] if i < len(expected) else "<missing>"
            act_val = actual[i] if i < len(actual) else "<missing>"

            if i >= len(expected):
                lines.append(f"  + [{i}]: {repr(act_val)} (extra)")
            elif i >= len(actual):
                lines.append(f"  - [{i}]: {repr(exp_val)} (missing)")
            elif exp_val != act_val:
                lines.append(f"  ~ [{i}]: {repr(act_val)} → {repr(exp_val)}")

    return lines
