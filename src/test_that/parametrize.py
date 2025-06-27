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
    if isinstance(args_set, dict):
        param_desc = _format_dict_params(args_set)
        parametrized_test = _create_dict_parametrized_test(func, args_set)
    else:
        param_desc = _format_tuple_params(args_set)
        parametrized_test = _create_tuple_parametrized_test(func, args_set)
    
    full_description = f"{test_description} [{param_desc}]"
    line_number, file_path = _get_line_info()
    
    parametrized_test._original_func = func
    _registry.add_test(full_description, parametrized_test, line_number, file_path)

def _create_dict_parametrized_test(func: Callable, args_set: dict) -> Callable:
    """Creates a parametrized test from a dictionary of arguments."""
    def parametrized_test(**fixtures):
        combined_args = {**fixtures, **args_set}
        return func(**combined_args)
    return parametrized_test

def _create_tuple_parametrized_test(func: Callable, args_set: tuple) -> Callable:
    """Creates a parametrized test from a tuple of arguments."""
    def parametrized_test(**fixtures):
        sig = inspect.signature(func)
        params = list(sig.parameters.keys())
        combined_kwargs = fixtures.copy()
        for i, value in enumerate(args_set):
            if i < len(params):
                combined_kwargs[params[i]] = value
        return func(**combined_kwargs)
    return parametrized_test

def _get_line_info() -> Tuple[int, str]:
    """Get the line number and file path from the call stack."""
    frame = inspect.currentframe()
    if frame and frame.f_back and frame.f_back.f_back:
        line_number = frame.f_back.f_back.f_lineno
        file_path = frame.f_back.f_back.f_code.co_filename
        return line_number, file_path
    return 0, "<unknown>"


def _format_dict_params(args_dict: dict) -> str:
    """Format dict parameters for test description."""
    items = []
    for key, value in args_dict.items():
        items.append(f"{key}={repr(value)}")
    return ", ".join(items)


def _format_tuple_params(args_tuple: tuple) -> str:
    """Format tuple parameters for test description."""
    return ", ".join(repr(arg) for arg in args_tuple)