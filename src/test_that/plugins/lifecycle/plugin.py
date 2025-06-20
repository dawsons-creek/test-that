"""
Example lifecycle plugin to demonstrate test execution hooks.

This plugin shows how to hook into various points in the test lifecycle
for logging, metrics collection, or other cross-cutting concerns.
"""

from typing import Dict, Any
from ..base import LifecyclePlugin, PluginInfo


class ExampleLifecyclePlugin(LifecyclePlugin):
    """Example plugin that demonstrates lifecycle hooks."""

    def __init__(self):
        self.test_count = 0
        self.suite_count = 0
        self.failed_tests = []
        self.slow_tests = []
        self.enabled = False

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="lifecycle",
            version="1.0.0",
            description="Test execution lifecycle hooks and metrics collection",
            dependencies=[],
            optional_dependencies=[]
        )

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the lifecycle plugin with configuration."""
        self.enabled = config.get('enabled', False)
        self.slow_threshold = config.get('slow_threshold', 0.1)  # 100ms
        self.verbose = config.get('verbose', False)
        
        if self.enabled and self.verbose:
            print("🔌 Example lifecycle plugin initialized")

    def before_test_run(self) -> None:
        """Called before all tests start running."""
        if not self.enabled:
            return
            
        self.test_count = 0
        self.suite_count = 0
        self.failed_tests = []
        self.slow_tests = []
        
        if self.verbose:
            print("🚀 Starting test run...")

    def after_test_run(self) -> None:
        """Called after all tests finish running."""
        if not self.enabled:
            return
            
        if self.verbose:
            print("✅ Test run completed!")
            print(f"   📊 Total tests: {self.test_count}")
            print(f"   📦 Total suites: {self.suite_count}")
            
            if self.failed_tests:
                print(f"   ❌ Failed tests: {len(self.failed_tests)}")
                for test_name in self.failed_tests:
                    print(f"      - {test_name}")
            
            if self.slow_tests:
                print(f"   🐌 Slow tests (>{self.slow_threshold}s):")
                for test_name, duration in self.slow_tests:
                    print(f"      - {test_name}: {duration:.3f}s")

    def before_test(self, test_name: str) -> None:
        """Called before each individual test."""
        if not self.enabled:
            return
            
        self.test_count += 1
        
        if self.verbose:
            print(f"🧪 Running test: {test_name}")

    def after_test(self, test_name: str, result: Any) -> None:
        """Called after each individual test."""
        if not self.enabled:
            return
            
        # Check if test failed
        if hasattr(result, 'passed') and not result.passed:
            self.failed_tests.append(test_name)
            if self.verbose:
                print(f"❌ Test failed: {test_name}")
        
        # Check if test was slow
        if hasattr(result, 'duration') and result.duration > self.slow_threshold:
            self.slow_tests.append((test_name, result.duration))
            if self.verbose:
                print(f"🐌 Slow test detected: {test_name} ({result.duration:.3f}s)")

    def before_suite(self, suite_name: str) -> None:
        """Called before each test suite."""
        if not self.enabled:
            return
            
        self.suite_count += 1
        
        if self.verbose:
            print(f"📦 Starting suite: {suite_name}")

    def after_suite(self, suite_name: str) -> None:
        """Called after each test suite."""
        if not self.enabled:
            return
            
        if self.verbose:
            print(f"✅ Completed suite: {suite_name}")

    def get_stats(self) -> Dict[str, Any]:
        """Get collected statistics (useful for other plugins or tools)."""
        return {
            'test_count': self.test_count,
            'suite_count': self.suite_count,
            'failed_count': len(self.failed_tests),
            'slow_count': len(self.slow_tests),
            'failed_tests': self.failed_tests.copy(),
            'slow_tests': self.slow_tests.copy(),
        }
