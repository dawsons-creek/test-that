"""
Tests for plugin configuration management.

Tests configuration loading, caching, and validation.
"""

import tempfile
import os
from pathlib import Path

from test_that import suite, test, that


with suite("Configuration Loading"):

    @test("loads plugin configuration")
    def test_plugin_config_loading():
        from test_that.plugins.config import load_plugin_config
        
        # This should return default config if no pyproject.toml exists
        config = load_plugin_config()
        
        that(isinstance(config, dict)).equals(True)
        that("enabled" in config).equals(True)
        that("disabled" in config).equals(True)
        that("auto_discover" in config).equals(True)

    @test("ConfigCache provides caching functionality")
    def test_config_cache():
        from test_that.plugins.config import ConfigCache
        
        cache = ConfigCache()
        
        # Test basic caching functionality
        result1 = cache.get("test_key", lambda: {"value": "test"})
        result2 = cache.get("test_key", lambda: {"value": "different"})
        
        # Should return cached result
        that(result1).equals(result2)
        that(result1["value"]).equals("test")

    @test("ConfigCache invalidation works")
    def test_config_cache_invalidation():
        from test_that.plugins.config import ConfigCache
        
        cache = ConfigCache()
        
        # Load initial value
        result1 = cache.get("test_key", lambda: {"value": "first"})
        that(result1["value"]).equals("first")
        
        # Invalidate and reload
        cache.invalidate("test_key")
        result2 = cache.get("test_key", lambda: {"value": "second"})
        that(result2["value"]).equals("second")


