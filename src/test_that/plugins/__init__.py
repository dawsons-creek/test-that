"""
Plugin system for the That testing library.

Provides extensible functionality through a secure, thread-safe plugin architecture.
"""

from .base import (
    AssertionPlugin,
    DecoratorPlugin,
    LifecyclePlugin,
    PluginBase,
    PluginInfo,
)
from .config import get_plugin_specific_config, load_plugin_config
from .registry import plugin_registry

__all__ = [
    "plugin_registry",
    "PluginBase",
    "DecoratorPlugin",
    "AssertionPlugin",
    "LifecyclePlugin",
    "PluginInfo",
    "load_plugin_config",
    "get_plugin_specific_config",
]
