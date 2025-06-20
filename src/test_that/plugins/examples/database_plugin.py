"""
Example database plugin showing decorator and lifecycle functionality.

This plugin provides database transaction management and connection pooling
for tests that need database access.
"""

from contextlib import contextmanager
from typing import Any, Callable, Dict

from test_that.plugins.base import DecoratorPlugin, LifecyclePlugin, PluginInfo


class DatabasePlugin(DecoratorPlugin, LifecyclePlugin):
    """Example plugin providing database transaction management."""

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="database",
            version="1.0.0",
            description="Database transaction management for tests",
            dependencies=[],
            optional_dependencies=["sqlalchemy", "psycopg2"],
            author="That Framework",
            url="https://github.com/that-framework/database-plugin",
            priority=50  # High priority for setup/teardown
        )

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration."""
        self.config = config
        self.connection_url = config.get('connection_url', 'sqlite:///:memory:')
        self.auto_rollback = config.get('auto_rollback', True)
        self.pool_size = config.get('pool_size', 5)
        self.stats = {
            'transactions_created': 0,
            'rollbacks_performed': 0,
            'connections_opened': 0
        }

    def get_decorators(self) -> Dict[str, Callable]:
        """Return database decorators."""
        return {
            "transaction": self._create_transaction_decorator,
            "database": self._create_database_decorator
        }

    def _create_transaction_decorator(self, rollback: bool = None):
        """Create database transaction decorator."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Use config default if not specified
                should_rollback = rollback if rollback is not None else self.auto_rollback

                with self._database_transaction(should_rollback):
                    return func(*args, **kwargs)
            return wrapper
        return decorator

    def _create_database_decorator(self, connection_name: str = "default"):
        """Create database connection decorator."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                with self._database_connection(connection_name) as conn:
                    # Inject connection as first argument
                    return func(conn, *args, **kwargs)
            return wrapper
        return decorator

    @contextmanager
    def _database_transaction(self, rollback: bool = True):
        """Context manager for database transactions."""
        self.stats['transactions_created'] += 1
        print(f"[Database] Starting transaction (rollback={rollback})")

        try:
            # Simulate transaction start
            yield
            if rollback:
                print("[Database] Rolling back transaction")
                self.stats['rollbacks_performed'] += 1
            else:
                print("[Database] Committing transaction")
        except Exception as e:
            print(f"[Database] Transaction failed, rolling back: {e}")
            self.stats['rollbacks_performed'] += 1
            raise

    @contextmanager
    def _database_connection(self, name: str):
        """Context manager for database connections."""
        self.stats['connections_opened'] += 1
        print(f"[Database] Opening connection: {name}")

        try:
            # Simulate connection object
            connection = MockConnection(name, self.connection_url)
            yield connection
        finally:
            print(f"[Database] Closing connection: {name}")

    # Lifecycle hooks
    def before_test_run(self) -> None:
        """Initialize database connections before tests."""
        print("[Database] Initializing database connections")

    def after_test_run(self) -> None:
        """Cleanup database connections after tests."""
        print("[Database] Cleaning up database connections")
        print(f"[Database] Stats: {self.stats}")

    def before_suite(self, suite_name: str) -> None:
        """Setup suite-level database state."""
        print(f"[Database] Setting up database for suite: {suite_name}")

    def after_suite(self, suite_name: str) -> None:
        """Cleanup suite-level database state."""
        print(f"[Database] Cleaning up database for suite: {suite_name}")


class MockConnection:
    """Mock database connection for demonstration."""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url
        self.closed = False

    def execute(self, query: str, params=None):
        """Execute a query."""
        print(f"[DB:{self.name}] Executing: {query}")
        return MockResult()

    def close(self):
        """Close the connection."""
        self.closed = True


class MockResult:
    """Mock query result."""

    def fetchall(self):
        return [{"id": 1, "name": "test"}]

    def fetchone(self):
        return {"id": 1, "name": "test"}
