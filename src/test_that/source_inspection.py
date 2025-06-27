"""
Robust source code inspection for test-that framework.

Replaces fragile stack inspection with reliable source analysis
using inspect.getsourcelines() and AST parsing.
"""

import ast
import inspect
import warnings
from pathlib import Path
from typing import Callable, Optional, Tuple


class SourceMapper:
    """Maps functions to their source locations reliably."""
    
    def __init__(self):
        self._cache = {}
    
    def get_line_info(self, func: Callable) -> Tuple[int, str]:
        """Get line number and file path for a function using robust methods."""
        
        # Check cache first
        cache_key = (func.__module__, func.__qualname__)
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        result = self._get_line_info_robust(func)
        self._cache[cache_key] = result
        return result
    
    def _get_line_info_robust(self, func: Callable) -> Tuple[int, str]:
        """Get line info using multiple robust methods with fallbacks."""
        
        # Method 1: Use inspect.getsourcelines (most reliable)
        try:
            _, line_number = inspect.getsourcelines(func)
            file_path = inspect.getfile(func)
            return line_number, file_path
        except (OSError, TypeError, IOError):
            pass
        
        # Method 2: Use function code object
        try:
            if hasattr(func, '__code__'):
                line_number = func.__code__.co_firstlineno
                file_path = func.__code__.co_filename
                if line_number > 0 and file_path != '<string>':
                    return line_number, file_path
        except (AttributeError, TypeError):
            pass
        
        # Method 3: AST parsing for decorated functions
        try:
            return self._get_line_from_ast(func)
        except Exception:
            pass
        
        # Method 4: Stack inspection fallback (with warning)
        return self._get_line_info_stack_fallback(func)
    
    def _get_line_from_ast(self, func: Callable) -> Tuple[int, str]:
        """Extract line number using AST parsing."""
        try:
            file_path = inspect.getfile(func)
            func_name = func.__name__
            
            # Read source file
            source_path = Path(file_path)
            if not source_path.exists():
                raise FileNotFoundError(f"Source file not found: {file_path}")
            
            with open(source_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Parse AST and find function
            tree = ast.parse(source, filename=file_path)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name == func_name:
                    return node.lineno, file_path
                elif isinstance(node, ast.AsyncFunctionDef) and node.name == func_name:
                    return node.lineno, file_path
            
            # If not found, try looking in classes
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    for item in node.body:
                        if (isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)) 
                            and item.name == func_name):
                            return item.lineno, file_path
            
            raise ValueError(f"Function {func_name} not found in AST")
            
        except Exception as e:
            raise RuntimeError(f"AST parsing failed: {e}") from e
    
    def _get_line_info_stack_fallback(self, func: Callable) -> Tuple[int, str]:
        """Fallback to stack inspection with warning."""
        warnings.warn(
            f"Using fragile stack inspection for function '{func.__name__}'. "
            "Line numbers may be inaccurate. Consider using explicit source mapping.",
            UserWarning,
            stacklevel=4
        )
        
        # Try to get some info from the function itself
        try:
            file_path = inspect.getfile(func)
            line_number = getattr(func, '__code__', type('', (), {'co_firstlineno': 0})).co_firstlineno
            return max(line_number, 1), file_path
        except (OSError, TypeError):
            pass
        
        # Last resort: use current frame
        frame = inspect.currentframe()
        try:
            # Walk up the stack to find a reasonable caller
            for _ in range(5):  # Look up to 5 frames
                if frame and frame.f_back:
                    frame = frame.f_back
                    if frame.f_code.co_filename != __file__:
                        return frame.f_lineno, frame.f_code.co_filename
            
            return 0, "<unknown>"
        finally:
            del frame  # Prevent reference cycles
    
    def clear_cache(self):
        """Clear the source location cache."""
        self._cache.clear()


# Global source mapper instance
_source_mapper = SourceMapper()


def get_line_info(func: Callable) -> Tuple[int, str]:
    """Get line number and file path for a function.
    
    This is the main entry point for getting source location information.
    It uses multiple robust methods with graceful fallbacks.
    
    Args:
        func: The function to inspect
        
    Returns:
        Tuple of (line_number, file_path)
    """
    return _source_mapper.get_line_info(func)


def get_source_mapper() -> SourceMapper:
    """Get the global source mapper instance."""
    return _source_mapper


def with_explicit_line_info(line: int, file: str):
    """Decorator to explicitly set line information for a function.
    
    Useful when automatic detection fails or for generated functions.
    
    Usage:
        @with_explicit_line_info(42, "/path/to/file.py")
        def my_test():
            pass
    """
    def decorator(func: Callable) -> Callable:
        # Store explicit line info on the function
        func._explicit_line_info = (line, file)
        return func
    return decorator


def get_line_info_with_explicit(func: Callable) -> Tuple[int, str]:
    """Get line info, checking for explicit annotation first."""
    # Check for explicit line info first
    if hasattr(func, '_explicit_line_info'):
        return func._explicit_line_info
    
    return get_line_info(func)