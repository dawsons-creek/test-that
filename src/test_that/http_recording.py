"""
HTTP recording functionality for deterministic testing.

Records HTTP requests and responses to YAML files for replay in tests.
Includes security sanitization to prevent credential leakage.
"""

import base64
import functools
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from unittest.mock import patch

import yaml

try:
    from .plugins.security import default_sanitizer
except ImportError:
    # Fallback if plugins not available
    default_sanitizer = None

from .http_adapters import get_adapter


class HTTPRecorder:
    """Records and replays HTTP requests."""

    def __init__(
        self,
        cassette_name: str,
        record_mode: str = "once",
        recordings_dir: str = "tests/recordings",
        sanitize: bool = True,
        http_client: str = "requests",
    ):
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
            raise RuntimeError(
                f"Failed to load cassette {self.cassette_path}: {e}"
            ) from e

    def _save_cassette(self):
        """Save interactions to cassette file."""
        try:
            self._ensure_cassette_dir()
            data = {"interactions": self.interactions, "version": 1}
            with open(self.cassette_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False)
        except (OSError, yaml.YAMLError, PermissionError) as e:
            raise RuntimeError(
                f"Failed to save cassette {self.cassette_path}: {e}"
            ) from e

    def _find_matching_interaction(
        self, method: str, url: str, headers: Dict, body: Any
    ) -> Optional[Dict]:
        """Find a matching recorded interaction."""
        for interaction in self.interactions:
            request = interaction["request"]
            if (
                request["method"] == method
                and request["url"] == url
                and self._headers_match(request.get("headers", {}), headers)
                and request.get("body") == body
            ):
                return interaction
        return None

    def _headers_match(self, recorded_headers: Dict, request_headers: Dict) -> bool:
        """Check if important headers match (excluding auth, timestamps, etc.)"""
        # Skip headers that commonly change between requests
        skip_headers = {
            "authorization",
            "x-api-key",
            "date",
            "timestamp",
            "user-agent",
            "x-request-id",
            "x-correlation-id",
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
            response_body = base64.b64encode(response.content).decode("ascii")
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
            method, url, headers=None, data=None, json_data=None, **kwargs
        ):
            import json
            body = data
            if json_data is not None:
                body = json_data if isinstance(json_data, str) else json.dumps(json_data)

            matching = self._find_matching_interaction(method, url, headers or {}, body)

            if self.record_mode == "replay_only":
                return self._handle_replay_only(matching, method, url)
            elif self.record_mode == "record":
                return self._handle_record(
                    original_request, method, url, headers, data, json_data, body, **kwargs
                )
            elif self.record_mode == "once":
                return self._handle_once(
                    matching,
                    original_request,
                    method,
                    url,
                    headers,
                    data,
                    json_data,
                    body,
                    **kwargs,
                )
            else:
                raise Exception(f"Unknown record mode: {self.record_mode}")

        return mock_request_func

    def _handle_replay_only(self, matching, method, url):
        if not matching:
            raise Exception(
                f"No recorded interaction found for {method} {url} (replay_only mode)"
            )
        return self._create_mock_response(matching)

    def _handle_record(
        self, original_request, method, url, headers, data, json_data, body, **kwargs
    ):
        response = original_request(
            method, url, headers=headers, data=data, json=json_data, **kwargs
        )
        self._record_interaction(method, url, headers or {}, body, response)
        return response

    def _handle_once(
        self,
        matching,
        original_request,
        method,
        url,
        headers,
        data,
        json_data,
        body,
        **kwargs,
    ):
        if matching:
            return self._create_mock_response(matching)
        else:
            return self._handle_record(
                original_request, method, url, headers, data, json_data, body, **kwargs
            )

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
            self.interactions = self._load_cassette()
            patch_targets = self.adapter.get_patch_targets()

            try:
                original_request = self._get_original_request(patch_targets)
                if not original_request:
                    return func(*args, **kwargs)  # Fallback

                mock_request = self._mock_request(original_request)
                patches = self._create_patches(patch_targets, mock_request)

                with self._apply_patches(patches):
                    return func(*args, **kwargs)

            except ImportError:
                # HTTP client not available, just run the test
                return func(*args, **kwargs)

        return wrapper

    def _get_original_request(
        self, patch_targets: Dict[str, str]
    ) -> Optional[Callable]:
        """Get the original request function from the HTTP client module."""
        client_module = __import__(self.http_client)
        for attr_path in patch_targets.values():
            if "request" in attr_path:
                obj = client_module
                for part in attr_path.split(".")[1:]:
                    obj = getattr(obj, part, None)
                    if obj is None:
                        break
                if obj and callable(obj):
                    return obj
        return None

    def _create_patches(
        self, patch_targets: Dict[str, str], mock_request: Callable
    ) -> List[patch]:
        """Create a list of patch objects for all HTTP methods."""
        patches = []
        method_map = {
            "request": mock_request,
            "get": lambda url, **kw: mock_request("GET", url, **kw),
            "post": lambda url, **kw: mock_request("POST", url, **kw),
            "put": lambda url, **kw: mock_request("PUT", url, **kw),
            "delete": lambda url, **kw: mock_request("DELETE", url, **kw),
        }
        for name, path in patch_targets.items():
            for method_name, mock_func in method_map.items():
                if method_name in name:
                    patches.append(patch(path, mock_func))
                    break
        return patches

    def _apply_patches(self, patches: List[patch]):
        """Context manager to apply and clean up patches."""

        class PatchManager:
            def __enter__(self):
                for p in patches:
                    p.__enter__()

            def __exit__(self, exc_type, exc_val, exc_tb):
                for p in reversed(patches):
                    p.__exit__(exc_type, exc_val, exc_tb)

        return PatchManager()


def http_record(
    cassette_name: str,
    *,
    record_mode: str = "once",
    recordings_dir: str = "tests/recordings",
    sanitize: bool = True,
    http_client: str = "requests",
):
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
            http_client=http_client,
        )
        return recorder.record_during(func)

    return decorator
