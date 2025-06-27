"""
Two-phase test discovery system for the That testing library.

This module provides AST-based test discovery that separates finding tests
from executing them, avoiding side effects and improving performance.
"""

import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple


@dataclass
class DiscoveredTest:
    """Information about a discovered test."""
    name: str
    function_name: str
    line_number: int
    suite_name: Optional[str] = None
    is_async: bool = False
    decorators: List[str] = None

    def __post_init__(self):
        if self.decorators is None:
            self.decorators = []


@dataclass
class DiscoveredSuite:
    """Information about a discovered test suite."""
    name: str
    line_number: int
    tests: List[DiscoveredTest] = None

    def __post_init__(self):
        if self.tests is None:
            self.tests = []


class TestDiscoveryVisitor(ast.NodeVisitor):
    """AST visitor that discovers tests without executing code."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.tests: List[DiscoveredTest] = []
        self.suites: List[DiscoveredSuite] = []
        self.current_suite: Optional[DiscoveredSuite] = None
        self.in_suite_context = False

    def visit_With(self, node: ast.With) -> None:
        """Visit with statements to find suite contexts."""
        for item in node.items:
            if isinstance(item.context_expr, ast.Call):
                func = item.context_expr.func
                if isinstance(func, ast.Name) and func.id == "suite":
                    # Found a suite context
                    suite_name = self._extract_suite_name(item.context_expr)
                    self.current_suite = DiscoveredSuite(
                        name=suite_name,
                        line_number=node.lineno
                    )
                    self.suites.append(self.current_suite)
                    self.in_suite_context = True

                    # Visit the suite body
                    self.generic_visit(node)

                    self.current_suite = None
                    self.in_suite_context = False
                    return

        # Not a suite context, continue normally
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions to find suite classes."""
        # Check if class is decorated with @suite
        is_suite_class = False
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "suite":
                is_suite_class = True
                break
            elif isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Name) and func.id == "suite":
                    is_suite_class = True
                    break

        if is_suite_class:
            # This is a suite class
            suite_name = node.name
            self.current_suite = DiscoveredSuite(
                name=suite_name,
                line_number=node.lineno
            )
            self.suites.append(self.current_suite)

            # Visit methods in the class
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    self.visit_FunctionDef(item)

            self.current_suite = None
        else:
            # Not a suite class, visit normally
            self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions to find test functions."""
        # Check if function is decorated with @test
        test_name = None
        decorators = []

        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Name):
                decorators.append(decorator.id)
                if decorator.id == "test":
                    test_name = node.name
            elif isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Name):
                    decorators.append(func.id)
                    if func.id == "test":
                        # Extract test description if provided
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            test_name = decorator.args[0].value
                        else:
                            test_name = node.name

        if test_name:
            # This is a test function
            test = DiscoveredTest(
                name=test_name,
                function_name=node.name,
                line_number=node.lineno,
                suite_name=self.current_suite.name if self.current_suite else None,
                is_async=isinstance(node, ast.AsyncFunctionDef),
                decorators=decorators
            )

            self.tests.append(test)
            if self.current_suite:
                self.current_suite.tests.append(test)

        # Don't visit nested functions

    def _extract_suite_name(self, call_node: ast.Call) -> str:
        """Extract suite name from suite() call."""
        if call_node.args and isinstance(call_node.args[0], ast.Constant):
            return call_node.args[0].value

        # Check keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg == "name" and isinstance(keyword.value, ast.Constant):
                return keyword.value.value

        return "Unnamed Suite"


class TestDiscovery:
    """Two-phase test discovery system."""

    def __init__(self):
        self.discovered_tests: Dict[str, List[DiscoveredTest]] = {}
        self.discovered_suites: Dict[str, List[DiscoveredSuite]] = {}

    def discover_file(self, file_path: Path) -> Tuple[List[DiscoveredTest], List[DiscoveredSuite]]:
        """Discover tests in a single file using AST parsing.
        
        Args:
            file_path: Path to the test file
            
        Returns:
            Tuple of (tests, suites) discovered in the file
        """
        try:
            with open(file_path, encoding='utf-8') as f:
                source = f.read()

            tree = ast.parse(source, filename=str(file_path))
            visitor = TestDiscoveryVisitor(file_path)
            visitor.visit(tree)

            # Store discoveries
            abs_path = str(file_path.resolve())
            self.discovered_tests[abs_path] = visitor.tests
            self.discovered_suites[abs_path] = visitor.suites

            return visitor.tests, visitor.suites

        except Exception as e:
            print(f"Error discovering tests in {file_path}: {e}")
            return [], []

    def discover_directory(self, directory: Path, pattern: str = "test_*.py") -> None:
        """Discover all tests in a directory.
        
        Args:
            directory: Directory to search
            pattern: File pattern to match
        """
        if directory.is_file():
            self.discover_file(directory)
        else:
            for file_path in directory.rglob(pattern):
                if file_path.is_file() and file_path.suffix == ".py":
                    self.discover_file(file_path)

    def get_tests_at_lines(self, file_path: str, line_numbers: Set[int]) -> List[DiscoveredTest]:
        """Get tests at specific line numbers in a file.
        
        Args:
            file_path: Absolute path to the file
            line_numbers: Set of line numbers to check
            
        Returns:
            List of tests at those line numbers
        """
        tests = self.discovered_tests.get(file_path, [])
        matching_tests = []

        for test in tests:
            if test.line_number in line_numbers:
                matching_tests.append(test)

        return matching_tests

    def get_tests_by_pattern(self, pattern: str) -> List[DiscoveredTest]:
        """Get tests matching a name pattern.
        
        Args:
            pattern: Pattern to match in test names
            
        Returns:
            List of matching tests
        """
        matching_tests = []
        pattern_lower = pattern.lower()

        for tests in self.discovered_tests.values():
            for test in tests:
                if pattern_lower in test.name.lower():
                    matching_tests.append(test)

        return matching_tests

    def get_suite_tests(self, suite_name: str) -> List[DiscoveredTest]:
        """Get all tests in a specific suite.
        
        Args:
            suite_name: Name of the suite
            
        Returns:
            List of tests in that suite
        """
        suite_tests = []

        for suites in self.discovered_suites.values():
            for suite in suites:
                if suite.name == suite_name:
                    suite_tests.extend(suite.tests)

        return suite_tests

    def get_all_tests(self) -> List[Tuple[str, DiscoveredTest]]:
        """Get all discovered tests with their file paths.
        
        Returns:
            List of (file_path, test) tuples
        """
        all_tests = []

        for file_path, tests in self.discovered_tests.items():
            for test in tests:
                all_tests.append((file_path, test))

        return all_tests

    def print_summary(self) -> None:
        """Print a summary of discovered tests."""
        total_tests = sum(len(tests) for tests in self.discovered_tests.values())
        total_suites = sum(len(suites) for suites in self.discovered_suites.values())

        print(f"Discovered {total_tests} tests in {total_suites} suites")

        for file_path, tests in self.discovered_tests.items():
            if tests:
                print(f"\n{Path(file_path).name}:")
                for test in tests:
                    prefix = "  async " if test.is_async else "  "
                    suite_info = f" [{test.suite_name}]" if test.suite_name else ""
                    print(f"{prefix}{test.name}{suite_info} (line {test.line_number})")

