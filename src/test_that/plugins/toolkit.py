"""
Plugin development toolkit for creating That plugins.

Provides templates, utilities, and validation tools for plugin development.
"""

from pathlib import Path
from textwrap import dedent
from typing import List


class PluginTemplate:
    """Template generator for different plugin types."""

    PLUGIN_TEMPLATES = {
        'decorator': '''"""
{description}

A decorator plugin for the That testing framework.
"""

from typing import Dict, Callable, Any
from test_that.plugins.base import DecoratorPlugin, PluginInfo


class {class_name}(DecoratorPlugin):
    """Decorator plugin: {description}"""

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="{name}",
            version="1.0.0",
            description="{description}",
            dependencies=[],
            optional_dependencies=[],
            author="{author}",
            url="",
            priority=100
        )

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration."""
        self.config = config

    def get_decorators(self) -> Dict[str, Callable]:
        """Return decorator functions."""
        return {{
            "{name}": self._create_{name}_decorator
        }}

    def _create_{name}_decorator(self, *args, **kwargs):
        """Create the {name} decorator."""
        def decorator(func):
            def wrapper(*test_args, **test_kwargs):
                # Add your decorator logic here
                # Before test execution
                try:
                    result = func(*test_args, **test_kwargs)
                    # After successful test execution
                    return result
                except Exception as e:
                    # Handle test failure
                    raise
                finally:
                    # Cleanup code
                    pass
            return wrapper
        return decorator
''',

        'assertion': '''"""
{description}

An assertion plugin for the That testing framework.
"""

from typing import Dict, Callable, Any
from test_that.plugins.base import AssertionPlugin, PluginInfo


class {class_name}(AssertionPlugin):
    """Assertion plugin: {description}"""

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="{name}",
            version="1.0.0",
            description="{description}",
            dependencies=[],
            optional_dependencies=[],
            author="{author}",
            url="",
            priority=100
        )

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration."""
        self.config = config

    def get_assertion_methods(self) -> Dict[str, Callable]:
        """Return assertion methods."""
        return {{
            "{name}_example": self._create_{name}_assertion
        }}

    def _create_{name}_assertion(self, assertion_instance):
        """Create assertion method for {name}."""
        def assertion_method(*args, **kwargs):
            # Add your assertion logic here
            value = assertion_instance.value

            # Example assertion logic
            if not self._validate_value(value, *args, **kwargs):
                from test_that.assertions import ThatAssertionError
                raise ThatAssertionError(
                    f"{{assertion_instance.expression}}.{name}_example(...)",
                    expected="expected condition",
                    actual=value
                )

            return assertion_instance

        return assertion_method

    def _validate_value(self, value: Any, *args, **kwargs) -> bool:
        """Validate the assertion condition."""
        # Implement your validation logic here
        return True
''',

        'lifecycle': '''"""
{description}

A lifecycle plugin for the That testing framework.
"""

from typing import Dict, Any
from test_that.plugins.base import LifecyclePlugin, PluginInfo


class {class_name}(LifecyclePlugin):
    """Lifecycle plugin: {description}"""

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="{name}",
            version="1.0.0",
            description="{description}",
            dependencies=[],
            optional_dependencies=[],
            author="{author}",
            url="",
            priority=100
        )

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize plugin with configuration."""
        self.config = config
        self.stats = {{
            'tests_run': 0,
            'suites_run': 0,
            'start_time': None,
            'end_time': None
        }}

    def before_test_run(self) -> None:
        """Called before all tests start."""
        import time
        self.stats['start_time'] = time.time()
        print(f"[{self.info.name}] Starting test run")

    def after_test_run(self) -> None:
        """Called after all tests complete."""
        import time
        self.stats['end_time'] = time.time()
        duration = self.stats['end_time'] - self.stats['start_time']
        print(f"[{self.info.name}] Test run completed in {{duration:.2f}}s")
        print(f"[{self.info.name}] Ran {{self.stats['tests_run']}} tests in {{self.stats['suites_run']}} suites")

    def before_test(self, test_name: str) -> None:
        """Called before each individual test."""
        print(f"[{self.info.name}] Starting test: {{test_name}}")

    def after_test(self, test_name: str, result: Any) -> None:
        """Called after each individual test."""
        self.stats['tests_run'] += 1
        status = "PASSED" if result.passed else "FAILED"
        print(f"[{self.info.name}] Test {{test_name}}: {{status}}")

    def before_suite(self, suite_name: str) -> None:
        """Called before each test suite."""
        print(f"[{self.info.name}] Starting suite: {{suite_name}}")

    def after_suite(self, suite_name: str) -> None:
        """Called after each test suite."""
        self.stats['suites_run'] += 1
        print(f"[{self.info.name}] Suite {{suite_name}} completed")

    def get_stats(self) -> Dict[str, Any]:
        """Get plugin statistics."""
        return self.stats.copy()
'''
    }

    def create_plugin(self, name: str, plugin_type: str, description: str = "",
                     author: str = "Unknown", output_dir: str = ".") -> Path:
        """Create a new plugin from template."""
        if plugin_type not in self.PLUGIN_TEMPLATES:
            raise ValueError(f"Unknown plugin type: {plugin_type}")

        if not description:
            description = f"A {plugin_type} plugin for That"

        # Create class name
        class_name = self._to_class_name(name)

        # Generate plugin code
        template = self.PLUGIN_TEMPLATES[plugin_type]
        code = template.format(
            name=name,
            class_name=class_name,
            description=description,
            author=author
        )

        # Create output file
        output_path = Path(output_dir) / f"{name}_plugin.py"
        with open(output_path, 'w') as f:
            f.write(dedent(code).strip())

        # Create test file
        test_path = self._create_test_file(name, plugin_type, class_name, output_dir)

        # Create configuration example
        config_path = self._create_config_example(name, plugin_type, output_dir)

        print("Created plugin files:")
        print(f"  Plugin: {output_path}")
        print(f"  Test: {test_path}")
        print(f"  Config: {config_path}")

        return output_path

    def _to_class_name(self, name: str) -> str:
        """Convert plugin name to class name."""
        return ''.join(word.capitalize() for word in name.replace('-', '_').split('_')) + 'Plugin'

    def _create_test_file(self, name: str, plugin_type: str, class_name: str, output_dir: str) -> Path:
        """Create a test file for the plugin."""
        test_template = f'''"""
Tests for the {name} plugin.
"""

from test_that import test, suite, that
from {name}_plugin import {class_name}


with suite("{class_name} Tests"):

    @test("plugin info is valid")
    def test_plugin_info():
        plugin = {class_name}()
        info = plugin.info

        that(info.name).equals("{name}")
        that(info.version).is_not_none()
        that(info.description).is_not_none()

    @test("plugin initializes without error")
    def test_plugin_initialization():
        plugin = {class_name}()

        # Should not raise an exception
        that(lambda: plugin.initialize({{}})).does_not_raise()

    @test("plugin cleanup works")
    def test_plugin_cleanup():
        plugin = {class_name}()
        plugin.initialize({{}})

        # Should not raise an exception
        that(lambda: plugin.cleanup()).does_not_raise()
'''

        if plugin_type == 'decorator':
            test_template += f'''
    @test("decorator is available")
    def test_decorator_available():
        plugin = {class_name}()
        decorators = plugin.get_decorators()

        that(decorators).has_key("{name}")
        that(decorators["{name}"]).is_not_none()
'''

        elif plugin_type == 'assertion':
            test_template += f'''
    @test("assertion methods are available")
    def test_assertion_methods():
        plugin = {class_name}()
        methods = plugin.get_assertion_methods()

        that(len(methods)).is_greater_than(0)
'''

        elif plugin_type == 'lifecycle':
            test_template += f'''
    @test("lifecycle hooks are callable")
    def test_lifecycle_hooks():
        plugin = {class_name}()
        plugin.initialize({{}})

        # Test lifecycle methods don't raise exceptions
        that(lambda: plugin.before_test_run()).does_not_raise()
        that(lambda: plugin.before_test("test")).does_not_raise()
        that(lambda: plugin.after_test("test", None)).does_not_raise()
        that(lambda: plugin.after_test_run()).does_not_raise()
'''

        test_path = Path(output_dir) / f"test_{name}_plugin.py"
        with open(test_path, 'w') as f:
            f.write(dedent(test_template).strip())

        return test_path

    def _create_config_example(self, name: str, plugin_type: str, output_dir: str) -> Path:
        """Create a configuration example file."""
        config_template = f'''# Configuration example for {name} plugin
# Add to your pyproject.toml file

[tool.test_that.plugins]
enabled = ["{name}"]

[tool.test_that.plugins.{name}]
# Plugin-specific configuration options
# enabled = true
# option1 = "value1"
# option2 = 42
'''

        config_path = Path(output_dir) / f"{name}_plugin_config.toml"
        with open(config_path, 'w') as f:
            f.write(config_template)

        return config_path


class PluginValidator:
    """Validates plugin implementations for common issues."""

    def validate_plugin_file(self, file_path: Path) -> List[str]:
        """Validate a plugin file and return list of issues."""
        issues = []

        if not file_path.exists():
            return [f"Plugin file does not exist: {file_path}"]

        try:
            with open(file_path) as f:
                content = f.read()
        except Exception as e:
            return [f"Could not read plugin file: {e}"]

        # Check for required imports
        if 'from test_that.plugins.base import' not in content:
            issues.append("Missing import from test_that.plugins.base")

        # Check for plugin class
        if 'Plugin(' not in content:
            issues.append("No plugin class found (should inherit from PluginBase)")

        # Check for info property
        if '@property' not in content or 'def info(' not in content:
            issues.append("Missing info property")

        # Check for PluginInfo
        if 'PluginInfo(' not in content:
            issues.append("Missing PluginInfo instance")

        # Try to import and validate
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("test_plugin", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Look for plugin class
                plugin_class = None
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and
                        hasattr(attr, 'info') and
                        attr.__name__.endswith('Plugin')):
                        plugin_class = attr
                        break

                if plugin_class:
                    issues.extend(self._validate_plugin_class(plugin_class))
                else:
                    issues.append("No valid plugin class found in file")

        except Exception as e:
            issues.append(f"Plugin import/validation failed: {e}")

        return issues

    def _validate_plugin_class(self, plugin_class) -> List[str]:
        """Validate a plugin class."""
        issues = []

        try:
            plugin = plugin_class()

            # Validate info
            if hasattr(plugin, 'info'):
                info = plugin.info
                if not info.name:
                    issues.append("Plugin name is empty")
                if not info.version:
                    issues.append("Plugin version is empty")
                if not info.description:
                    issues.append("Plugin description is empty")
            else:
                issues.append("Plugin missing info property")

            # Test initialization
            try:
                plugin.initialize({})
            except Exception as e:
                issues.append(f"Plugin initialization failed: {e}")

            # Test cleanup
            try:
                plugin.cleanup()
            except Exception as e:
                issues.append(f"Plugin cleanup failed: {e}")

        except Exception as e:
            issues.append(f"Could not instantiate plugin: {e}")

        return issues


def create_plugin_cli() -> int:
    """CLI for creating plugins."""
    import argparse

    parser = argparse.ArgumentParser(description="Create a new That plugin")
    parser.add_argument('name', help='Plugin name (e.g., my_plugin)')
    parser.add_argument('type', choices=['decorator', 'assertion', 'lifecycle'],
                       help='Plugin type')
    parser.add_argument('--description', help='Plugin description')
    parser.add_argument('--author', default='Unknown', help='Plugin author')
    parser.add_argument('--output-dir', default='.', help='Output directory')

    args = parser.parse_args()

    template = PluginTemplate()
    try:
        output_path = template.create_plugin(
            args.name, args.type, args.description or f"A {args.type} plugin",
            args.author, args.output_dir
        )
        print("\nPlugin created successfully!")
        print("\nNext steps:")
        print(f"1. Edit {output_path} to implement your plugin logic")
        print(f"2. Run tests: that test_{args.name}_plugin.py")
        print("3. Add configuration to pyproject.toml")
        print("4. Install and enable your plugin")
        return 0
    except Exception as e:
        print(f"Error creating plugin: {e}")
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(create_plugin_cli())
