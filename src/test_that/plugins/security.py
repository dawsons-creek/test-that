"""
Security utilities for the plugin system, including HTTP recording sanitization.
"""

import re
from typing import Any, Dict, Set
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


class SecuritySanitizer:
    """Handles sanitization of sensitive data in HTTP recordings and other contexts."""

    # Common sensitive header patterns
    SENSITIVE_HEADERS = {
        "authorization",
        "x-api-key",
        "cookie",
        "set-cookie",
        "x-auth-token",
        "x-access-token",
        "x-csrf-token",
        "proxy-authorization",
        "www-authenticate",
        "x-api-secret",
        "x-session-id",
        "x-user-token",
    }

    # Sensitive URL parameter patterns
    SENSITIVE_PARAMS = {
        "password",
        "token",
        "api_key",
        "apikey",
        "secret",
        "auth",
        "authorization",
        "session",
        "sid",
        "key",
        "access_token",
        "refresh_token",
        "client_secret",
    }

    # Patterns for sensitive data in request/response bodies
    SENSITIVE_PATTERNS = [
        re.compile(r'"password"\s*:\s*"[^"]*"', re.IGNORECASE),
        re.compile(r'"token"\s*:\s*"[^"]*"', re.IGNORECASE),
        re.compile(r'"api_key"\s*:\s*"[^"]*"', re.IGNORECASE),
        re.compile(r'"secret"\s*:\s*"[^"]*"', re.IGNORECASE),
        re.compile(r'"auth"\s*:\s*"[^"]*"', re.IGNORECASE),
        # Credit card patterns
        re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"),
        # Social security numbers
        re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"),
        # Email addresses in sensitive contexts
        re.compile(r'"email"\s*:\s*"[^"]*"', re.IGNORECASE),
    ]

    def __init__(
        self,
        custom_sensitive_headers: Set[str] = None,
        custom_sensitive_params: Set[str] = None,
    ):
        """Initialize sanitizer with optional custom patterns."""
        self.sensitive_headers = self.SENSITIVE_HEADERS.copy()
        if custom_sensitive_headers:
            self.sensitive_headers.update(custom_sensitive_headers)

        self.sensitive_params = self.SENSITIVE_PARAMS.copy()
        if custom_sensitive_params:
            self.sensitive_params.update(custom_sensitive_params)

    def sanitize_headers(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Sanitize sensitive headers."""
        sanitized = {}
        for key, value in headers.items():
            if key.lower() in self.sensitive_headers:
                sanitized[key] = "***REDACTED***"
            else:
                sanitized[key] = value
        return sanitized

    def sanitize_url(self, url: str) -> str:
        """Sanitize sensitive information from URL."""
        try:
            parsed = urlparse(url)

            # Parse query parameters
            query_params = parse_qs(parsed.query, keep_blank_values=True)
            sanitized_params = {}

            for key, values in query_params.items():
                if key.lower() in self.sensitive_params:
                    sanitized_params[key] = ["***REDACTED***"]
                else:
                    sanitized_params[key] = values

            # Rebuild query string
            sanitized_query = urlencode(sanitized_params, doseq=True)

            # Reconstruct URL
            sanitized_parsed = parsed._replace(query=sanitized_query)
            return urlunparse(sanitized_parsed)

        except Exception:
            # If URL parsing fails, return original URL
            # Better to leak some data than break functionality
            return url

    def sanitize_body(self, body: Any) -> Any:
        """Sanitize sensitive data from request/response body."""
        if not body:
            return body

        if isinstance(body, str):
            return self._sanitize_string_body(body)
        elif isinstance(body, dict):
            return self._sanitize_dict_body(body)
        elif isinstance(body, bytes):
            try:
                decoded = body.decode("utf-8")
                sanitized = self._sanitize_string_body(decoded)
                return sanitized.encode("utf-8")
            except UnicodeDecodeError:
                # If we can't decode, return as-is (might be binary data)
                return body
        else:
            return body

    def _sanitize_string_body(self, body: str) -> str:
        """Sanitize string body content."""
        sanitized = body
        for pattern in self.SENSITIVE_PATTERNS:
            sanitized = pattern.sub(
                lambda m: self._replace_sensitive_value(m.group(0)), sanitized
            )
        return sanitized

    def _sanitize_dict_body(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize dictionary body content."""
        sanitized = {}
        for key, value in body.items():
            if key.lower() in self.sensitive_params:
                sanitized[key] = "***REDACTED***"
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict_body(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    self._sanitize_dict_body(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                sanitized[key] = value
        return sanitized

    def _replace_sensitive_value(self, match: str) -> str:
        """Replace the value part of a sensitive key-value pair."""
        # Extract the key part and replace only the value
        if ":" in match:
            key_part, _ = match.split(":", 1)
            return f'{key_part}: "***REDACTED***"'
        else:
            return "***REDACTED***"

    def sanitize_interaction(self, interaction: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize a complete HTTP interaction (request + response)."""
        sanitized = interaction.copy()

        # Sanitize request
        if "request" in sanitized:
            request = sanitized["request"].copy()

            if "url" in request:
                request["url"] = self.sanitize_url(request["url"])

            if "headers" in request:
                request["headers"] = self.sanitize_headers(request["headers"])

            if "body" in request:
                request["body"] = self.sanitize_body(request["body"])

            sanitized["request"] = request

        # Sanitize response
        if "response" in sanitized:
            response = sanitized["response"].copy()

            if "headers" in response:
                response["headers"] = self.sanitize_headers(response["headers"])

            if "body" in response:
                response["body"] = self.sanitize_body(response["body"])

            sanitized["response"] = response

        return sanitized


class PluginSecurityValidator:
    """Validates plugin security and sandboxing."""

    @staticmethod
    def validate_plugin_source(plugin_path: str) -> bool:
        """Validate plugin source for basic security checks."""
        # This is a basic implementation - in production you'd want
        # more sophisticated security analysis

        dangerous_imports = [
            "subprocess",
            "os.system",
            "eval",
            "exec",
            "compile",
            "__import__",
            "open",
        ]

        try:
            with open(plugin_path) as f:
                content = f.read()

            for danger in dangerous_imports:
                if danger in content:
                    print(
                        f"Warning: Plugin contains potentially dangerous import: {danger}"
                    )
                    return False

            return True
        except Exception:
            return False

    @staticmethod
    def create_restricted_globals() -> Dict[str, Any]:
        """Create restricted global namespace for plugin execution."""
        safe_builtins = {
            "len",
            "str",
            "int",
            "float",
            "bool",
            "list",
            "dict",
            "set",
            "tuple",
            "range",
            "enumerate",
            "zip",
            "map",
            "filter",
            "sorted",
            "sum",
            "min",
            "max",
            "abs",
            "round",
            "isinstance",
            "issubclass",
            "hasattr",
            "getattr",
            "setattr",
            "type",
            "id",
            "hash",
            "repr",
            "format",
            "print",
        }

        return {name: getattr(__builtins__, name) for name in safe_builtins}


# Global sanitizer instance
default_sanitizer = SecuritySanitizer()
