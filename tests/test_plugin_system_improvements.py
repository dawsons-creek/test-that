"""
Tests for the improved plugin system.

Tests thread safety, security, configuration caching, and other improvements.
"""

import time
import threading
from test_that import test, suite, that


with suite("Plugin System Security"):
    
    @test("HTTP recording sanitizes sensitive headers")
    def test_http_sanitization():
        """Test that HTTP recording sanitizes sensitive data."""
        from test_that.plugins.security import SecuritySanitizer
        
        sanitizer = SecuritySanitizer()
        
        headers = {
            'Authorization': 'Bearer secret-token',
            'Content-Type': 'application/json',
            'X-API-Key': 'super-secret-key'
        }
        
        sanitized = sanitizer.sanitize_headers(headers)
        
        that(sanitized['Authorization']).equals('***REDACTED***')
        that(sanitized['Content-Type']).equals('application/json')
        that(sanitized['X-API-Key']).equals('***REDACTED***')
    
    @test("URL sanitization removes sensitive parameters")
    def test_url_sanitization():
        """Test URL parameter sanitization."""
        from test_that.plugins.security import SecuritySanitizer
        import urllib.parse
        
        sanitizer = SecuritySanitizer()
        url = "https://api.example.com/users?api_key=secret123&name=john&token=abc123"
        
        sanitized = sanitizer.sanitize_url(url)
        
        that(sanitized).contains("name=john")
        that(sanitized).does_not_contain("secret123")
        that(sanitized).does_not_contain("abc123")
        # Check for URL-encoded redacted text
        redacted_encoded = urllib.parse.quote("***REDACTED***")
        that(sanitized).contains(redacted_encoded)
    
    @test("body sanitization removes sensitive JSON fields")
    def test_body_sanitization():
        """Test request/response body sanitization."""
        from test_that.plugins.security import SecuritySanitizer
        
        sanitizer = SecuritySanitizer()
        body = '{"username": "john", "password": "secret123", "email": "john@example.com"}'
        
        sanitized = sanitizer.sanitize_body(body)
        
        that(sanitized).contains('"username": "john"')
        that(sanitized).does_not_contain('secret123')
        that(sanitized).contains('***REDACTED***')


with suite("Plugin Registry Thread Safety"):
    
    @test("concurrent plugin registration is thread-safe")
    def test_concurrent_registration():
        """Test that plugin registration is thread-safe."""
        from test_that.plugins.registry import PluginRegistry
        from test_that.plugins.base import PluginBase, PluginInfo
        
        # Create test plugins
        class TestPlugin1(PluginBase):
            @property
            def info(self):
                return PluginInfo(name="test1", version="1.0.0", description="Test 1")
        
        class TestPlugin2(PluginBase):
            @property
            def info(self):
                return PluginInfo(name="test2", version="1.0.0", description="Test 2")
        
        registry = PluginRegistry()
        errors = []
        
        def register_plugin(plugin_class):
            try:
                registry.register_plugin(plugin_class)
            except Exception as e:
                errors.append(e)
        
        # Register plugins concurrently
        threads = [
            threading.Thread(target=register_plugin, args=(TestPlugin1,)),
            threading.Thread(target=register_plugin, args=(TestPlugin2,))
        ]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have no errors and both plugins registered
        that(len(errors)).equals(0)
        that(len(registry._plugins)).equals(2)
        that(registry.get_plugin("test1")).is_not_none()
        that(registry.get_plugin("test2")).is_not_none()
    
    @test("lazy loading is thread-safe")
    def test_lazy_loading_thread_safety():
        """Test that lazy plugin loading is thread-safe."""
        from test_that.plugins.registry import PluginRegistry
        from test_that.plugins.base import PluginBase, PluginInfo
        
        class LazyTestPlugin(PluginBase):
            @property
            def info(self):
                return PluginInfo(name="lazy_test", version="1.0.0", description="Lazy Test")
        
        registry = PluginRegistry()
        registry.register_lazy_plugin("lazy_test", lambda: LazyTestPlugin)
        
        plugins = []
        errors = []
        
        def get_plugin():
            try:
                plugin = registry.get_plugin("lazy_test")
                plugins.append(plugin)
            except Exception as e:
                errors.append(e)
        
        # Try to load the same lazy plugin from multiple threads
        threads = [threading.Thread(target=get_plugin) for _ in range(3)]
        
        for thread in threads:
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Should have no errors and same plugin instance
        that(len(errors)).equals(0)
        that(len(plugins)).equals(3)
        that(all(p is plugins[0] for p in plugins)).is_true()


with suite("Configuration Caching"):
    
    @test("configuration is cached and reused")
    def test_config_caching():
        """Test that configuration caching improves performance."""
        from test_that.plugins.config import ConfigCache
        
        cache = ConfigCache()
        load_count = 0
        
        def expensive_loader():
            nonlocal load_count
            load_count += 1
            time.sleep(0.01)  # Simulate expensive operation
            return {"test": "value"}
        
        # First call should trigger load
        start_time = time.perf_counter()
        result1 = cache.get("test_key", expensive_loader)
        first_duration = time.perf_counter() - start_time
        
        # Second call should use cache
        start_time = time.perf_counter()
        result2 = cache.get("test_key", expensive_loader)
        second_duration = time.perf_counter() - start_time
        
        that(load_count).equals(1)  # Loader called only once
        that(result1).equals(result2)
        that(second_duration).is_less_than(first_duration)  # Cache is faster
    
    @test("cache invalidation works correctly")
    def test_cache_invalidation():
        """Test cache invalidation functionality."""
        from test_that.plugins.config import ConfigCache
        
        cache = ConfigCache()
        load_count = 0
        
        def counter_loader():
            nonlocal load_count
            load_count += 1
            return {"count": load_count}
        
        # Load initial value
        result1 = cache.get("counter", counter_loader)
        that(result1["count"]).equals(1)
        
        # Should get cached value
        result2 = cache.get("counter", counter_loader)
        that(result2["count"]).equals(1)
        
        # Invalidate and reload
        cache.invalidate("counter")
        result3 = cache.get("counter", counter_loader)
        that(result3["count"]).equals(2)


with suite("Plugin Validation"):
    
    @test("plugin conflict detection works")
    def test_plugin_conflict_detection():
        """Test that plugin conflicts are detected."""
        from test_that.plugins.registry import PluginRegistry
        from test_that.plugins.base import PluginBase, PluginInfo, PluginConflictError
        
        class ConflictPlugin(PluginBase):
            @property
            def info(self):
                return PluginInfo(name="conflict_test", version="1.0.0", description="Conflict Test")
        
        registry = PluginRegistry()
        registry._config = {'allow_plugin_override': False}
        
        # Register first plugin
        registry.register_plugin(ConflictPlugin)
        
        # Try to register conflicting plugin
        that(lambda: registry.register_plugin(ConflictPlugin)).raises(PluginConflictError)
    
    @test("plugin version compatibility is checked")
    def test_version_compatibility():
        """Test plugin version compatibility checking."""
        from test_that.plugins.registry import PluginRegistry
        from test_that.plugins.base import PluginBase, PluginInfo, PluginVersionError
        
        class IncompatiblePlugin(PluginBase):
            @property
            def info(self):
                return PluginInfo(
                    name="incompatible", 
                    version="1.0.0", 
                    description="Incompatible",
                    min_that_version="999.0.0"  # Future version
                )
        
        registry = PluginRegistry()
        
        # Should raise version error
        that(lambda: registry.register_plugin(IncompatiblePlugin)).raises(PluginVersionError)


with suite("Plugin CLI"):
    
    @test("plugin CLI is importable")
    def test_plugin_cli_import():
        """Test that plugin CLI can be imported."""
        from test_that.plugins.cli import PluginCLI
        
        cli = PluginCLI()
        that(cli).is_not_none()
        that(hasattr(cli, 'create_parser')).is_true()
    
    @test("plugin toolkit is functional")
    def test_plugin_toolkit():
        """Test plugin development toolkit."""
        from test_that.plugins.toolkit import PluginTemplate, PluginValidator
        
        template = PluginTemplate()
        validator = PluginValidator()
        
        that(template).is_not_none()
        that(validator).is_not_none()
        that(hasattr(template, 'create_plugin')).is_true()
        that(hasattr(validator, 'validate_plugin_file')).is_true()


with suite("Plugin Performance"):
    
    @test("plugin loading is fast")
    def test_plugin_loading_performance():
        """Test that plugin loading performance is acceptable."""
        from test_that.plugins.registry import PluginRegistry
        
        start_time = time.perf_counter()
        registry = PluginRegistry()
        registry.initialize()
        end_time = time.perf_counter()
        
        duration = end_time - start_time
        
        # Should load in reasonable time (less than 1 second)
        that(duration).is_less_than(1.0)
    
    @test("lazy loading improves startup time")
    def test_lazy_loading_benefit():
        """Test that lazy loading improves startup performance."""
        from test_that.plugins.registry import PluginRegistry
        from test_that.plugins.base import PluginBase, PluginInfo
        
        class SlowPlugin(PluginBase):
            @property
            def info(self):
                return PluginInfo(name="slow", version="1.0.0", description="Slow Plugin")
            
            def initialize(self, config):
                time.sleep(0.1)  # Simulate slow initialization
        
        # Test eager loading
        registry1 = PluginRegistry()
        start_time = time.perf_counter()
        registry1.register_plugin(SlowPlugin)
        eager_time = time.perf_counter() - start_time
        
        # Test lazy loading
        registry2 = PluginRegistry()
        start_time = time.perf_counter()
        registry2.register_lazy_plugin("slow", lambda: SlowPlugin)
        lazy_time = time.perf_counter() - start_time
        
        that(lazy_time).is_less_than(eager_time)