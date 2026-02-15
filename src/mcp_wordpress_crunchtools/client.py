"""WordPress REST API client with security hardening.

This module provides a secure async HTTP client for the WordPress REST API.
All requests go through this client to ensure consistent security practices.
"""

import base64
import logging
from typing import Any

import httpx

from .config import get_config
from .errors import (
    CommentNotFoundError,
    MediaNotFoundError,
    PageNotFoundError,
    PermissionDeniedError,
    PostNotFoundError,
    RateLimitError,
    WordPressApiError,
)

logger = logging.getLogger(__name__)

# Response size limit to prevent memory exhaustion (10MB)
MAX_RESPONSE_SIZE = 10 * 1024 * 1024

# Request timeout in seconds
REQUEST_TIMEOUT = 30.0


class WordPressClient:
    """Async HTTP client for WordPress REST API.

    Security features:
    - Hardcoded REST API path (prevents SSRF)
    - Basic auth via header (not URL)
    - TLS certificate validation (httpx default)
    - Request timeout enforcement
    - Response size limits
    """

    def __init__(self) -> None:
        """Initialize the WordPress client."""
        self._config = get_config()
        self._client: httpx.AsyncClient | None = None

    def _get_auth_header(self) -> str:
        """Generate Basic Auth header value."""
        credentials = f"{self._config.username}:{self._config.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self._config.api_base_url,
                headers={
                    "Authorization": self._get_auth_header(),
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(REQUEST_TIMEOUT),
                # Enable TLS certificate verification (default, but explicit)
                verify=True,
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json_data: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make an API request with error handling.

        Args:
            method: HTTP method (GET, POST, PUT, PATCH, DELETE)
            path: API path (e.g., /posts)
            params: Query parameters
            json_data: JSON body data
            data: Form data (for multipart uploads)
            files: Files for upload

        Returns:
            API response data

        Raises:
            WordPressApiError: On API errors
            RateLimitError: On rate limiting
            PermissionDeniedError: On authorization failures
        """
        client = await self._get_client()

        # Log request (without sensitive data)
        logger.debug("API request: %s %s", method, path)

        # Prepare request kwargs
        request_kwargs: dict[str, Any] = {
            "method": method,
            "url": path,
        }

        if params:
            request_kwargs["params"] = params
        if json_data:
            request_kwargs["json"] = json_data
        if data:
            request_kwargs["data"] = data
        if files:
            # For file uploads, remove Content-Type header (httpx sets it)
            request_kwargs["files"] = files
            request_kwargs["headers"] = {"Authorization": self._get_auth_header()}

        try:
            response = await client.request(**request_kwargs)
        except httpx.TimeoutException as e:
            raise WordPressApiError("timeout", f"Request timeout: {e}") from e
        except httpx.RequestError as e:
            raise WordPressApiError("request_failed", f"Request failed: {e}") from e

        # Check response size before parsing
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > MAX_RESPONSE_SIZE:
            raise WordPressApiError("response_too_large", "Response too large")

        # Parse response
        try:
            response_data = response.json()
        except ValueError as e:
            raise WordPressApiError(
                "invalid_json", f"Invalid JSON response: {e}"
            ) from e

        # Handle error responses
        if not response.is_success:
            self._handle_error_response(response.status_code, response_data, path)

        return response_data  # type: ignore[no-any-return]

    def _handle_error_response(
        self, status_code: int, data: dict[str, Any] | list[Any], path: str
    ) -> None:
        """Handle error responses from the API.

        Args:
            status_code: HTTP status code
            data: Response data
            path: Request path (for context)

        Raises:
            Various UserError subclasses based on error type
        """
        # WordPress error format: {"code": "...", "message": "...", "data": {...}}
        if isinstance(data, dict):
            error_code = data.get("code", "unknown_error")
            error_msg = data.get("message", "Unknown error")
        else:
            error_code = "unknown_error"
            error_msg = "Unknown error"

        # Handle specific status codes
        if status_code == 401:
            raise PermissionDeniedError("authentication required")
        if status_code == 403:
            raise PermissionDeniedError("this operation")
        if status_code == 404:
            # Determine resource type from path and extract ID
            resource_id = path.rsplit("/", maxsplit=1)[-1] if "/" in path else "unknown"
            if "/posts/" in path or path.endswith("/posts"):
                raise PostNotFoundError(resource_id)
            if "/pages/" in path or path.endswith("/pages"):
                raise PageNotFoundError(resource_id)
            if "/media/" in path or path.endswith("/media"):
                raise MediaNotFoundError(resource_id)
            if "/comments/" in path or path.endswith("/comments"):
                raise CommentNotFoundError(resource_id)
            raise WordPressApiError(error_code, error_msg)
        if status_code == 429:
            retry_after = None
            if isinstance(data, dict) and "data" in data:
                retry_after = data["data"].get("retry_after")
            raise RateLimitError(retry_after)

        raise WordPressApiError(error_code, error_msg)

    # Convenience methods for HTTP verbs

    async def get(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | list[Any]:
        """Make a GET request."""
        return await self._request("GET", path, params=params)

    async def post(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make a POST request."""
        return await self._request(
            "POST", path, params=params, json_data=json_data, data=data, files=files
        )

    async def put(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make a PUT request."""
        return await self._request("PUT", path, json_data=json_data)

    async def patch(
        self,
        path: str,
        json_data: dict[str, Any] | None = None,
    ) -> dict[str, Any] | list[Any]:
        """Make a PATCH request."""
        return await self._request("PATCH", path, json_data=json_data)

    async def delete(
        self, path: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any] | list[Any]:
        """Make a DELETE request."""
        return await self._request("DELETE", path, params=params)


# Global client instance
_client: WordPressClient | None = None


def get_client() -> WordPressClient:
    """Get the global WordPress client instance."""
    global _client
    if _client is None:
        _client = WordPressClient()
    return _client
