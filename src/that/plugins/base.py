"""
Base classes and interfaces for That plugins.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field


@dataclass
class PluginInfo:
    """Metadata about a plugin."""
    name: str
    version: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)


class PluginBase(ABC):
    """Base class for all That plugins."""

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
    """Plugin that hooks into test lifecycle."""

    def before_test_run(self) -> None:
        """Called before all tests start running."""
        pass

    def after_test_run(self) -> None:
        """Called after all tests finish running."""
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
