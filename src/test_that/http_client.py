"""
HTTP client abstraction for the That testing library.

This module provides a protocol/interface for HTTP clients, allowing
HTTPRecorder to work with different HTTP libraries (requests, httpx, aiohttp, etc).
"""

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class HTTPResponse(Protocol):
    """Protocol for HTTP response objects."""

    @property
    def status_code(self) -> int:
        """HTTP status code."""
        ...

    @property
    def headers(self) -> Dict[str, str]:
        """Response headers."""
        ...

    @property
    def text(self) -> str:
        """Response body as text."""
        ...

    @property
    def content(self) -> bytes:
        """Response body as bytes."""
        ...

    def json(self) -> Any:
        """Parse response body as JSON."""
        ...


@runtime_checkable
class HTTPClient(Protocol):
    """Protocol for HTTP client implementations."""

    def request(
        self,
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        **kwargs
    ) -> HTTPResponse:
        """Make an HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc)
            url: URL to request
            headers: Optional headers dict
            data: Optional request body data
            json: Optional JSON data (will be serialized)
            **kwargs: Additional client-specific arguments
            
        Returns:
            HTTPResponse object
        """
        ...

    def get(self, url: str, **kwargs) -> HTTPResponse:
        """Make a GET request."""
        ...

    def post(self, url: str, **kwargs) -> HTTPResponse:
        """Make a POST request."""
        ...

    def put(self, url: str, **kwargs) -> HTTPResponse:
        """Make a PUT request."""
        ...

    def delete(self, url: str, **kwargs) -> HTTPResponse:
        """Make a DELETE request."""
        ...


class HTTPClientAdapter:
    """Base class for HTTP client adapters."""

    def __init__(self, client_module: Any):
        """Initialize adapter with the client module."""
        self.client_module = client_module

    def get_patch_targets(self) -> Dict[str, str]:
        """Get the module paths to patch.
        
        Returns:
            Dict mapping attribute names to module paths to patch.
            E.g., {"request": "requests.request", "get": "requests.get"}
        """
        raise NotImplementedError

    def create_mock_response(self, response_data: Dict[str, Any]) -> Any:
        """Create a mock response object for this client.
        
        Args:
            response_data: Dict with status, headers, body, is_binary
            
        Returns:
            Mock response object compatible with the client
        """
        raise NotImplementedError
