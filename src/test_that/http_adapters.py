"""
HTTP client adapters for common libraries.

This module provides adapters for different HTTP client libraries
to work with the HTTPRecorder system.
"""

import base64
import json as json_lib
from typing import Any, Dict
from unittest.mock import MagicMock

from .http_client import HTTPClientAdapter


class RequestsAdapter(HTTPClientAdapter):
    """Adapter for the requests library."""

    def get_patch_targets(self) -> Dict[str, str]:
        """Get requests module paths to patch."""
        return {
            "request": "requests.request",
            "get": "requests.get",
            "post": "requests.post",
            "put": "requests.put",
            "delete": "requests.delete",
        }

    def create_mock_response(self, response_data: Dict[str, Any]) -> Any:
        """Create a mock requests.Response object."""
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
                mock_response.json.return_value = json_lib.loads(response_data["body"])
            else:
                mock_response.json.side_effect = ValueError(
                    "No JSON object could be decoded"
                )
        except (json_lib.JSONDecodeError, TypeError):
            mock_response.json.side_effect = ValueError(
                "No JSON object could be decoded"
            )

        return mock_response


class HTTPXAdapter(HTTPClientAdapter):
    """Adapter for the httpx library."""

    def get_patch_targets(self) -> Dict[str, str]:
        """Get httpx module paths to patch."""
        return {
            "request": "httpx.request",
            "get": "httpx.get",
            "post": "httpx.post",
            "put": "httpx.put",
            "delete": "httpx.delete",
            # Also patch client methods
            "client_request": "httpx.Client.request",
            "client_get": "httpx.Client.get",
            "client_post": "httpx.Client.post",
            "client_put": "httpx.Client.put",
            "client_delete": "httpx.Client.delete",
            # Async client methods
            "async_client_request": "httpx.AsyncClient.request",
            "async_client_get": "httpx.AsyncClient.get",
            "async_client_post": "httpx.AsyncClient.post",
            "async_client_put": "httpx.AsyncClient.put",
            "async_client_delete": "httpx.AsyncClient.delete",
        }

    def create_mock_response(self, response_data: Dict[str, Any]) -> Any:
        """Create a mock httpx.Response object."""
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
                mock_response.json.return_value = json_lib.loads(response_data["body"])
            else:
                mock_response.json.side_effect = ValueError(
                    "No JSON object could be decoded"
                )
        except (json_lib.JSONDecodeError, TypeError):
            mock_response.json.side_effect = ValueError(
                "No JSON object could be decoded"
            )

        return mock_response


class AioHTTPAdapter(HTTPClientAdapter):
    """Adapter for the aiohttp library."""

    def get_patch_targets(self) -> Dict[str, str]:
        """Get aiohttp module paths to patch."""
        return {
            # aiohttp uses ClientSession, not module-level functions
            "session_request": "aiohttp.ClientSession.request",
            "session_get": "aiohttp.ClientSession.get",
            "session_post": "aiohttp.ClientSession.post",
            "session_put": "aiohttp.ClientSession.put",
            "session_delete": "aiohttp.ClientSession.delete",
        }

    def create_mock_response(self, response_data: Dict[str, Any]) -> Any:
        """Create a mock aiohttp.ClientResponse object."""
        mock_response = MagicMock()
        mock_response.status = response_data["status"]  # aiohttp uses 'status', not 'status_code'
        mock_response.headers = response_data["headers"]

        # aiohttp uses async methods for content
        async def mock_text():
            if response_data.get("is_binary", False):
                return response_data["body"]  # Base64 string
            return response_data["body"]

        async def mock_read():
            if response_data.get("is_binary", False):
                return base64.b64decode(response_data["body"])
            return response_data["body"].encode("utf-8")

        async def mock_json():
            if not response_data.get("is_binary", False):
                return json_lib.loads(response_data["body"])
            raise ValueError("No JSON object could be decoded")

        mock_response.text = mock_text
        mock_response.read = mock_read
        mock_response.json = mock_json

        return mock_response


# Registry of available adapters
ADAPTERS = {
    "requests": RequestsAdapter,
    "httpx": HTTPXAdapter,
    "aiohttp": AioHTTPAdapter,
}


def get_adapter(client_name: str) -> HTTPClientAdapter:
    """Get an adapter instance for the specified client.
    
    Args:
        client_name: Name of the HTTP client library
        
    Returns:
        HTTPClientAdapter instance
        
    Raises:
        ValueError: If no adapter exists for the client
    """
    if client_name not in ADAPTERS:
        available = ", ".join(ADAPTERS.keys())
        raise ValueError(
            f"No adapter available for '{client_name}'. "
            f"Available adapters: {available}"
        )

    # Import the client module to pass to adapter
    try:
        client_module = __import__(client_name)
    except ImportError:
        client_module = None

    return ADAPTERS[client_name](client_module)

