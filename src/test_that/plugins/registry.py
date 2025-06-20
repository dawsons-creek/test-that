"""
Thread-safe plugin registry with conflict resolution and lazy loading.

Provides central management of all plugins with comprehensive error handling
and performance optimizations.
"""

import importlib
import importlib.metadata
import importlib.util
import threading
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Type

from packaging import version

from .base import (
    AssertionPlugin,
    DecoratorPlugin,
    LifecyclePlugin,
    PluginBase,
    PluginConflictError,
    PluginDependencyError,
    PluginError,
    PluginInfo,
    PluginVersionError,
)
from .config import get_plugin_specific_config, is_plugin_enabled, load_plugin_config


class PluginRegistry:
    """Thread-safe central registry for managing plugins with lazy loading."""

    def __init__(self):
        self._plugins: Dict[str, PluginBase] = {}
        self._decorator_plugins: Dict[str, DecoratorPlugin] = {}
        self._assertion_plugins: List[AssertionPlugin] = []
        self._lifecycle_plugins: List[LifecyclePlugin] = []
        self._config: Dict[str, Any] = {}
        self._initialized = False
        self._lock = threading.RLock()
        self._lazy_plugins: Dict[str, Callable[[], PluginBase]] = {}
        self._plugin_load_times: Dict[str, float] = {}
        self._failed_plugins: Set[str] = set()

    def initialize(self, force: bool = False) -> None:
        """Initialize the plugin system with thread safety."""
        with self._lock:
            if self._initialized and not force:
                return

            start_time = time.perf_counter()

            try:
                # Load configuration
                self._config = load_plugin_config()

                # Load built-in plugins
                self._load_builtin_plugins()

                # Load external plugins from entry points
                self._load_entry_point_plugins()

                # Load plugins from directories
                self._load_directory_plugins()

                self._initialized = True

                load_time = time.perf_counter() - start_time
                if load_time > self._config.get('max_load_time', 5.0):
                    print(f"Warning: Plugin loading took {load_time:.2f}s")

            except Exception as e:
                if self._config.get('fail_on_plugin_error', False):
                    raise
                print(f"Warning: Plugin system initialization failed: {e}")

    def register_plugin(self, plugin_class: Type[PluginBase], force: bool = False) -> None:
        """Register a plugin with conflict detection and validation."""
        with self._lock:
            plugin = plugin_class()

            # Validate plugin info
            self._validate_plugin_info(plugin.info)

            # Check for conflicts
            if plugin.info.name in self._plugins and not force:
                existing = self._plugins[plugin.info.name]
                if not self._config.get('allow_plugin_override', False):
                    raise PluginConflictError(
                        f"Plugin '{plugin.info.name}' already registered "
                        f"(existing: v{existing.info.version}, new: v{plugin.info.version})"
                    )
                else:
                    print(f"Warning: Overriding plugin {plugin.info.name} "
                          f"v{existing.info.version} with v{plugin.info.version}")

            # Check dependencies
            missing_deps = plugin.validate_dependencies()
            if missing_deps:
                error_msg = f"Plugin '{plugin.info.name}' missing dependencies: {missing_deps}"
                if plugin.info.name not in self._config.get('optional_plugins', []):
                    raise PluginDependencyError(error_msg)
                else:
                    print(f"Warning: {error_msg}")
                    return

            # Check version compatibility
            self._check_version_compatibility(plugin.info)

            # Initialize plugin
            plugin_config = get_plugin_specific_config(plugin.info.name)
            try:
                start_time = time.perf_counter()
                plugin.initialize(plugin_config)
                self._plugin_load_times[plugin.info.name] = time.perf_counter() - start_time
            except Exception as e:
                raise PluginError(f"Plugin '{plugin.info.name}' initialization failed: {e}") from e

            # Register by type with priority sorting
            self._plugins[plugin.info.name] = plugin

            if isinstance(plugin, DecoratorPlugin):
                self._decorator_plugins[plugin.info.name] = plugin
            if isinstance(plugin, AssertionPlugin):
                self._assertion_plugins.append(plugin)
                self._assertion_plugins.sort(key=lambda p: p.info.priority)
            if isinstance(plugin, LifecyclePlugin):
                self._lifecycle_plugins.append(plugin)
                self._lifecycle_plugins.sort(key=lambda p: p.info.priority)

    def register_lazy_plugin(self, name: str, loader: Callable[[], PluginBase]) -> None:
        """Register a plugin for lazy loading."""
        with self._lock:
            if not is_plugin_enabled(name):
                return
            self._lazy_plugins[name] = loader

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """Get plugin by name, loading lazily if needed."""
        with self._lock:
            # Check if already loaded
            if name in self._plugins:
                return self._plugins[name]

            # Check if available for lazy loading
            if name in self._lazy_plugins:
                try:
                    plugin_class = self._lazy_plugins[name]()
                    self.register_plugin(plugin_class)
                    del self._lazy_plugins[name]  # Remove from lazy queue
                    return self._plugins[name]
                except Exception as e:
                    self._failed_plugins.add(name)
                    print(f"Warning: Failed to load lazy plugin '{name}': {e}")

            return None

    def get_decorators(self) -> Dict[str, Any]:
        """Get all decorators from decorator plugins."""
        with self._lock:
            decorators = {}
            for plugin in self._decorator_plugins.values():
                try:
                    plugin_decorators = plugin.get_decorators()
                    decorators.update(plugin_decorators)
                except Exception as e:
                    print(f"Warning: Error getting decorators from {plugin.info.name}: {e}")
            return decorators

    def get_assertion_methods(self) -> Dict[str, Callable]:
        """Get all assertion methods from assertion plugins."""
        with self._lock:
            methods = {}
            for plugin in self._assertion_plugins:
                try:
                    plugin_methods = plugin.get_assertion_methods()
                    methods.update(plugin_methods)
                except Exception as e:
                    print(f"Warning: Error getting assertions from {plugin.info.name}: {e}")
            return methods

    def trigger_lifecycle_event(self, event: str, *args, **kwargs) -> None:
        """Trigger lifecycle event on all lifecycle plugins."""
        with self._lock:
            for plugin in self._lifecycle_plugins:
                if hasattr(plugin, event):
                    try:
                        getattr(plugin, event)(*args, **kwargs)
                    except Exception as e:
                        print(f"Warning: Plugin {plugin.info.name} failed in {event}: {e}")

    async def trigger_lifecycle_event_async(self, event: str, *args, **kwargs) -> None:
        """Trigger async lifecycle event on all lifecycle plugins."""
        # Note: Not using lock here to avoid blocking async operations
        async_event = f"{event}_async"
        for plugin in self._lifecycle_plugins[:]:  # Copy to avoid modification during iteration
            if hasattr(plugin, async_event):
                try:
                    await getattr(plugin, async_event)(*args, **kwargs)
                except Exception as e:
                    print(f"Warning: Plugin {plugin.info.name} failed in {async_event}: {e}")

    def list_plugins(self) -> List[Dict[str, Any]]:
        """List all plugins with their metadata."""
        with self._lock:
            plugins_info = []
            for plugin in self._plugins.values():
                info = {
                    'name': plugin.info.name,
                    'version': plugin.info.version,
                    'description': plugin.info.description,
                    'type': self._get_plugin_types(plugin),
                    'dependencies': plugin.info.dependencies,
                    'load_time': self._plugin_load_times.get(plugin.info.name, 0),
                    'priority': plugin.info.priority
                }
                plugins_info.append(info)

            # Add lazy plugins
            for name in self._lazy_plugins:
                plugins_info.append({
                    'name': name,
                    'version': 'unknown',
                    'description': 'Lazy-loaded plugin',
                    'type': ['lazy'],
                    'dependencies': [],
                    'load_time': 0,
                    'priority': 100
                })

            return sorted(plugins_info, key=lambda p: p['name'])

    def cleanup(self) -> None:
        """Cleanup all plugins and resources."""
        with self._lock:
            for plugin in self._plugins.values():
                try:
                    plugin.cleanup()
                except Exception as e:
                    print(f"Warning: Plugin {plugin.info.name} cleanup failed: {e}")

            self._plugins.clear()
            self._decorator_plugins.clear()
            self._assertion_plugins.clear()
            self._lifecycle_plugins.clear()
            self._lazy_plugins.clear()
            self._plugin_load_times.clear()
            self._initialized = False

    def get_stats(self) -> Dict[str, Any]:
        """Get plugin system statistics."""
        with self._lock:
            return {
                'total_plugins': len(self._plugins),
                'decorator_plugins': len(self._decorator_plugins),
                'assertion_plugins': len(self._assertion_plugins),
                'lifecycle_plugins': len(self._lifecycle_plugins),
                'lazy_plugins': len(self._lazy_plugins),
                'failed_plugins': len(self._failed_plugins),
                'total_load_time': sum(self._plugin_load_times.values()),
                'average_load_time': (
                    sum(self._plugin_load_times.values()) / len(self._plugin_load_times)
                    if self._plugin_load_times else 0
                ),
                'initialized': self._initialized
            }

    def _load_builtin_plugins(self) -> None:
        """Load built-in plugins with lazy registration."""
        builtin_plugins = [
            ('replay', 'test_that.plugins.replay:ReplayPlugin'),
            ('json_schema', 'test_that.plugins.json_schema:JSONSchemaPlugin'),
            ('lifecycle', 'test_that.plugins.lifecycle:ExampleLifecyclePlugin'),
        ]

        for name, spec in builtin_plugins:
            if is_plugin_enabled(name):
                self.register_lazy_plugin(name, lambda s=spec: self._load_plugin_from_spec(s))

    def _load_entry_point_plugins(self) -> None:
        """Load plugins from entry points."""
        try:
            # Handle different versions of importlib.metadata
            entry_points = importlib.metadata.entry_points()
            if hasattr(entry_points, 'get'):
                # Older style
                plugin_entry_points = entry_points.get('test_that.plugins', [])
            else:
                # Newer style (Python 3.10+)
                plugin_entry_points = entry_points.select(group='test_that.plugins')

            for entry_point in plugin_entry_points:
                name = entry_point.name
                if is_plugin_enabled(name):
                    self.register_lazy_plugin(
                        name,
                        lambda ep=entry_point: ep.load()
                    )
        except Exception as e:
            print(f"Warning: Failed to load entry point plugins: {e}")

    def _load_directory_plugins(self) -> None:
        """Load plugins from configured directories."""
        plugin_dirs = self._config.get('plugin_directories', [])
        for dir_path in plugin_dirs:
            self._scan_directory_for_plugins(Path(dir_path))

    def _scan_directory_for_plugins(self, directory: Path) -> None:
        """Scan directory for plugin files."""
        if not directory.exists():
            return

        for file_path in directory.glob("*.py"):
            if file_path.name.startswith("plugin_"):
                name = file_path.stem[7:]  # Remove "plugin_" prefix
                if is_plugin_enabled(name):
                    self.register_lazy_plugin(
                        name,
                        lambda fp=file_path: self._load_plugin_from_file(fp)
                    )

    def _load_plugin_from_spec(self, spec: str) -> Type[PluginBase]:
        """Load plugin class from module:class specification."""
        module_name, class_name = spec.split(':')
        module = importlib.import_module(module_name)
        return getattr(module, class_name)

    def _load_plugin_from_file(self, file_path: Path) -> Type[PluginBase]:
        """Load plugin class from file."""
        spec = importlib.util.spec_from_file_location(f"plugin_{file_path.stem}", file_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load plugin from {file_path}")

        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        # Look for plugin class
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if (isinstance(attr, type) and
                issubclass(attr, PluginBase) and
                attr != PluginBase):
                return attr

        raise ImportError(f"No plugin class found in {file_path}")

    def _validate_plugin_info(self, info: PluginInfo) -> None:
        """Validate plugin metadata."""
        if not info.name:
            raise ValueError("Plugin name cannot be empty")

        if not info.version:
            raise ValueError("Plugin version cannot be empty")

        try:
            version.parse(info.version)
        except version.InvalidVersion:
            raise ValueError(f"Invalid plugin version: {info.version}") from None

    def _check_version_compatibility(self, info: PluginInfo) -> None:
        """Check if plugin version is compatible with That."""
        # This would check against the actual That version
        # For now, we'll assume compatibility
        current_version = "0.2.0"  # Would come from test_that.__version__

        try:
            if (version.parse(current_version) < version.parse(info.min_that_version) or
                version.parse(current_version) > version.parse(info.max_that_version)):
                raise PluginVersionError(
                    f"Plugin '{info.name}' requires That version "
                    f"{info.min_that_version}-{info.max_that_version}, "
                    f"but current version is {current_version}"
                )
        except version.InvalidVersion as e:
            print(f"Warning: Invalid version in plugin {info.name}: {e}")

    def _get_plugin_types(self, plugin: PluginBase) -> List[str]:
        """Get plugin types for metadata."""
        types = []
        if isinstance(plugin, DecoratorPlugin):
            types.append('decorator')
        if isinstance(plugin, AssertionPlugin):
            types.append('assertion')
        if isinstance(plugin, LifecyclePlugin):
            types.append('lifecycle')
        return types


# Global registry instance
plugin_registry = PluginRegistry()
