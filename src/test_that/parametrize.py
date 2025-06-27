"""
Parametrized test support for test-that testing framework.

Allows running the same test with multiple sets of parameters.
"""

import inspect
from typing import Any, Callable, List, Tuple, Union
from .runner import _registry


def parametrize(*args_sets: Union[Tuple[Any, ...], List[Tuple[Any, ...]]]):
    """
    Decorator to run a test with multiple parameter sets.
    
    Usage:
        @parametrize((1, 2, 3), (2, 3, 5), (3, 4, 7))
        @test("addition works")
        def test_add(a, b, expected):
            that(a + b).equals(expected)
            
        # Or with named tuples for clarity:
        @parametrize(
            {"input": 1, "expected": 2},
            {"input": 2, "expected": 4}
        )
        @test("doubles numbers")
        def test_double(input, expected):
            that(double(input)).equals(expected)
    """
    def decorator(func: Callable):
        # Get the original test description from the @test decorator
        test_description = getattr(func, '_test_description', func.__name__)
        
        # Remove the original test from registry if it was added
        _remove_test_from_registry(func)
        
        # Create parametrized tests
        for i, args_set in enumerate(args_sets):
            _create_parametrized_test(func, test_description, args_set, i)
                
        return func
    
    return decorator


def _remove_test_from_registry(func: Callable):
    """Remove a test function from the registry."""
    # Remove from standalone tests
    _registry.standalone_tests = [
        (name, test_func, line) for name, test_func, line in _registry.standalone_tests
        if test_func != func
    ]
    
    # Remove from suites
    for suite in _registry.suites.values():
        suite.tests = [
            (name, test_func, line) for name, test_func, line in suite.tests
            if test_func != func
        ]


def _create_parametrized_test(func: Callable, test_description: str, args_set: Any, index: int):
    """Create a single parametrized test instance."""
    # Handle both tuple/list args and dict args
    if isinstance(args_set, dict):
        param_desc = _format_dict_params(args_set)
        def parametrized_test(**fixtures):
            # Merge fixture args with parametrized args
            combined_args = {**fixtures, **args_set}
            return func(**combined_args)
    else:
        param_desc = _format_tuple_params(args_set)
        def parametrized_test(**fixtures):
            # Get function signature to map args correctly
            sig = inspect.signature(func)
            params = list(sig.parameters.keys())
            
            # Build combined arguments
            combined_kwargs = fixtures.copy()
            
            # Add parametrized args based on parameter order
            for i, value in enumerate(args_set):
                if i < len(params):
                    combined_kwargs[params[i]] = value
            
            # Debug: Check what we're passing
            # print(f"Function: {func.__name__}, Params: {params}, Fixtures: {fixtures}, Combined: {combined_kwargs}")
                        
            return func(**combined_kwargs)
    
    # Create descriptive test name
    full_description = f"{test_description} [{param_desc}]"
    
    # Get line number from original function
    frame = inspect.currentframe()
    if frame and frame.f_back and frame.f_back.f_back:
        line_number = frame.f_back.f_back.f_lineno
        file_path = frame.f_back.f_back.f_code.co_filename
    else:
        line_number = 0
        file_path = "<unknown>"
    
    # Store original function for fixture resolution
    parametrized_test._original_func = func
    
    # Register the parametrized test
    _registry.add_test(full_description, parametrized_test, line_number, file_path)


def _format_dict_params(args_dict: dict) -> str:
    """Format dict parameters for test description."""
    items = []
    for key, value in args_dict.items():
        items.append(f"{key}={repr(value)}")
    return ", ".join(items)


def _format_tuple_params(args_tuple: tuple) -> str:
    """Format tuple parameters for test description."""
    return ", ".join(repr(arg) for arg in args_tuple)