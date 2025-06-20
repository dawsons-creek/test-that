"""
Configuration loading for the plugin system.
"""

from pathlib import Path
from typing import Dict, Any


def load_plugin_config() -> Dict[str, Any]:
    """Load plugin configuration from pyproject.toml."""
    config = {
        "enabled": [],  # Empty means all available plugins
        "disabled": [],
        "plugin_directories": [],
        "auto_discover": True,
        "fail_on_plugin_error": False,
    }
    
    # Use the same TOML loading logic as the main config
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return config
    
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            
            # Load plugin configuration
            plugin_config = data.get("tool", {}).get("that", {}).get("plugins", {})
            config.update(plugin_config)
            
        except Exception as e:
            print(f"Warning: Could not load plugin config from pyproject.toml: {e}")
    
    return config


def get_plugin_specific_config(plugin_name: str) -> Dict[str, Any]:
    """Get configuration specific to a plugin."""
    try:
        import tomllib
    except ImportError:
        try:
            import tomli as tomllib
        except ImportError:
            return {}
    
    pyproject_path = Path("pyproject.toml")
    if pyproject_path.exists():
        try:
            with open(pyproject_path, "rb") as f:
                data = tomllib.load(f)
            
            # Load plugin-specific configuration
            return data.get("tool", {}).get("that", {}).get("plugins", {}).get(plugin_name, {})
            
        except Exception:
            return {}
    
    return {}
