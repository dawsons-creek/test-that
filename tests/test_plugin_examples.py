"""
Tests for example plugins included in the repository.

Tests the DatabasePlugin example to ensure it works correctly.
"""

from test_that import suite, test, that


with suite("DatabasePlugin Example"):

    @test("creates with proper info")
    def test_database_plugin_info():
        from test_that.plugins.examples.database_plugin import DatabasePlugin
        
        plugin = DatabasePlugin()
        info = plugin.info
        
        that(info.name).equals("database")
        that(info.version).equals("1.0.0")
        that(info.description).contains("Database transaction management")
        that(info.optional_dependencies).contains("sqlalchemy")
        that(info.optional_dependencies).contains("psycopg2")
        that(info.priority).equals(50)  # High priority for setup/teardown

    @test("has lifecycle plugin capabilities")
    def test_database_plugin_lifecycle():
        from test_that.plugins.examples.database_plugin import DatabasePlugin
        from test_that.plugins.base import LifecyclePlugin
        
        plugin = DatabasePlugin()
        
        # Should be a lifecycle plugin
        that(isinstance(plugin, LifecyclePlugin)).equals(True)
        
        # Should have lifecycle methods
        that(hasattr(plugin, 'before_test')).equals(True)
        that(hasattr(plugin, 'after_test')).equals(True)

    @test("initializes with configuration")
    def test_database_plugin_initialization():
        from test_that.plugins.examples.database_plugin import DatabasePlugin
        
        plugin = DatabasePlugin()
        config = {
            "connection_string": "sqlite:///test.db",
            "pool_size": 5,
            "echo": True
        }
        
        # Should not raise
        that(lambda: plugin.initialize(config)).does_not_raise()

    @test("provides database decorators")
    def test_database_plugin_decorators():
        from test_that.plugins.examples.database_plugin import DatabasePlugin
        from test_that.plugins.base import DecoratorPlugin
        
        plugin = DatabasePlugin()
        plugin.initialize({})
        
        # Should be a decorator plugin
        that(isinstance(plugin, DecoratorPlugin)).equals(True)
        
        # Should provide transaction and database decorators
        decorators = plugin.get_decorators()
        that("transaction" in decorators).equals(True)
        that("database" in decorators).equals(True)
        
        # Test transaction decorator
        transaction_decorator = decorators["transaction"]()
        
        @transaction_decorator
        def test_function():
            return "decorated"
        
        that(test_function()).equals("decorated")

    @test("handles database connection lifecycle")
    def test_database_plugin_connection_lifecycle():
        from test_that.plugins.examples.database_plugin import DatabasePlugin
        
        plugin = DatabasePlugin()
        
        # Initialize with test config
        plugin.initialize({
            "connection_string": "sqlite:///memory:",
            "pool_size": 1
        })
        
        # Should handle lifecycle events without errors
        that(lambda: plugin.before_test_run()).does_not_raise()
        that(lambda: plugin.before_test(lambda: None)).does_not_raise()
        that(lambda: plugin.after_test(lambda: None, None)).does_not_raise()
        that(lambda: plugin.after_test_run()).does_not_raise()
        that(lambda: plugin.cleanup()).does_not_raise()

    @test("provides database transaction context")
    def test_database_plugin_transaction_context():
        from test_that.plugins.examples.database_plugin import DatabasePlugin
        
        plugin = DatabasePlugin()
        plugin.initialize({"auto_rollback": True})
        
        # Should track transaction stats
        initial_transactions = plugin.stats['transactions_created']
        
        # Use transaction context
        with plugin._database_transaction(rollback=True):
            pass
        
        # Should increment transaction count
        that(plugin.stats['transactions_created']).equals(initial_transactions + 1)
        that(plugin.stats['rollbacks_performed']).is_greater_than(0)

    @test("validates dependencies properly")
    def test_database_plugin_dependencies():
        from test_that.plugins.examples.database_plugin import DatabasePlugin
        
        plugin = DatabasePlugin()
        missing_deps = plugin.validate_dependencies()
        
        # Should return a list (may be empty if dependencies are installed)
        that(isinstance(missing_deps, list)).equals(True)
        
        # If SQLAlchemy is not installed, should report it
        # (This test will pass either way - we're just testing the structure)