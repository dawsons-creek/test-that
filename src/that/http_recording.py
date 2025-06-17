"""
HTTP recording functionality for deterministic testing.

Records HTTP requests and responses to YAML files for replay in tests.
"""

import base64
import functools
import json
import yaml
from pathlib import Path
from typing import Any, Callable, Dict, List
from unittest.mock import patch, MagicMock


class HTTPRecorder:
    """Records and replays HTTP requests."""

    def __init__(self, cassette_name: str, record_mode: str = "once", recordings_dir: str = "tests/recordings"):
        self.cassette_name = cassette_name
        self.record_mode = record_mode
        self.cassette_path = Path(recordings_dir) / f"{cassette_name}.yaml"
        self.interactions = []

    def _ensure_cassette_dir(self):
        """Ensure the cassettes directory exists."""
        self.cassette_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_cassette(self) -> List[Dict]:
        """Load existing cassette or return empty list."""
        if not self.cassette_path.exists():
            return []

        try:
            with open(self.cassette_path, "r") as f:
                data = yaml.safe_load(f) or {}
                return data.get("interactions", [])
        except (yaml.YAMLError, IOError, PermissionError) as e:
            raise RuntimeError(f"Failed to load cassette {self.cassette_path}: {e}") from e

    def _save_cassette(self):
        """Save interactions to cassette file."""
        try:
            self._ensure_cassette_dir()
            data = {"interactions": self.interactions, "version": 1}
            with open(self.cassette_path, "w") as f:
                yaml.dump(data, f, default_flow_style=False)
        except (yaml.YAMLError, IOError, PermissionError) as e:
            raise RuntimeError(f"Failed to save cassette {self.cassette_path}: {e}") from e

    def _find_matching_interaction(
        self, method: str, url: str, headers: Dict, body: Any
    ) -> Dict:
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
        """Record a new interaction."""
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
        self.interactions.append(interaction)
        self._save_cassette()

    def _create_mock_response(self, interaction: Dict):
        """Create a mock response from a recorded interaction."""
        response_data = interaction["response"]
        mock_response = MagicMock()
        mock_response.status_code = response_data["status"]
        mock_response.headers = response_data["headers"]

        # Handle binary vs text content
        if response_data.get("is_binary", False):
            mock_response.content = base64.b64decode(response_data["body"])
            mock_response.text = response_data["body"]  # Keep base64 for text access
        else:
            mock_response.text = response_data["body"]
            mock_response.content = response_data["body"].encode("utf-8")

        # Handle JSON responses
        try:
            if not response_data.get("is_binary", False):
                mock_response.json.return_value = json.loads(response_data["body"])
            else:
                mock_response.json.side_effect = ValueError(
                    "No JSON object could be decoded"
                )
        except (json.JSONDecodeError, TypeError):
            mock_response.json.side_effect = ValueError(
                "No JSON object could be decoded"
            )

        return mock_response

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

            # Patch requests library
            try:
                import requests

                original_request = requests.request
                mock_request = self._mock_request(original_request)

                with patch("requests.request", mock_request), patch(
                    "requests.get", lambda url, **kw: mock_request("GET", url, **kw)
                ), patch(
                    "requests.post", lambda url, **kw: mock_request("POST", url, **kw)
                ), patch(
                    "requests.put", lambda url, **kw: mock_request("PUT", url, **kw)
                ), patch(
                    "requests.delete",
                    lambda url, **kw: mock_request("DELETE", url, **kw),
                ):

                    return func(*args, **kwargs)
            except ImportError:
                # requests not available, just run the test
                return func(*args, **kwargs)
        
        return wrapper



