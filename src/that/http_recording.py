"""
HTTP recording functionality for deterministic testing.

Records HTTP requests and responses to YAML files for replay in tests.
"""

import functools
import json
import yaml
from pathlib import Path
from typing import Any, Callable, Dict, List
from unittest.mock import patch, MagicMock


class HTTPRecorder:
    """Records and replays HTTP requests."""

    def __init__(self, cassette_name: str, record_mode: str = "once"):
        self.cassette_name = cassette_name
        self.record_mode = record_mode
        self.cassette_path = Path("tests/cassettes") / f"{cassette_name}.yaml"
        self.interactions = []

    def _ensure_cassette_dir(self):
        """Ensure the cassettes directory exists."""
        self.cassette_path.parent.mkdir(parents=True, exist_ok=True)

    def _load_cassette(self) -> List[Dict]:
        """Load existing cassette or return empty list."""
        if self.cassette_path.exists():
            with open(self.cassette_path, "r") as f:
                data = yaml.safe_load(f) or {}
                return data.get("interactions", [])
        return []

    def _save_cassette(self):
        """Save interactions to cassette file."""
        self._ensure_cassette_dir()
        data = {"interactions": self.interactions, "version": 1}
        with open(self.cassette_path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

    def _find_matching_interaction(
        self, method: str, url: str, headers: Dict, body: Any
    ) -> Dict:
        """Find a matching recorded interaction."""
        for interaction in self.interactions:
            request = interaction["request"]
            if request["method"] == method and request["url"] == url:
                return interaction
        return None

    def _record_interaction(
        self, method: str, url: str, headers: Dict, body: Any, response
    ):
        """Record a new interaction."""
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
                "body": response.text,
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
        mock_response.text = response_data["body"]
        mock_response.content = response_data["body"].encode("utf-8")

        # Handle JSON responses
        try:
            mock_response.json.return_value = json.loads(response_data["body"])
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
                body = json if isinstance(json, str) else str(json)

            # Look for existing interaction
            matching = self._find_matching_interaction(method, url, headers or {}, body)

            if matching:
                # Return recorded response
                return self._create_mock_response(matching)
            elif self.record_mode == "once":
                # Record new interaction
                response = original_request(
                    method, url, headers=headers, data=data, json=json, **kwargs
                )
                self._record_interaction(method, url, headers or {}, body, response)
                return response
            else:
                raise Exception(f"No recorded interaction found for {method} {url}")

        return mock_request_func


def recorded(cassette_name: str, record_mode: str = "once"):
    """
    Decorator to record HTTP requests during test execution.

    Args:
        cassette_name: Name of the cassette file (without .yaml extension)
        record_mode: "once" to record if not exists, "new_episodes" to record new requests

    Example:
        @test("fetches user from API")
        @recorded("user_fetch")
        def test_fetch_user():
            response = requests.get("https://api.example.com/user/123")
            that(response.json()["name"]).equals("John Doe")
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            recorder = HTTPRecorder(cassette_name, record_mode)

            # Load existing cassette
            recorder.interactions = recorder._load_cassette()

            # Patch requests library
            try:
                import requests

                original_request = requests.request
                mock_request = recorder._mock_request(original_request)

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

    return decorator
