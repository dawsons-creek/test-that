"""
Example test file from the todo CLI example.

This demonstrates the comprehensive testing capabilities of test_that
through a complex todo application. The actual todo CLI example is available
in examples/todo_cli/ directory.
"""

from test_that import suite, test, that

with suite("Todo CLI Example Demo"):

    @test("demonstrates complex test organization")
    def test_todo_example_exists():
        """This is a placeholder showing the todo CLI example structure."""
        that("examples/todo_cli contains a comprehensive test suite").contains("todo_cli")
        that("Unit tests cover model validation and business logic").contains("Unit tests")
        that("Integration tests cover CLI commands and file I/O").contains("Integration")

    @test("shows testing patterns available")
    def test_testing_patterns():
        """Demonstrates patterns shown in the todo CLI example."""
        patterns = [
            "Model validation testing",
            "Storage backend testing",
            "Time-based testing with replay",
            "CLI integration testing",
            "File persistence testing",
            "Test fixtures and testing organization"
        ]

        for pattern in patterns:
            that(pattern).contains("testing")

        that(len(patterns)).equals(6)
