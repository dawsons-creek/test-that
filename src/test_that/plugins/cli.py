"""
Command line interface for plugin management.

Provides commands to list, enable, disable, and manage plugins.
"""

import argparse
import sys
from typing import Any, Dict, List

from .config import invalidate_config_cache, load_plugin_config
from .registry import plugin_registry


class PluginCLI:
    """Command line interface for plugin management."""

    def __init__(self):
        self.registry = plugin_registry

    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for plugin commands."""
        parser = argparse.ArgumentParser(
            description="That Plugin Manager", prog="that plugins"
        )

        subparsers = parser.add_subparsers(dest="command", help="Plugin commands")

        # List command
        list_parser = subparsers.add_parser("list", help="List all plugins")
        list_parser.add_argument(
            "--type",
            choices=["decorator", "assertion", "lifecycle", "lazy"],
            help="Filter by plugin type",
        )
        list_parser.add_argument(
            "--enabled", action="store_true", help="Show only enabled plugins"
        )
        list_parser.add_argument(
            "--stats", action="store_true", help="Show plugin statistics"
        )

        # Info command
        info_parser = subparsers.add_parser("info", help="Show plugin information")
        info_parser.add_argument("name", help="Plugin name")

        # Enable command
        enable_parser = subparsers.add_parser("enable", help="Enable a plugin")
        enable_parser.add_argument("name", help="Plugin name")

        # Disable command
        disable_parser = subparsers.add_parser("disable", help="Disable a plugin")
        disable_parser.add_argument("name", help="Plugin name")

        # Reload command
        reload_parser = subparsers.add_parser("reload", help="Reload plugin system")
        reload_parser.add_argument(
            "--force",
            action="store_true",
            help="Force reload even if already initialized",
        )

        # Status command
        subparsers.add_parser("status", help="Show plugin system status")

        # Doctor command
        subparsers.add_parser("doctor", help="Diagnose plugin issues")

        return parser

    def run(self, args: List[str] = None) -> int:
        """Run the plugin CLI with given arguments."""
        parser = self.create_parser()
        parsed_args = parser.parse_args(args)

        if not parsed_args.command:
            parser.print_help()
            return 1

        try:
            # Initialize plugin system if needed
            if parsed_args.command != "reload":
                self.registry.initialize()

            # Dispatch to command handler
            handler = getattr(self, f"_handle_{parsed_args.command}")
            return handler(parsed_args)

        except Exception as e:
            print(f"Error: {e}")
            return 1

    def _handle_list(self, args) -> int:
        """Handle the list command."""
        plugins = self.registry.list_plugins()

        if args.type:
            plugins = [p for p in plugins if args.type in p["type"]]

        if args.enabled:
            from .config import is_plugin_enabled

            plugins = [p for p in plugins if is_plugin_enabled(p["name"])]

        if not plugins:
            print("No plugins found")
            return 0

        if args.stats:
            self._print_plugin_stats()
            print()

        # Print plugins table
        self._print_plugins_table(plugins)
        return 0

    def _handle_info(self, args) -> int:
        """Handle the info command."""
        plugin = self.registry.get_plugin(args.name)
        if not plugin:
            print(f"Plugin '{args.name}' not found")
            return 1

        self._print_plugin_info(plugin)
        return 0

    def _handle_enable(self, args) -> int:
        """Handle the enable command."""
        return self._modify_plugin_config(args.name, enable=True)

    def _handle_disable(self, args) -> int:
        """Handle the disable command."""
        return self._modify_plugin_config(args.name, enable=False)

    def _handle_reload(self, args) -> int:
        """Handle the reload command."""
        print("Reloading plugin system...")

        # Clear caches
        invalidate_config_cache()

        # Cleanup and reinitialize
        self.registry.cleanup()
        self.registry.initialize(force=args.force)

        stats = self.registry.get_stats()
        print(f"Loaded {stats['total_plugins']} plugins")

        if stats["failed_plugins"] > 0:
            print(f"Warning: {stats['failed_plugins']} plugins failed to load")

        return 0

    def _handle_status(self, args) -> int:
        """Handle the status command."""
        stats = self.registry.get_stats()
        config = load_plugin_config()

        print("Plugin System Status")
        print("=" * 40)
        print(f"Initialized: {stats['initialized']}")
        print(f"Total Plugins: {stats['total_plugins']}")
        print(f"  - Decorator: {stats['decorator_plugins']}")
        print(f"  - Assertion: {stats['assertion_plugins']}")
        print(f"  - Lifecycle: {stats['lifecycle_plugins']}")
        print(f"  - Lazy: {stats['lazy_plugins']}")
        print(f"Failed Plugins: {stats['failed_plugins']}")
        print(f"Average Load Time: {stats['average_load_time']:.3f}s")
        print()
        print("Configuration:")
        print(f"  Auto Discover: {config.get('auto_discover', True)}")
        print(f"  Fail on Error: {config.get('fail_on_plugin_error', False)}")
        print(f"  Allow Override: {config.get('allow_plugin_override', False)}")

        return 0

    def _handle_doctor(self, args) -> int:
        """Handle the doctor command."""
        print("Plugin System Diagnostics")
        print("=" * 40)

        issues_found = 0

        # Check configuration
        try:
            load_plugin_config()
            print("✓ Configuration loaded successfully")
        except Exception as e:
            print(f"✗ Configuration error: {e}")
            issues_found += 1

        # Check plugin system initialization
        if self.registry._initialized:
            print("✓ Plugin system initialized")
        else:
            print("✗ Plugin system not initialized")
            issues_found += 1

        # Check for failed plugins
        stats = self.registry.get_stats()
        if stats["failed_plugins"] > 0:
            print(f"✗ {stats['failed_plugins']} plugins failed to load")
            issues_found += 1
        else:
            print("✓ All plugins loaded successfully")

        # Check plugin dependencies
        for plugin in self.registry._plugins.values():
            missing_deps = plugin.validate_dependencies()
            if missing_deps:
                print(
                    f"✗ Plugin '{plugin.info.name}' missing dependencies: {missing_deps}"
                )
                issues_found += 1

        if issues_found == 0:
            print("\n✓ No issues found")
        else:
            print(f"\n✗ Found {issues_found} issues")

        return 1 if issues_found > 0 else 0

    def _print_plugins_table(self, plugins: List[Dict[str, Any]]) -> None:
        """Print plugins in a formatted table."""
        if not plugins:
            return

        # Calculate column widths
        name_width = max(len(p["name"]) for p in plugins)
        version_width = max(len(p["version"]) for p in plugins)
        type_width = max(len(",".join(p["type"])) for p in plugins)

        # Minimum widths
        name_width = max(name_width, 8)
        version_width = max(version_width, 7)
        type_width = max(type_width, 8)

        # Print header
        header = f"{'Name':<{name_width}} {'Version':<{version_width}} {'Type':<{type_width}} {'Load Time':<10} Priority"
        print(header)
        print("-" * len(header))

        # Print plugins
        for plugin in sorted(plugins, key=lambda p: p["name"]):
            name = plugin["name"]
            version = plugin["version"]
            types = ",".join(plugin["type"])
            load_time = f"{plugin['load_time']:.3f}s"
            priority = str(plugin["priority"])

            print(
                f"{name:<{name_width}} {version:<{version_width}} {types:<{type_width}} {load_time:<10} {priority}"
            )

    def _print_plugin_info(self, plugin) -> None:
        """Print detailed plugin information."""
        info = plugin.info

        print(f"Plugin: {info.name}")
        print(f"Version: {info.version}")
        print(f"Description: {info.description}")
        print(f"Author: {info.author}")
        if info.url:
            print(f"URL: {info.url}")
        print(f"Priority: {info.priority}")

        if info.dependencies:
            print(f"Dependencies: {', '.join(info.dependencies)}")

        if info.optional_dependencies:
            print(f"Optional Dependencies: {', '.join(info.optional_dependencies)}")

        print(f"Version Range: {info.min_that_version} - {info.max_that_version}")

        # Show plugin types
        types = self.registry._get_plugin_types(plugin)
        print(f"Types: {', '.join(types)}")

        # Show load time if available
        load_time = self.registry._plugin_load_times.get(info.name)
        if load_time:
            print(f"Load Time: {load_time:.3f}s")

    def _print_plugin_stats(self) -> None:
        """Print plugin system statistics."""
        stats = self.registry.get_stats()
        print("Plugin Statistics:")
        print(f"  Total: {stats['total_plugins']}")
        print(f"  Decorator: {stats['decorator_plugins']}")
        print(f"  Assertion: {stats['assertion_plugins']}")
        print(f"  Lifecycle: {stats['lifecycle_plugins']}")
        print(f"  Lazy: {stats['lazy_plugins']}")
        print(f"  Failed: {stats['failed_plugins']}")
        print(f"  Total Load Time: {stats['total_load_time']:.3f}s")
        print(f"  Average Load Time: {stats['average_load_time']:.3f}s")

    def _modify_plugin_config(self, plugin_name: str, enable: bool) -> int:
        """Modify plugin configuration to enable/disable a plugin."""
        # This is a basic implementation - in a real system you'd want
        # to modify the pyproject.toml file directly

        action = "enable" if enable else "disable"
        print(f"To {action} plugin '{plugin_name}', add to pyproject.toml:")
        print()
        print("[tool.test_that.plugins]")

        if enable:
            print(f'enabled = ["{plugin_name}"]')
        else:
            print(f'disabled = ["{plugin_name}"]')

        print()
        print("Then run: that plugins reload")

        return 0


def main(args: List[str] = None) -> int:
    """Main entry point for plugin CLI."""
    cli = PluginCLI()
    return cli.run(args)


if __name__ == "__main__":
    sys.exit(main())
