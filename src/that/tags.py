"""
Test tagging functionality for selective test execution.

Provides decorators to tag tests and filter execution based on tags.
"""

from typing import Callable, Set


class TestTags:
    """Manages test tags for filtering."""
    
    def __init__(self):
        self.test_tags = {}  # test_func -> set of tags
        self.predefined_tags = {
            'slow': 'Tests that take a long time to run',
            'integration': 'Integration tests that require external resources',
            'unit': 'Unit tests that run in isolation', 
            'requires_network': 'Tests that require network access',
            'requires_db': 'Tests that require database access',
            'smoke': 'Quick smoke tests for basic functionality'
        }
    
    def add_tags(self, test_func: Callable, tags: Set[str]):
        """Add tags to a test function."""
        if test_func not in self.test_tags:
            self.test_tags[test_func] = set()
        self.test_tags[test_func].update(tags)
    
    def get_tags(self, test_func: Callable) -> Set[str]:
        """Get tags for a test function."""
        return self.test_tags.get(test_func, set())
    
    def has_tag(self, test_func: Callable, tag: str) -> bool:
        """Check if a test has a specific tag."""
        return tag in self.test_tags.get(test_func, set())
    
    def should_run(self, test_func: Callable, include_tags: Set[str] = None, 
                   exclude_tags: Set[str] = None) -> bool:
        """Determine if a test should run based on tag filters."""
        test_tags = self.get_tags(test_func)
        
        # If exclude tags specified, skip if test has any of them
        if exclude_tags and test_tags.intersection(exclude_tags):
            return False
        
        # If include tags specified, only run if test has at least one
        if include_tags and not test_tags.intersection(include_tags):
            return False
        
        return True


# Global tag registry
_tag_registry = TestTags()


def tag(*tags: str):
    """
    Decorator to add tags to a test.
    
    Example:
        @test("network test")
        @tag("slow", "requires_network")
        def test_api_call():
            ...
    """
    def decorator(func: Callable) -> Callable:
        _tag_registry.add_tags(func, set(tags))
        return func
    return decorator


# Predefined tag decorators for convenience
def slow(func: Callable) -> Callable:
    """Mark test as slow."""
    return tag("slow")(func)


def integration(func: Callable) -> Callable:
    """Mark test as integration test."""
    return tag("integration")(func)


def unit(func: Callable) -> Callable:
    """Mark test as unit test."""
    return tag("unit")(func)


def requires_network(func: Callable) -> Callable:
    """Mark test as requiring network access."""
    return tag("requires_network")(func)


def requires_db(func: Callable) -> Callable:
    """Mark test as requiring database access."""
    return tag("requires_db")(func)


def smoke(func: Callable) -> Callable:
    """Mark test as smoke test."""
    return tag("smoke")(func)


def get_tag_registry() -> TestTags:
    """Get the global tag registry."""
    return _tag_registry