"""
Plugin system for the That testing library.

Provides extensible functionality through a secure, thread-safe plugin architecture.
"""

from .registry import plugin_registry
from .base import PluginBase, DecoratorPlugin, AssertionPlugin, LifecyclePlugin, PluginInfo
from .config import load_plugin_config, get_plugin_specific_config

__all__ = [
    'plugin_registry',
    'PluginBase', 
    'DecoratorPlugin',
    'AssertionPlugin', 
    'LifecyclePlugin',
    'PluginInfo',
    'load_plugin_config',
    'get_plugin_specific_config'
]