"""
Plugin registry and management for the That testing library.
"""

import importlib
import importlib.util
from pathlib import Path
from typing import Dict, List, Type, Any, Optional, Callable

from .base import PluginBase, PluginInfo, DecoratorPlugin, AssertionPlugin, LifecyclePlugin
from .config import load_plugin_config, get_plugin_specific_config


class PluginRegistry:
    """Central registry for managing plugins."""

    def __init__(self):
        self._plugins: Dict[str, PluginBase] = {}
        self._decorator_plugins: Dict[str, DecoratorPlugin] = {}
        self._assertion_plugins: List[AssertionPlugin] = []
        self._lifecycle_plugins: List[LifecyclePlugin] = []
        self._config: Dict[str, Any] = {}
        self._initialized = False

    def initialize(self) -> None:
        """Initialize the plugin system."""
        if self._initialized:
            return
            
        # Load configuration
        self._config = load_plugin_config()
        
        # Load built-in plugins
        self.load_builtin_plugins()
        
        # Load external plugins from entry points
        self.load_entry_point_plugins()
        
        self._initialized = True

    def load_builtin_plugins(self) -> None:
        """Load built-in plugins (replay functionality)."""
        builtin_plugins = [
            'that.plugins.replay:ReplayPlugin',
        ]

        for plugin_spec in builtin_plugins:
            if self._is_plugin_enabled(plugin_spec):
                self.load_plugin_from_spec(plugin_spec)

    def load_entry_point_plugins(self) -> None:
        """Load plugins from entry points."""
        try:
            import importlib.metadata

            # Handle different versions of importlib.metadata
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'get'):
                # Older style
                plugin_entry_points = entry_points.get('that.plugins', [])
            else:
                # Newer style (Python 3.10+)
                plugin_entry_points = entry_points.select(group='that.plugins')

            for entry_point in plugin_entry_points:
                try:
                    plugin_class = entry_point.load()
                    self.register_plugin(plugin_class)
                except Exception as e:
                    if self._config.get('fail_on_plugin_error', False):
                        raise
                    print(f"Warning: Could not load plugin {entry_point.name}: {e}")

        except ImportError:
            # importlib.metadata not available in older Python versions
            pass

    def load_plugin_from_spec(self, spec: str) -> None:
        """Load plugin from module:class specification."""
        module_name, class_name = spec.split(':')
        try:
            module = importlib.import_module(module_name)
            plugin_class = getattr(module, class_name)
            self.register_plugin(plugin_class)
        except (ImportError, AttributeError) as e:
            # Log warning but don't fail - plugin dependencies might be missing
            if self._config.get('fail_on_plugin_error', False):
                raise
            print(f"Warning: Could not load plugin {spec}: {e}")

    def register_plugin(self, plugin_class: Type[PluginBase]) -> None:
        """Register a plugin class."""
        plugin = plugin_class()

        # Check dependencies
        if not self._check_dependencies(plugin.info):
            return

        # Initialize plugin
        plugin_config = get_plugin_specific_config(plugin.info.name)
        plugin.initialize(plugin_config)

        # Register by type
        self._plugins[plugin.info.name] = plugin

        if isinstance(plugin, DecoratorPlugin):
            self._decorator_plugins[plugin.info.name] = plugin
        if isinstance(plugin, AssertionPlugin):
            self._assertion_plugins.append(plugin)
        if isinstance(plugin, LifecyclePlugin):
            self._lifecycle_plugins.append(plugin)

    def _check_dependencies(self, plugin_info: PluginInfo) -> bool:
        """Check if plugin dependencies are available."""
        for dep in plugin_info.dependencies:
            try:
                importlib.import_module(dep)
            except ImportError:
                print(f"Warning: Plugin {plugin_info.name} disabled - missing dependency: {dep}")
                return False
        return True

    def _is_plugin_enabled(self, plugin_spec: str) -> bool:
        """Check if a plugin is enabled in configuration."""
        plugin_name = plugin_spec.split(':')[1].lower()
        
        enabled = self._config.get('enabled', [])
        disabled = self._config.get('disabled', [])
        
        # If enabled list is empty, all plugins are enabled by default
        if not enabled:
            return plugin_name not in disabled
        
        return plugin_name in enabled and plugin_name not in disabled

    def get_decorators(self) -> Dict[str, Any]:
        """Get all decorators from decorator plugins."""
        decorators = {}
        for plugin in self._decorator_plugins.values():
            decorators.update(plugin.get_decorators())
        return decorators

    def get_assertion_methods(self) -> Dict[str, Callable]:
        """Get all assertion methods from assertion plugins."""
        methods = {}
        for plugin in self._assertion_plugins:
            methods.update(plugin.get_assertion_methods())
        return methods

    def trigger_lifecycle_event(self, event: str, *args, **kwargs) -> None:
        """Trigger lifecycle event on all lifecycle plugins."""
        for plugin in self._lifecycle_plugins:
            if hasattr(plugin, event):
                try:
                    getattr(plugin, event)(*args, **kwargs)
                except Exception as e:
                    if self._config.get('fail_on_plugin_error', False):
                        raise
                    print(f"Warning: Plugin {plugin.info.name} failed on {event}: {e}")

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get a loaded plugin by name."""
        return self._plugins.get(name)

    def cleanup(self) -> None:
        """Cleanup all plugins."""
        for plugin in self._plugins.values():
            try:
                plugin.cleanup()
            except Exception as e:
                print(f"Warning: Plugin {plugin.info.name} cleanup failed: {e}")


# Global registry instance
plugin_registry = PluginRegistry()
