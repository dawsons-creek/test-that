"""
Replay plugin implementation for the That testing library.
"""

from typing import Dict, Any, Callable, Union
from ..base import DecoratorPlugin, PluginInfo
from .time_freeze import TimeFreeze
from .http_recording import HTTPRecorder


class ReplayPlugin(DecoratorPlugin):
    """Plugin providing time freezing and HTTP recording capabilities."""

    @property
    def info(self) -> PluginInfo:
        return PluginInfo(
            name="replay",
            version="1.0.0",
            description="Time freezing and HTTP recording/replay for deterministic testing",
            dependencies=[],
            optional_dependencies=['pyyaml', 'requests']
        )

    def initialize(self, config: Dict[str, Any]) -> None:
        """Initialize the replay plugin with configuration."""
        self.recordings_dir = config.get('recordings_dir', 'tests/recordings')
        self.default_http_mode = config.get('default_http_mode', 'once')
        self.time_format = config.get('time_format', 'iso')
        self.http_timeout = config.get('http_timeout', 30)

    def get_decorators(self) -> Dict[str, Callable]:
        """Return available decorators from this plugin."""
        decorators = {
            'time': self._create_time_decorator,
        }
        
        # Only add HTTP decorator if dependencies are available
        try:
            import yaml
            import requests
            decorators['http'] = self._create_http_decorator
        except ImportError:
            pass
            
        return decorators

    def _create_time_decorator(self, frozen_time: Union[str, Any]):
        """Create time freeze decorator."""
        def decorator(func):
            freezer = TimeFreeze(frozen_time)
            return freezer.freeze_during(func)
        return decorator

    def _create_http_decorator(self, cassette_name: str, mode: str = None):
        """Create HTTP recording decorator."""
        def decorator(func):
            recorder = HTTPRecorder(
                cassette_name,
                record_mode=mode or self.default_http_mode,
                recordings_dir=self.recordings_dir
            )
            return recorder.record_during(func)
        return decorator
