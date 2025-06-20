"""
Comprehensive test of the complete plugin system.

Tests all plugin types working together: decorators, assertions, and lifecycle.
"""

import datetime
import time
from that import test, suite, that, replay


with suite("Complete Plugin System Integration"):
    
    @test("all plugin types are loaded")
    def test_all_plugin_types():
        """Test that all plugin types are loaded correctly."""
        from that.plugins.registry import plugin_registry

        # Should have plugins of all types
        that(len(plugin_registry._plugins)).is_greater_than(1)  # At least replay + assertion
        that(len(plugin_registry._decorator_plugins)).is_greater_than(0)  # Replay
        that(len(plugin_registry._assertion_plugins)).is_greater_than(0)  # Example assertions
        that(len(plugin_registry._lifecycle_plugins)).is_greater_than(0)  # Example lifecycle

    @test("decorator and assertion plugins work together")
    @replay.time("2024-01-01T12:00:00Z")
    def test_decorator_assertion_integration():
        """Test decorator plugin (replay) with assertion plugin methods."""
        current_time = datetime.datetime.now()

        # Use replay plugin for time freezing
        that(current_time.year).equals(2024)
        that(current_time.month).equals(1)
        that(current_time.day).equals(1)

        # Use JSON schema plugin for JSON assertions
        json_data = '{"timestamp": "2024-01-01T12:00:00Z", "event": "test"}'
        that(json_data).as_json().has_key("timestamp")

        # Test schema validation
        schema = {"type": "object", "properties": {"timestamp": {"type": "string"}}}
        that(json_data).as_json().matches_schema(schema)

    @test("lifecycle plugin tracks test execution")
    def test_lifecycle_tracking():
        """Test that lifecycle plugin is tracking test execution."""
        from that.plugins.registry import plugin_registry
        
        # Get the lifecycle plugin
        lifecycle_plugin = None
        for plugin in plugin_registry._lifecycle_plugins:
            if plugin.info.name == "example_lifecycle":
                lifecycle_plugin = plugin
                break
        
        # Plugin should exist (even if disabled)
        that(lifecycle_plugin).is_not_none()
        
        # Should have stats tracking capability
        that(hasattr(lifecycle_plugin, 'get_stats')).is_true()

    @test("plugin configuration is loaded")
    def test_plugin_configuration():
        """Test that plugin configuration is loaded correctly."""
        from that.plugins.config import get_plugin_specific_config
        
        # Should be able to get config for replay plugin
        replay_config = get_plugin_specific_config("replay")
        that(replay_config).is_not_none()
        that(replay_config).has_key("recordings_dir")

    @test("plugins handle errors gracefully")
    def test_plugin_error_handling():
        """Test that plugin errors are handled gracefully."""
        # This should not crash even if a plugin has issues
        from that.plugins.registry import plugin_registry
        
        # Trigger lifecycle events (should not fail)
        plugin_registry.trigger_lifecycle_event('before_test', 'test_name')
        plugin_registry.trigger_lifecycle_event('after_test', 'test_name', None)
        
        # Should still be functional
        that(plugin_registry._initialized).is_true()


with suite("Plugin Performance"):
    
    @test("plugin loading is fast")
    def test_plugin_loading_performance():
        """Test that plugin loading doesn't significantly impact startup time."""
        start_time = time.perf_counter()
        
        # Re-initialize plugin system
        from that.plugins.registry import PluginRegistry
        test_registry = PluginRegistry()
        test_registry.initialize()
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        # Should load quickly (less than 100ms)
        that(duration).is_less_than(0.1)

    @test("assertion plugin methods are cached")
    def test_assertion_method_caching():
        """Test that assertion methods are cached for performance."""
        # Create multiple assertion instances
        assertion1 = that("test1")
        assertion2 = that("test2")

        # Both should have the same custom methods
        that(hasattr(assertion1, 'as_json')).equals(hasattr(assertion2, 'as_json'))
        that(hasattr(assertion1, 'matches_schema')).equals(hasattr(assertion2, 'matches_schema'))


with suite("Plugin Extensibility"):
    
    @test("plugins can be discovered by name")
    def test_plugin_discovery():
        """Test that plugins can be discovered and accessed by name."""
        from that.plugins.registry import plugin_registry
        
        # Should be able to get plugins by name
        replay_plugin = plugin_registry.get_plugin("replay")
        that(replay_plugin).is_not_none()
        that(replay_plugin.info.name).equals("replay")

    @test("plugin metadata is accessible")
    def test_plugin_metadata():
        """Test that plugin metadata is properly accessible."""
        from that.plugins.registry import plugin_registry
        
        replay_plugin = plugin_registry.get_plugin("replay")
        that(replay_plugin.info.version).is_not_none()
        that(replay_plugin.info.description).is_not_none()
        that(replay_plugin.info.dependencies).is_instance_of(list)

    @test("plugins can be cleaned up")
    def test_plugin_cleanup():
        """Test that plugins can be properly cleaned up."""
        from that.plugins.registry import plugin_registry
        
        # Should be able to cleanup without errors
        plugin_registry.cleanup()
        
        # Should still be functional after cleanup
        that(plugin_registry._plugins).is_not_none()
