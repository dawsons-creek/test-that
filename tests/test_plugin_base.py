"""
Tests for plugin base classes and interfaces.

Tests PluginInfo, PluginBase, and all plugin type interfaces.
"""

from test_that import suite, test, that
from test_that.plugins.base import (
    AssertionPlugin, DecoratorPlugin, LifecyclePlugin, PluginBase, PluginInfo,
    PluginError, PluginConflictError, PluginDependencyError, PluginVersionError
)


with suite("PluginInfo"):

    @test("creates with required fields")
    def test_plugin_info_creation():
        info = PluginInfo(
            name="test-plugin",
            version="1.0.0", 
            description="Test plugin"
        )
        
        that(info.name).equals("test-plugin")
        that(info.version).equals("1.0.0")
        that(info.description).equals("Test plugin")
        that(info.dependencies).equals([])
        that(info.priority).equals(100)

    @test("supports optional fields")
    def test_plugin_info_optional_fields():
        info = PluginInfo(
            name="advanced-plugin",
            version="2.1.0",
            description="Advanced plugin",
            dependencies=["requests"],
            optional_dependencies=["sqlalchemy"],
            min_that_version="0.2.0",
            max_that_version="1.0.0",
            author="Test Author",
            url="https://example.com",
            priority=50
        )
        
        that(info.dependencies).equals(["requests"])
        that(info.optional_dependencies).equals(["sqlalchemy"])
        that(info.min_that_version).equals("0.2.0")
        that(info.max_that_version).equals("1.0.0")
        that(info.author).equals("Test Author")
        that(info.url).equals("https://example.com")
        that(info.priority).equals(50)


with suite("PluginBase"):

    @test("requires info property implementation")
    def test_plugin_base_abstract():
        that(lambda: PluginBase()).raises(TypeError)

    @test("has default lifecycle methods")
    def test_plugin_base_lifecycle():
        class TestPlugin(PluginBase):
            @property
            def info(self):
                return PluginInfo(name="test", version="1.0.0", description="Test")
        
        plugin = TestPlugin()
        
        # Should not raise - these have default implementations
        that(lambda: plugin.initialize({})).does_not_raise()
        that(lambda: plugin.cleanup()).does_not_raise()
        
        # validate_dependencies should return empty list by default
        that(plugin.validate_dependencies()).equals([])


with suite("DecoratorPlugin"):

    @test("requires get_decorators implementation")
    def test_decorator_plugin_abstract():
        class BadDecoratorPlugin(DecoratorPlugin):
            @property
            def info(self):
                return PluginInfo(name="bad", version="1.0.0", description="Bad")
        
        that(lambda: BadDecoratorPlugin()).raises(TypeError)

    @test("works with proper implementation")
    def test_decorator_plugin_implementation():
        class GoodDecoratorPlugin(DecoratorPlugin):
            @property
            def info(self):
                return PluginInfo(name="good", version="1.0.0", description="Good")
            
            def get_decorators(self):
                def test_decorator(func):
                    func._decorated = True
                    return func
                return {"test_decorator": test_decorator}
        
        plugin = GoodDecoratorPlugin()
        decorators = plugin.get_decorators()
        
        that("test_decorator" in decorators).equals(True)
        
        test_decorator = decorators["test_decorator"]
        
        @test_decorator
        def test_func():
            pass
        
        that(hasattr(test_func, '_decorated')).equals(True)


with suite("AssertionPlugin"):

    @test("requires get_assertion_methods implementation")
    def test_assertion_plugin_abstract():
        class BadAssertionPlugin(AssertionPlugin):
            @property
            def info(self):
                return PluginInfo(name="bad", version="1.0.0", description="Bad")
        
        that(lambda: BadAssertionPlugin()).raises(TypeError)

    @test("works with proper implementation")
    def test_assertion_plugin_implementation():
        class GoodAssertionPlugin(AssertionPlugin):
            @property
            def info(self):
                return PluginInfo(name="good", version="1.0.0", description="Good")
            
            def get_assertion_methods(self):
                def is_positive(value):
                    return value > 0
                
                return {"is_positive": is_positive}
        
        plugin = GoodAssertionPlugin()
        methods = plugin.get_assertion_methods()
        
        that("is_positive" in methods).equals(True)
        that(methods["is_positive"](5)).equals(True)
        that(methods["is_positive"](-1)).equals(False)


with suite("LifecyclePlugin"):

    @test("has default sync lifecycle methods")
    def test_lifecycle_plugin_sync_defaults():
        class TestLifecyclePlugin(LifecyclePlugin):
            @property
            def info(self):
                return PluginInfo(name="test", version="1.0.0", description="Test")
        
        plugin = TestLifecyclePlugin()
        
        # All should have default implementations that don't raise
        that(lambda: plugin.before_test_run()).does_not_raise()
        that(lambda: plugin.after_test_run()).does_not_raise()
        that(lambda: plugin.before_test("test_name")).does_not_raise()
        that(lambda: plugin.after_test("test_name", None)).does_not_raise()
        that(lambda: plugin.before_suite("test")).does_not_raise()
        that(lambda: plugin.after_suite("test")).does_not_raise()

    @test("has default async lifecycle methods")
    def test_lifecycle_plugin_async_defaults():
        import asyncio
        
        class TestLifecyclePlugin(LifecyclePlugin):
            @property
            def info(self):
                return PluginInfo(name="test", version="1.0.0", description="Test")
        
        plugin = TestLifecyclePlugin()
        
        # Test that async methods exist and are coroutines
        that(hasattr(plugin, 'before_test_run_async')).equals(True)
        that(hasattr(plugin, 'after_test_run_async')).equals(True)
        that(hasattr(plugin, 'before_test_async')).equals(True)
        that(hasattr(plugin, 'after_test_async')).equals(True)
        that(hasattr(plugin, 'before_suite_async')).equals(True)
        that(hasattr(plugin, 'after_suite_async')).equals(True)


with suite("Plugin Exceptions"):

    @test("PluginError is base exception")
    def test_plugin_error():
        error = PluginError("Test error")
        that(str(error)).equals("Test error")
        that(isinstance(error, Exception)).equals(True)

    @test("PluginConflictError inherits from PluginError")
    def test_plugin_conflict_error():
        error = PluginConflictError("Plugin conflict")
        that(str(error)).equals("Plugin conflict")
        that(isinstance(error, PluginError)).equals(True)

    @test("PluginDependencyError inherits from PluginError")
    def test_plugin_dependency_error():
        error = PluginDependencyError("Missing dependency")
        that(str(error)).equals("Missing dependency")
        that(isinstance(error, PluginError)).equals(True)

    @test("PluginVersionError inherits from PluginError")
    def test_plugin_version_error():
        error = PluginVersionError("Version mismatch")
        that(str(error)).equals("Version mismatch")
        that(isinstance(error, PluginError)).equals(True)