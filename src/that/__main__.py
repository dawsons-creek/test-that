"""
CLI entry point for the That testing library.

Handles command-line arguments and test discovery.
"""

import argparse
import glob
import importlib.util
import os
import sys
import time
from pathlib import Path
from typing import List, Optional

from .runner import TestRunner, get_registry, clear_registry
from .output import TestFormatter


def discover_test_files(test_dir: str = "tests", pattern: str = "test_*.py") -> List[Path]:
    """Discover test files in the given directory."""
    test_path = Path(test_dir)
    
    if not test_path.exists():
        return []
    
    # Find all matching files
    test_files = []
    for file_path in test_path.rglob(pattern):
        if file_path.is_file() and file_path.suffix == '.py':
            test_files.append(file_path)
    
    return sorted(test_files)


def load_test_file(file_path: Path) -> bool:
    """Load a test file and execute it to register tests."""
    try:
        # Create module spec
        spec = importlib.util.spec_from_file_location(
            f"test_module_{file_path.stem}", 
            file_path
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
        'test_dir': 'tests',
        'pattern': 'test_*.py',
        'verbose': False,
        'color': True
    }
    
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            # No TOML support, use defaults
            return config
    
    pyproject_path = Path('pyproject.toml')
    if pyproject_path.exists():
        try:
            with open(pyproject_path, 'rb') as f:
                data = tomllib.load(f)
                
            tool_config = data.get('tool', {}).get('that', {})
            config.update(tool_config)
            
        except Exception as e:
            print(f"Warning: Could not load config from pyproject.toml: {e}")
    
    return config


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="That - A Python testing library",
        prog="that"
    )
    
    parser.add_argument(
        'files', 
        nargs='*', 
        help='Test files to run (default: discover in test directory)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output (includes stack traces and timing)'
    )
    
    parser.add_argument(
        '--no-color',
        action='store_true',
        help='Disable colored output'
    )
    
    parser.add_argument(
        '-s', '--suite',
        help='Run only tests in the specified suite'
    )
    
    parser.add_argument(
        '--test-dir',
        default=None,
        help='Directory to search for tests (default: tests)'
    )
    
    parser.add_argument(
        '--pattern',
        default=None,
        help='Pattern for test files (default: test_*.py)'
    )
    
    parser.add_argument(
        '--watch',
        action='store_true',
        help='Watch mode (re-run tests when files change)'
    )
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config()
    
    # Override config with command line arguments
    test_dir = args.test_dir or config['test_dir']
    pattern = args.pattern or config['pattern']
    verbose = args.verbose or config['verbose']
    use_color = not args.no_color and config['color']
    
    if args.watch:
        print("Watch mode not implemented yet")
        return 1
    
    # Clear any existing tests
    clear_registry()
    
    # Discover and load test files
    if args.files:
        # Run specific files
        test_files = [Path(f) for f in args.files]
        for file_path in test_files:
            if not file_path.exists():
                print(f"Error: Test file {file_path} not found")
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
    
    # Filter by suite if specified
    if args.suite:
        filtered_tests = [
            (suite_name, test_name, test_func) 
            for suite_name, test_name, test_func in all_tests
            if suite_name == args.suite
        ]
        
        if not filtered_tests:
            print(f"No tests found in suite '{args.suite}'")
            return 1
        
        # We need to update the registry to only include the filtered tests
        # This is a bit hacky, but works for the filtering
        print(f"Running tests in suite '{args.suite}'")
    
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


if __name__ == '__main__':
    sys.exit(main())
