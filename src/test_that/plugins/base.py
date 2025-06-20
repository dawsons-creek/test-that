"""
Base classes and interfaces for the That plugin system.

Provides the foundation for all plugin types with comprehensive metadata support.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List


@dataclass
class PluginInfo:
    """Plugin metadata with version compatibility and dependencies."""
    name: str
    version: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    min_that_version: str = "0.1.0"
    max_that_version: str = "999.0.0"
    author: str = "Unknown"
    url: str = ""
    priority: int = 100  # Lower number = higher priority


class PluginBase(ABC):
    """Base class for all That plugins with lifecycle management."""

    @property
    @abstractmethod
    def info(self) -> PluginInfo:
        """Return plugin metadata."""
        pass

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration."""
        pass

    def cleanup(self) -> None:
        """Cleanup plugin resources."""
        pass

    def validate_dependencies(self) -> List[str]:
        """Validate plugin dependencies and return missing ones."""
        missing = []
        for dep in self.info.dependencies:
            try:
                __import__(dep)
            except ImportError:
                missing.append(dep)
        return missing


class DecoratorPlugin(PluginBase):
    """Plugin that provides test decorators."""

    @abstractmethod
    def get_decorators(self) -> Dict[str, Callable]:
        """Return dict of decorator_name -> decorator_function."""
        pass


class AssertionPlugin(PluginBase):
    """Plugin that extends assertion capabilities."""

    @abstractmethod
    def get_assertion_methods(self) -> Dict[str, Callable]:
        """Return dict of method_name -> method_function."""
        pass


class LifecyclePlugin(PluginBase):
    """Plugin that hooks into test lifecycle with async support."""

    def before_test_run(self) -> None:
        """Called before all tests start."""
        pass

    def after_test_run(self) -> None:
        """Called after all tests complete."""
        pass

    def before_test(self, test_name: str) -> None:
        """Called before each individual test."""
        pass

    def after_test(self, test_name: str, result: Any) -> None:
        """Called after each individual test."""
        pass

    def before_suite(self, suite_name: str) -> None:
        """Called before each test suite."""
        pass

    def after_suite(self, suite_name: str) -> None:
        """Called after each test suite."""
        pass

    # Async variants for modern testing workflows
    async def before_test_run_async(self) -> None:
        """Async version of before_test_run."""
        pass

    async def after_test_run_async(self) -> None:
        """Async version of after_test_run."""
        pass

    async def before_test_async(self, test_name: str) -> None:
        """Async version of before_test."""
        pass

    async def after_test_async(self, test_name: str, result: Any) -> None:
        """Async version of after_test."""
        pass

    async def before_suite_async(self, suite_name: str) -> None:
        """Async version of before_suite."""
        pass

    async def after_suite_async(self, suite_name: str) -> None:
        """Async version of after_suite."""
        pass


class PluginError(Exception):
    """Base exception for plugin-related errors."""
    pass


class PluginConflictError(PluginError):
    """Raised when plugins conflict with each other."""
    pass


class PluginDependencyError(PluginError):
    """Raised when plugin dependencies are missing."""
    pass


class PluginVersionError(PluginError):
    """Raised when plugin version is incompatible."""
    pass
