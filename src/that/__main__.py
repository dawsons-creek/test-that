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
    """Parse file argument that may contain line numbers."""
    if not _has_line_syntax(file_arg):
        return Path(file_arg), None

    parts = file_arg.rsplit(":", 1)
    file_path = Path(parts[0])
    line_spec = parts[1]

    line_numbers = _parse_line_specification(line_spec)
    return file_path, line_numbers


def _has_line_syntax(file_arg: str) -> bool:
    """Check if file argument has line number syntax."""
    has_colon = ":" in file_arg
    is_windows_absolute = (
        sys.platform == "win32" and len(file_arg) > 1 and file_arg[1] == ":"
    )
    return has_colon and not is_windows_absolute


def _parse_line_specification(line_spec: str) -> Set[int]:
    """Parse line specification into set of line numbers."""
    if "-" in line_spec:
        return _parse_line_range(line_spec)
    elif "," in line_spec:
        return _parse_multiple_lines(line_spec)
    else:
        return _parse_single_line(line_spec)


def _parse_line_range(line_spec: str) -> Set[int]:
    """Parse line range like '20-50'."""
    start, end = line_spec.split("-", 1)
    try:
        start_line = int(start)
        end_line = int(end)
        return set(range(start_line, end_line + 1))
    except ValueError:
        raise ValueError(f"Invalid line range: {line_spec}")


def _parse_multiple_lines(line_spec: str) -> Set[int]:
    """Parse multiple lines like '10,20,30'."""
    line_numbers = set()
    for line in line_spec.split(","):
        try:
            line_numbers.add(int(line.strip()))
        except ValueError:
            raise ValueError(f"Invalid line number: {line}")
    return line_numbers


def _parse_single_line(line_spec: str) -> Set[int]:
    """Parse single line like '42'."""
    try:
        return {int(line_spec)}
    except ValueError:
        raise ValueError(f"Invalid line number: {line_spec}")


def load_test_file(file_path: Path) -> bool:
    """Load a test file and execute it to register tests."""
    try:
        spec = _create_module_spec(file_path)
        if spec is None or spec.loader is None:
            print(f"Warning: Could not load {file_path}")
            return False

        module = importlib.util.module_from_spec(spec)
        _execute_module_with_path(spec, module, file_path)
        return True

    except Exception as e:
        print(f"Error loading {file_path}: {e}")
        return False


def _create_module_spec(file_path: Path):
    """Create module spec for test file."""
    return importlib.util.spec_from_file_location(
        f"test_module_{file_path.stem}", file_path
    )


def _execute_module_with_path(spec, module, file_path: Path):
    """Execute module with test directory in sys.path."""
    test_dir = str(file_path.parent)
    if test_dir not in sys.path:
        sys.path.insert(0, test_dir)
        try:
            spec.loader.exec_module(module)
        finally:
            sys.path.remove(test_dir)
    else:
        spec.loader.exec_module(module)


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


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description="That - A Python testing library", prog="that"
    )

    parser.add_argument(
        "files",
        nargs="*",
        help="Test files to run with optional line numbers (e.g., test.py:42, test.py:20-50)",
    )

    parser.add_argument(
        "-v", "--verbose", action="store_true",
        help="Verbose output (includes stack traces and timing)"
    )

    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    parser.add_argument(
        "-s", "--suite", help="Run only tests in the specified suite"
    )

    parser.add_argument(
        "-k", "--filter", help="Run tests matching pattern in description"
    )

    parser.add_argument(
        "--test-dir", default=None,
        help="Directory to search for tests (default: tests)"
    )

    parser.add_argument(
        "--pattern", default=None, help="Pattern for test files (default: test_*.py)"
    )

    parser.add_argument(
        "--watch", action="store_true",
        help="Watch mode (re-run tests when files change)"
    )

    parser.add_argument(
        "--include-tags", help="Run only tests with these tags (comma-separated)"
    )

    parser.add_argument(
        "--exclude-tags", help="Skip tests with these tags (comma-separated)"
    )

    parser.add_argument(
        "--skip-slow", action="store_true",
        help="Skip tests tagged as 'slow' (shortcut for --exclude-tags=slow)"
    )

    parser.add_argument(
        "--focus", action="store_true",
        help="Focus mode - show only failures with full context"
    )

    return parser


def parse_file_arguments(args) -> Tuple[Optional[str], dict]:
    """Parse file arguments and extract specific test names and line filters."""
    if not args.files:
        return None, {}

    specific_test = None
    line_filters = {}
    parsed_files = []

    for file_arg in args.files:
        if "::" in file_arg:
            file_and_test = file_arg.split("::", 1)
            parsed_files.append(file_and_test[0])
            specific_test = file_and_test[1]
        else:
            try:
                file_path, line_numbers = parse_file_with_line(file_arg)
                parsed_files.append(str(file_path))
                if line_numbers:
                    abs_path = str(file_path.resolve())
                    line_filters[abs_path] = line_numbers
            except ValueError as e:
                print(f"Error: {e}")
                raise SystemExit(1)

    args.files = parsed_files
    return specific_test, line_filters


def discover_test_files_from_args(args, config) -> List[Path]:
    """Discover test files based on arguments and configuration."""
    test_dir = args.test_dir or config["test_dir"]
    pattern = args.pattern or config["pattern"]

    if args.files:
        return _discover_specific_files(args.files, pattern)
    else:
        test_files = discover_test_files(test_dir, pattern)
        if not test_files:
            print(f"No test files found in {test_dir} matching {pattern}")
            raise SystemExit(0)
        return test_files


def _discover_specific_files(file_args: List[str], pattern: str) -> List[Path]:
    """Discover test files from specific file arguments."""
    test_files = []
    for file_arg in file_args:
        file_path = Path(file_arg)
        if file_path.is_file():
            if not file_path.exists():
                print(f"Error: Test file {file_path} not found")
                raise SystemExit(1)
            test_files.append(file_path)
        elif file_path.is_dir():
            dir_tests = discover_test_files(str(file_path), pattern)
            test_files.extend(dir_tests)
        else:
            print(f"Error: Path {file_path} not found")
            raise SystemExit(1)
    return test_files


def load_all_test_files(test_files: List[Path]) -> None:
    """Load all test files and validate at least one loaded successfully."""
    loaded_count = 0
    for file_path in test_files:
        if load_test_file(file_path):
            loaded_count += 1

    if loaded_count == 0:
        print("No test files could be loaded")
        raise SystemExit(1)


def apply_test_filters(args, specific_test: Optional[str], line_filters: dict):
    """Apply all test filters and return filtered tests."""
    registry = get_registry()
    all_tests = registry.get_all_tests()

    if not all_tests:
        print("No tests found")
        raise SystemExit(0)

    filtered_tests = all_tests
    filtered_tests = _apply_suite_filter(filtered_tests, args.suite)
    filtered_tests = _apply_pattern_filter(filtered_tests, args.filter)
    filtered_tests = _apply_specific_test_filter(filtered_tests, specific_test)
    filtered_tests = _apply_line_filters(filtered_tests, line_filters, registry)

    return filtered_tests, all_tests, registry


def _apply_suite_filter(tests, suite_name):
    """Filter tests by suite name."""
    if not suite_name:
        return tests

    filtered = [
        (sn, tn, tf) for sn, tn, tf in tests if sn == suite_name
    ]

    if not filtered:
        print(f"No tests found in suite '{suite_name}'")
        raise SystemExit(1)

    print(f"Running tests in suite '{suite_name}'")
    return filtered


def _apply_pattern_filter(tests, pattern):
    """Filter tests by pattern in description."""
    if not pattern:
        return tests

    filtered = [
        (sn, tn, tf) for sn, tn, tf in tests
        if pattern.lower() in tn.lower()
    ]

    if not filtered:
        print(f"No tests found matching pattern '{pattern}'")
        raise SystemExit(1)

    print(f"Running tests matching '{pattern}'")
    return filtered


def _apply_specific_test_filter(tests, specific_test):
    """Filter tests by specific test name."""
    if not specific_test:
        return tests

    filtered = [
        (sn, tn, tf) for sn, tn, tf in tests
        if (tf.__name__ == specific_test or specific_test.lower() in tn.lower())
    ]

    if not filtered:
        print(f"No test found matching '{specific_test}'")
        raise SystemExit(1)

    print(f"Running specific test: {specific_test}")
    return filtered


def _apply_line_filters(tests, line_filters, registry):
    """Filter tests by line numbers."""
    if not line_filters:
        return tests

    line_filtered_tests = []
    for file_path, line_numbers in line_filters.items():
        matching_test_names = registry.get_tests_by_line(file_path, line_numbers)
        for sn, tn, tf in tests:
            if tn in matching_test_names:
                line_filtered_tests.append((sn, tn, tf))

    if not line_filtered_tests:
        lines_desc = ", ".join([
            f"{path}:{','.join(map(str, sorted(lines)))}"
            for path, lines in line_filters.items()
        ])
        print(f"No tests found at lines: {lines_desc}")
        raise SystemExit(1)

    lines_desc = ", ".join([
        f"{Path(path).name}:{','.join(map(str, sorted(lines)))}"
        for path, lines in line_filters.items()
    ])
    print(f"Running tests at lines: {lines_desc}")
    return line_filtered_tests


def update_registry_with_filtered_tests(filtered_tests, all_tests):
    """Update registry with only the filtered tests."""
    if len(filtered_tests) == len(all_tests):
        return

    clear_registry()
    temp_registry = get_registry()

    suite_tests = {}
    standalone_tests = []

    for suite_name, test_name, test_func in filtered_tests:
        if suite_name:
            if suite_name not in suite_tests:
                suite_tests[suite_name] = []
            suite_tests[suite_name].append((test_name, test_func))
        else:
            standalone_tests.append((test_name, test_func))

    temp_registry.standalone_tests = [
        (name, func, 0) for name, func in standalone_tests
    ]
    for suite_name, tests in suite_tests.items():
        suite = temp_registry.create_suite(suite_name)
        for test_name, test_func in tests:
            suite.add_test(test_name, test_func, 0)


def parse_tag_filters(args) -> Tuple[Optional[set], Optional[set]]:
    """Parse tag filter arguments."""
    include_tags = None
    exclude_tags = None

    if args.include_tags:
        include_tags = set(tag.strip() for tag in args.include_tags.split(','))

    if args.exclude_tags:
        exclude_tags = set(tag.strip() for tag in args.exclude_tags.split(','))

    if args.skip_slow:
        if exclude_tags is None:
            exclude_tags = set()
        exclude_tags.add('slow')

    return include_tags, exclude_tags


def run_tests_and_format_output(args, config, include_tags, exclude_tags, registry):
    """Run tests and format output."""
    verbose = args.verbose or config["verbose"]
    use_color = not args.no_color and config["color"]

    runner = TestRunner(
        verbose=verbose, include_tags=include_tags, exclude_tags=exclude_tags
    )
    results = runner.run_all()

    formatter = TestFormatter(
        use_color=use_color, verbose=verbose, focus_mode=args.focus
    )
    output = formatter.format_results(results, registry)
    print(output)

    failed_count = sum(1 for r in results if not r.passed)
    return 1 if failed_count > 0 else 0


def main():
    """Main CLI entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    config = load_config()

    if args.watch:
        print("Watch mode not implemented yet")
        return 1

    clear_registry()

    specific_test, line_filters = parse_file_arguments(args)
    test_files = discover_test_files_from_args(args, config)
    load_all_test_files(test_files)

    filtered_tests, all_tests, registry = apply_test_filters(
        args, specific_test, line_filters
    )
    update_registry_with_filtered_tests(filtered_tests, all_tests)

    include_tags, exclude_tags = parse_tag_filters(args)

    return run_tests_and_format_output(
        args, config, include_tags, exclude_tags, registry
    )


if __name__ == "__main__":
    sys.exit(main())
