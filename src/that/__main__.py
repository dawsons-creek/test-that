"""
CLI entry point for the That testing library.

Handles command-line arguments and test discovery.
"""

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import List, Optional, Tuple, Set

from .runner import TestRunner, get_registry, clear_registry
from .output import TestFormatter


def discover_test_files(
    test_dir: str = "tests", pattern: str = "test_*.py"
) -> List[Path]:
    """Discover test files in the given directory."""
    test_path = Path(test_dir)

    if not test_path.exists():
        return []

    # Find all matching files recursively
    test_files = []
    if test_path.is_file():
        # Single file
        if test_path.name.startswith("test_") and test_path.suffix == ".py":
            test_files.append(test_path)
    else:
        # Directory - search recursively
        for file_path in test_path.rglob(pattern):
            if file_path.is_file() and file_path.suffix == ".py":
                test_files.append(file_path)

    return sorted(test_files)


def parse_file_with_line(file_arg: str) -> Tuple[Path, Optional[Set[int]]]:
    """Parse file argument that may contain line numbers.

    Supports:
    - file.py:42         (single line)
    - file.py:20-50      (line range)
    - file.py:10,20,30   (multiple lines)
    - file.py            (all tests)
    """
    # Check for line number syntax
    if ":" in file_arg and not (
        sys.platform == "win32" and len(file_arg) > 1 and file_arg[1] == ":"
    ):
        # Split on the last colon to handle absolute paths
        parts = file_arg.rsplit(":", 1)
        file_path = Path(parts[0])
        line_spec = parts[1]

        line_numbers = set()

        # Parse line specification
        if "-" in line_spec:
            # Range: 20-50
            start, end = line_spec.split("-", 1)
            try:
                start_line = int(start)
                end_line = int(end)
                line_numbers.update(range(start_line, end_line + 1))
            except ValueError:
                raise ValueError(f"Invalid line range: {line_spec}")
        elif "," in line_spec:
            # Multiple: 10,20,30
            for line in line_spec.split(","):
                try:
                    line_numbers.add(int(line.strip()))
                except ValueError:
                    raise ValueError(f"Invalid line number: {line}")
        else:
            # Single: 42
            try:
                line_numbers.add(int(line_spec))
            except ValueError:
                raise ValueError(f"Invalid line number: {line_spec}")

        return file_path, line_numbers
    else:
        return Path(file_arg), None


def load_test_file(file_path: Path) -> bool:
    """Load a test file and execute it to register tests."""
    try:
        # Create module spec
        spec = importlib.util.spec_from_file_location(
            f"test_module_{file_path.stem}", file_path
        )

        if spec is None or spec.loader is None:
            print(f"Warning: Could not load {file_path}")
            return False

        # Load and execute the module
        module = importlib.util.module_from_spec(spec)

        # Add the test file's directory to sys.path temporarily
        test_dir = str(file_path.parent)
        if test_dir not in sys.path:
            sys.path.insert(0, test_dir)
            try:
                spec.loader.exec_module(module)
            finally:
                sys.path.remove(test_dir)
        else:
            spec.loader.exec_module(module)

        return True

    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return False


def load_config() -> dict:
    """Load configuration from pyproject.toml if available."""
    config = {
        "test_dir": "tests",
        "pattern": "test_*.py",
        "verbose": False,
        "color": True,
    }

    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            # No TOML support, use defaults
            return config

    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)

            tool_config = data.get("tool", {}).get("that", {})
            config.update(tool_config)

        except Exception as e:
            print(f"Warning: Could not load config from pyproject.toml: {e}")

    return config


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="That - A Python testing library", prog="that"
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="Test files to run with optional line numbers (e.g., test.py:42, test.py:20-50)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Verbose output (includes stack traces and timing)",
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    parser.add_argument("-s", "--suite", help="Run only tests in the specified suite")

    parser.add_argument(
        "-k", "--filter", help="Run tests matching pattern in description"
    )

    parser.add_argument(
        "--test-dir",
        default=None,
        help="Directory to search for tests (default: tests)",
    )

    parser.add_argument(
        "--pattern", default=None, help="Pattern for test files (default: test_*.py)"
    )

    parser.add_argument(
        "--watch",
        action="store_true",
        help="Watch mode (re-run tests when files change)",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config()

    # Override config with command line arguments
    test_dir = args.test_dir or config["test_dir"]
    pattern = args.pattern or config["pattern"]
    verbose = args.verbose or config["verbose"]
    use_color = not args.no_color and config["color"]

    if args.watch:
        print("Watch mode not implemented yet")
        return 1

    # Clear any existing tests
    clear_registry()

    # Handle specific test syntax (file.py::test_name) and line numbers
    specific_test = None
    line_filters = {}  # file_path -> set of line numbers

    if args.files:
        parsed_files = []
        for file_arg in args.files:
            if "::" in file_arg:
                # Handle file.py::test_name syntax
                file_and_test = file_arg.split("::", 1)
                parsed_files.append(file_and_test[0])
                specific_test = file_and_test[1]
            else:
                # Parse potential line numbers
                try:
                    file_path, line_numbers = parse_file_with_line(file_arg)
                    parsed_files.append(str(file_path))
                    if line_numbers:
                        # Store absolute path for line filtering
                        abs_path = str(file_path.resolve())
                        line_filters[abs_path] = line_numbers
                except ValueError as e:
                    print(f"Error: {e}")
                    return 1

        args.files = parsed_files

    # Discover and load test files
    if args.files:
        # Run specific files or directories
        test_files = []
        for file_arg in args.files:
            file_path = Path(file_arg)
            if file_path.is_file():
                if not file_path.exists():
                    print(f"Error: Test file {file_path} not found")
                    return 1
                test_files.append(file_path)
            elif file_path.is_dir():
                # Discover tests in directory
                dir_tests = discover_test_files(str(file_path), pattern)
                test_files.extend(dir_tests)
            else:
                print(f"Error: Path {file_path} not found")
                return 1
    else:
        # Discover test files
        test_files = discover_test_files(test_dir, pattern)

        if not test_files:
            print(f"No test files found in {test_dir} matching {pattern}")
            return 0

    # Load test files
    loaded_count = 0
    for file_path in test_files:
        if load_test_file(file_path):
            loaded_count += 1

    if loaded_count == 0:
        print("No test files could be loaded")
        return 1

    # Get the registry and check for tests
    registry = get_registry()
    all_tests = registry.get_all_tests()

    if not all_tests:
        print("No tests found")
        return 0

    # Apply filters
    filtered_tests = all_tests

    # Filter by suite if specified
    if args.suite:
        filtered_tests = [
            (suite_name, test_name, test_func)
            for suite_name, test_name, test_func in filtered_tests
            if suite_name == args.suite
        ]

        if not filtered_tests:
            print(f"No tests found in suite '{args.suite}'")
            return 1

        print(f"Running tests in suite '{args.suite}'")

    # Filter by pattern if specified
    if args.filter:
        filtered_tests = [
            (suite_name, test_name, test_func)
            for suite_name, test_name, test_func in filtered_tests
            if args.filter.lower() in test_name.lower()
        ]

        if not filtered_tests:
            print(f"No tests found matching pattern '{args.filter}'")
            return 1

        print(f"Running tests matching '{args.filter}'")

    # Filter by specific test name if specified
    if specific_test:
        # Try to match by function name or description
        filtered_tests = [
            (suite_name, test_name, test_func)
            for suite_name, test_name, test_func in filtered_tests
            if (
                test_func.__name__ == specific_test
                or specific_test.lower() in test_name.lower()
            )
        ]

        if not filtered_tests:
            print(f"No test found matching '{specific_test}'")
            return 1

        print(f"Running specific test: {specific_test}")

    # Filter by line numbers if specified
    if line_filters:
        line_filtered_tests = []

        for file_path, line_numbers in line_filters.items():
            # Get test names that match these line numbers
            matching_test_names = registry.get_tests_by_line(file_path, line_numbers)

            # Filter tests by matching names
            for suite_name, test_name, test_func in filtered_tests:
                if test_name in matching_test_names:
                    line_filtered_tests.append((suite_name, test_name, test_func))

        if not line_filtered_tests:
            lines_desc = ", ".join(
                [
                    f"{path}:{','.join(map(str, sorted(lines)))}"
                    for path, lines in line_filters.items()
                ]
            )
            print(f"No tests found at lines: {lines_desc}")
            return 1

        filtered_tests = line_filtered_tests
        lines_desc = ", ".join(
            [
                f"{Path(path).name}:{','.join(map(str, sorted(lines)))}"
                for path, lines in line_filters.items()
            ]
        )
        print(f"Running tests at lines: {lines_desc}")

    # Update registry with filtered tests if filtering was applied
    if len(filtered_tests) != len(all_tests):
        # Clear registry and re-add only filtered tests
        clear_registry()
        temp_registry = get_registry()

        # Group filtered tests by suite
        suite_tests = {}
        standalone_tests = []

        for suite_name, test_name, test_func in filtered_tests:
            if suite_name:
                if suite_name not in suite_tests:
                    suite_tests[suite_name] = []
                suite_tests[suite_name].append((test_name, test_func))
            else:
                standalone_tests.append((test_name, test_func))

        # Re-register tests (Note: we lose line number info here, but that's ok for filtered tests)
        temp_registry.standalone_tests = [
            (name, func, 0) for name, func in standalone_tests
        ]
        for suite_name, tests in suite_tests.items():
            suite = temp_registry.create_suite(suite_name)
            for test_name, test_func in tests:
                suite.add_test(test_name, test_func, 0)

    # Run tests
    runner = TestRunner(verbose=verbose)
    results = runner.run_all()

    # Format and display results
    formatter = TestFormatter(use_color=use_color, verbose=verbose)
    output = formatter.format_results(results, registry)
    print(output)

    # Return appropriate exit code
    failed_count = sum(1 for r in results if not r.passed)
    return 1 if failed_count > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
