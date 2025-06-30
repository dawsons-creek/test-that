"""
Configuration management for the plugin system with caching and validation.
"""

import os
import threading
from pathlib import Path
from typing import Any, Dict, List


class ConfigCache:
    """Thread-safe configuration cache with automatic invalidation."""

    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._file_mtimes: Dict[str, float] = {}

    def get(self, key: str, loader_func, file_path: str = None):
        """Get cached config or load if stale."""
        with self._lock:
            # Check if file has been modified
            if file_path and self._is_file_modified(file_path):
                self._cache.pop(key, None)

            if key not in self._cache:
                self._cache[key] = loader_func()
                if file_path:
                    self._file_mtimes[key] = self._get_file_mtime(file_path)

            return self._cache[key]

    def invalidate(self, key: str = None):
        """Invalidate specific key or entire cache."""
        with self._lock:
            if key:
                self._cache.pop(key, None)
                self._file_mtimes.pop(key, None)
            else:
                self._cache.clear()
                self._file_mtimes.clear()

    def _is_file_modified(self, file_path: str) -> bool:
        """Check if file has been modified since last cache."""
        current_mtime = self._get_file_mtime(file_path)
        cached_mtime = self._file_mtimes.get(file_path, 0)
        return current_mtime > cached_mtime

    def _get_file_mtime(self, file_path: str) -> float:
        """Get file modification time, return 0 if file doesn't exist."""
        try:
            return os.path.getmtime(file_path)
        except OSError:
            return 0


# Global configuration cache
_config_cache = ConfigCache()


def load_plugin_config() -> Dict[str, Any]:
    """Load plugin configuration with caching and validation."""
    pyproject_path = "pyproject.toml"

    return _config_cache.get(
        "plugin_config", lambda: _load_toml_config(), pyproject_path
    )


def _load_toml_config() -> Dict[str, Any]:
    """Load TOML configuration with fallback support."""
    config = {
        "enabled": [],  # Empty list means all available plugins enabled
        "disabled": [],
        "auto_discover": True,
        "fail_on_plugin_error": False,
        "allow_plugin_override": False,
        "plugin_directories": [],
        "max_load_time": 5.0,  # Maximum seconds to spend loading plugins
    }

    # Try different TOML libraries
    toml_loader = _get_toml_loader()
    if not toml_loader:
        return config

    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return config

    try:
        with open(pyproject_path, "rb") as f:
            data = toml_loader(f)

        # Extract plugin configuration
        plugin_config = data.get("tool", {}).get("that", {}).get("plugins", {})
        config.update(plugin_config)

        # Validate configuration
        _validate_config(config)

    except Exception as e:
        print(f"Warning: Could not load plugin config from pyproject.toml: {e}")

    return config


def _get_toml_loader():
    """Get appropriate TOML loader function."""
    try:
        import tomllib

        return tomllib.load
    except ImportError:
        try:
            import tomli

            return tomli.load
        except ImportError:
            try:
                import toml

                def toml_load(f):
                    f.seek(0)
                    return toml.load(f.read().decode("utf-8"))

                return toml_load
            except ImportError:
                return None


def _validate_config(config: Dict[str, Any]) -> None:
    """Validate plugin configuration."""
    # Validate plugin names
    for name in config.get("enabled", []):
        if not _is_valid_plugin_name(name):
            raise ValueError(f"Invalid plugin name: {name}")

    for name in config.get("disabled", []):
        if not _is_valid_plugin_name(name):
            raise ValueError(f"Invalid plugin name: {name}")

    # Validate directories
    for dir_path in config.get("plugin_directories", []):
        path = Path(dir_path)
        if not path.exists():
            print(f"Warning: Plugin directory not found: {dir_path}")

    # Validate numeric values
    max_load_time = config.get("max_load_time", 5.0)
    if not isinstance(max_load_time, (int, float)) or max_load_time <= 0:
        raise ValueError(
            f"max_load_time must be a positive number, got: {max_load_time}"
        )


def _is_valid_plugin_name(name: str) -> bool:
    """Validate plugin name format."""
    if not isinstance(name, str):
        return False
    if not name or len(name) > 100:
        return False
    # Allow alphanumeric, underscore, dash
    return all(c.isalnum() or c in "_-" for c in name)


def get_plugin_specific_config(plugin_name: str) -> Dict[str, Any]:
    """Get configuration for specific plugin with caching."""
    cache_key = f"plugin_{plugin_name}"
    pyproject_path = "pyproject.toml"

    return _config_cache.get(
        cache_key, lambda: _load_plugin_specific_config(plugin_name), pyproject_path
    )


def _load_plugin_specific_config(plugin_name: str) -> Dict[str, Any]:
    """Load plugin-specific configuration."""
    toml_loader = _get_toml_loader()
    if not toml_loader:
        return {}

    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {}

    try:
        with open(pyproject_path, "rb") as f:
            data = toml_loader(f)

        plugin_configs = data.get("tool", {}).get("that", {}).get("plugins", {})
        return plugin_configs.get(plugin_name, {})

    except Exception:
        return {}


def invalidate_config_cache(plugin_name: str = None):
    """Invalidate configuration cache."""
    if plugin_name:
        _config_cache.invalidate(f"plugin_{plugin_name}")
    else:
        _config_cache.invalidate()


def list_available_plugins() -> List[str]:
    """List all available plugins from configuration."""
    config = load_plugin_config()
    enabled = config.get("enabled", [])
    disabled = config.get("disabled", [])

    # If enabled list is empty, all discovered plugins are enabled
    if not enabled:
        # This would be populated by plugin discovery
        enabled = []

    return [name for name in enabled if name not in disabled]


def is_plugin_enabled(plugin_name: str) -> bool:
    """Check if a specific plugin is enabled."""
    config = load_plugin_config()
    enabled = config.get("enabled", [])
    disabled = config.get("disabled", [])

    # If plugin is explicitly disabled, return False
    if plugin_name in disabled:
        return False

    # If enabled list is empty, all plugins are enabled by default
    if not enabled:
        return True

    # Otherwise, plugin must be in enabled list
    return plugin_name in enabled
