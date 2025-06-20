"""
Plugin system for the That testing library.

This module provides the core plugin infrastructure including:
- Plugin base classes and interfaces
- Plugin registry and management
- Plugin discovery and loading
- Configuration support
"""

from .base import PluginBase, DecoratorPlugin, AssertionPlugin, LifecyclePlugin, PluginInfo
from .registry import PluginRegistry, plugin_registry
from .config import load_plugin_config

__all__ = [
    "PluginBase",
    "DecoratorPlugin", 
    "AssertionPlugin",
    "LifecyclePlugin",
    "PluginInfo",
    "PluginRegistry",
    "plugin_registry",
    "load_plugin_config",
]
