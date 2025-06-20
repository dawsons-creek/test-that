"""
Test the plugin system implementation.
"""

import datetime
from that import test, suite, that, replay


with suite("Plugin System"):
    
    @test("plugin system loads successfully")
    def test_plugin_system():
        """Test that the plugin system initializes without errors."""
        from that.plugins.registry import plugin_registry
        
        # Plugin registry should be initialized
        that(plugin_registry._initialized).is_true()
        
        # Should have at least the replay plugin
        that(len(plugin_registry._plugins)).is_greater_than(0)

    @test("replay plugin is available")
    def test_replay_plugin_available():
        """Test that the replay plugin is loaded and available."""
        from that.plugins.registry import plugin_registry
        
        # Should have replay plugin
        replay_plugin = plugin_registry.get_plugin("replay")
        that(replay_plugin).is_not_none()
        that(replay_plugin.info.name).equals("replay")

    @test("replay decorators are available")
    def test_replay_decorators():
        """Test that replay decorators are available."""
        from that.plugins.registry import plugin_registry
        
        decorators = plugin_registry.get_decorators()
        that(decorators).has_key("time")
        
        # HTTP decorator might not be available if dependencies are missing
        # but that's okay for this test

    @test("replay API is importable")
    def test_replay_api_import():
        """Test that the replay API can be imported."""
        # replay should be available since we imported it at the top
        that(replay).is_not_none()


with suite("Replay Plugin Functionality"):
    
    @test("time freezing works with plugin")
    @replay.time("2024-01-01T12:00:00Z")
    def test_time_freezing():
        """Test that time is frozen at the specified moment."""
        current_time = datetime.datetime.now()
        expected = datetime.datetime(2024, 1, 1, 12, 0, 0, tzinfo=datetime.timezone.utc)
        that(current_time).equals(expected)

    @test("time context manager works")
    def test_time_context_manager():
        """Test time freezing as context manager."""
        with replay.time("2024-06-15T09:30:00Z"):
            current_time = datetime.datetime.now()
            expected = datetime.datetime(2024, 6, 15, 9, 30, 0, tzinfo=datetime.timezone.utc)
            that(current_time).equals(expected)

    @test("combined replay decorator works")
    @replay(time="2024-12-25T00:00:00Z")
    def test_combined_replay():
        """Test combined replay functionality."""
        current_time = datetime.datetime.now()
        expected = datetime.datetime(2024, 12, 25, 0, 0, 0, tzinfo=datetime.timezone.utc)
        that(current_time).equals(expected)

    @test("replay without time works")
    def test_replay_without_time():
        """Test that replay decorator works without time parameter."""
        @replay()
        def dummy_test():
            return "success"
        
        result = dummy_test()
        that(result).equals("success")

    @test("invalid time format raises error")
    def test_invalid_time_format():
        """Test that invalid time formats raise appropriate errors."""
        def create_invalid_time():
            with replay.time("not-a-valid-date"):
                pass
        
        that(create_invalid_time).raises(ValueError)
