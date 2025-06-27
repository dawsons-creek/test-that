"""
HTTP recording functionality for deterministic testing.

Records HTTP requests and responses to YAML files for replay in tests.
Includes security sanitization to prevent credential leakage.
"""

import base64
import functools
import json
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import MagicMock, patch

import yaml

try:
    from .plugins.security import default_sanitizer
except ImportError:
    # Fallback if plugins not available
    default_sanitizer = None

from .http_adapters import get_adapter


class HTTPRecorder:
    """Records and replays HTTP requests."""

    def __init__(self, cassette_name: str, record_mode: str = "once", recordings_dir: str = "tests/recordings",
                 sanitize: bool = True, http_client: str = "requests"):
        self.cassette_name = cassette_name
        self.record_mode = record_mode
        self.cassette_path = Path(recordings_dir) / f"{cassette_name}.yaml"
        self.interactions = []
        self.sanitize = sanitize and default_sanitizer is not None
        self.http_client = http_client
        self.adapter = get_adapter(http_client)

    def _ensure_cassette_dir(self):
        """Ensure the cassettes directory exists."""
        self.cassette_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_cassette(self) -> List[Dict]:
        """Load existing cassette or return empty list."""
        if not self.cassette_path.exists():
            return []

        try:
            with open(self.cassette_path) as f:
                data = yaml.safe_load(f) or {}
                return data.get("interactions", [])
        except (OSError, yaml.YAMLError, PermissionError) as e:
            raise RuntimeError(f"Failed to load cassette {self.cassette_path}: {e}") from e

    def _save_cassette(self):
        """Save interactions to cassette file."""
        try:
            self._ensure_cassette_dir()
            data = {"interactions": self.interactions, "version": 1}
            with open(self.cassette_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False)
        except (OSError, yaml.YAMLError, PermissionError) as e:
            raise RuntimeError(f"Failed to save cassette {self.cassette_path}: {e}") from e

    def _find_matching_interaction(
        self, method: str, url: str, headers: Dict, body: Any
    ) -> Optional[Dict]:
        """Find a matching recorded interaction."""
        for interaction in self.interactions:
            request = interaction["request"]
            if (request["method"] == method and
                request["url"] == url and
                self._headers_match(request.get("headers", {}), headers) and
                request.get("body") == body):
                return interaction
        return None

    def _headers_match(self, recorded_headers: Dict, request_headers: Dict) -> bool:
        """Check if important headers match (excluding auth, timestamps, etc.)"""
        # Skip headers that commonly change between requests
        skip_headers = {
            'authorization', 'x-api-key', 'date', 'timestamp',
            'user-agent', 'x-request-id', 'x-correlation-id'
        }

        # For now, do a simple match excluding skip headers
        # In the future, this could be made configurable
        for key, value in recorded_headers.items():
            if key.lower() not in skip_headers:
                if request_headers.get(key) != value:
                    return False
        return True

    def _record_interaction(
        self, method: str, url: str, headers: Dict, body: Any, response
    ):
        """Record a new interaction with optional sanitization."""
        # Handle binary vs text content
        try:
            response_body = response.text
            is_binary = False
        except (UnicodeDecodeError, AttributeError):
            response_body = base64.b64encode(response.content).decode('ascii')
            is_binary = True

        interaction = {
            "request": {
                "method": method,
                "url": url,
                "headers": dict(headers) if headers else {},
                "body": body,
            },
            "response": {
                "status": response.status_code,
                "headers": dict(response.headers),
                "body": response_body,
                "is_binary": is_binary,
            },
        }

        # Apply sanitization if enabled
        if self.sanitize and default_sanitizer:
            interaction = default_sanitizer.sanitize_interaction(interaction)

        self.interactions.append(interaction)
        self._save_cassette()

    def _create_mock_response(self, interaction: Dict):
        """Create a mock response from a recorded interaction."""
        return self.adapter.create_mock_response(interaction["response"])

    def _mock_request(self, original_request):
        """Create a mock request function."""

        def mock_request_func(
            method, url, headers=None, data=None, json=None, **kwargs
        ):
            # Convert json to data if provided
            body = data
            if json is not None:
                body = json if isinstance(json, str) else json.dumps(json)

            # Look for existing interaction
            matching = self._find_matching_interaction(method, url, headers or {}, body)

            if matching and self.record_mode != "record":
                # Return recorded response (unless forced to record)
                return self._create_mock_response(matching)
            elif self.record_mode == "replay_only":
                # Fail if no recording exists and we're in replay-only mode
                raise Exception(f"No recorded interaction found for {method} {url} (replay_only mode)")
            elif self.record_mode in ("once", "record") and (not matching or self.record_mode == "record"):
                # Record new interaction (or re-record if mode is "record")
                response = original_request(
                    method, url, headers=headers, data=data, json=json, **kwargs
                )
                self._record_interaction(method, url, headers or {}, body, response)
                return response
            else:
                raise Exception(f"No recorded interaction found for {method} {url}")

        return mock_request_func

    def record_during(self, func: Callable) -> Callable:
        """
        Return a wrapped version of func that executes with HTTP recording.

        Args:
            func: Function to execute with HTTP recording

        Returns:
            Wrapped function
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Load existing cassette
            self.interactions = self._load_cassette()

            # Get patch targets from adapter
            patch_targets = self.adapter.get_patch_targets()
            
            # Import the HTTP client module dynamically
            try:
                client_module = __import__(self.http_client)
                
                # Get the original request function
                original_request = None
                for attr_path in patch_targets.values():
                    parts = attr_path.split('.')
                    obj = client_module
                    for part in parts[1:]:
                        obj = getattr(obj, part, None)
                        if obj is None:
                            break
                    if obj and callable(obj) and 'request' in attr_path:
                        original_request = obj
                        break
                
                if not original_request:
                    # Fallback: just run the test without recording
                    return func(*args, **kwargs)
                
                mock_request = self._mock_request(original_request)
                
                # Create patches for all targets
                patches = []
                for target_name, target_path in patch_targets.items():
                    if 'request' in target_name:
                        patches.append(patch(target_path, mock_request))
                    elif 'get' in target_name:
                        patches.append(patch(target_path, lambda url, **kw: mock_request("GET", url, **kw)))
                    elif 'post' in target_name:
                        patches.append(patch(target_path, lambda url, **kw: mock_request("POST", url, **kw)))
                    elif 'put' in target_name:
                        patches.append(patch(target_path, lambda url, **kw: mock_request("PUT", url, **kw)))
                    elif 'delete' in target_name:
                        patches.append(patch(target_path, lambda url, **kw: mock_request("DELETE", url, **kw)))
                
                # Apply all patches
                for p in patches:
                    p.__enter__()
                
                try:
                    return func(*args, **kwargs)
                finally:
                    # Clean up patches
                    for p in reversed(patches):
                        p.__exit__(None, None, None)
                        
            except ImportError:
                # HTTP client not available, just run the test
                return func(*args, **kwargs)

        return wrapper


def http_record(cassette_name: str, *, record_mode: str = "once", 
                recordings_dir: str = "tests/recordings", sanitize: bool = True,
                http_client: str = "requests"):
    """
    Convenience decorator for HTTP recording.
    
    Args:
        cassette_name: Name for the cassette file
        record_mode: Recording mode (once, record, replay_only)
        recordings_dir: Directory to store recordings
        sanitize: Whether to sanitize sensitive data
        http_client: HTTP client library to use (requests, httpx, aiohttp)
        
    Example:
        @test("API call works")
        @http_record("api_test")
        def test_api():
            response = requests.get("https://api.example.com/data")
            that(response.status_code).equals(200)
            
        # With httpx
        @test("HTTPX API call")
        @http_record("httpx_test", http_client="httpx")
        def test_httpx_api():
            response = httpx.get("https://api.example.com/data")
            that(response.status_code).equals(200)
    """
    def decorator(func):
        recorder = HTTPRecorder(
            cassette_name, 
            record_mode=record_mode,
            recordings_dir=recordings_dir,
            sanitize=sanitize,
            http_client=http_client
        )
        return recorder.record_during(func)
    return decorator


