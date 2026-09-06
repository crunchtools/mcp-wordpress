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
    UserError,
    WordPressApiError,
)

logger = logging.getLogger(__name__)

# Response size limit to prevent memory exhaustion (10MB)
MAX_RESPONSE_SIZE = 10 * 1024 * 1024

# Request timeout in seconds
REQUEST_TIMEOUT = 30.0


# WordPress returns a bare 404 for every collection, so the path is the only
# clue to which kind of thing was missing.
_NOT_FOUND_BY_COLLECTION = {
    "posts": PostNotFoundError,
    "pages": PageNotFoundError,
    "media": MediaNotFoundError,
    "comments": CommentNotFoundError,
}


def _not_found_error(path: str) -> UserError | None:
    """The specific not-found error for a REST path, if the collection is known."""
    resource_id = path.rsplit("/", maxsplit=1)[-1] if "/" in path else "unknown"
    for collection, error in _NOT_FOUND_BY_COLLECTION.items():
        if f"/{collection}/" in path or path.endswith(f"/{collection}"):
            return error(resource_id)
    return None


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
            # For file uploads, let httpx set multipart Content-Type with boundary
            request_kwargs["files"] = files

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
            payload: dict[str, Any] | list[Any] = response.json()
        except ValueError as e:
            raise WordPressApiError("invalid_json", f"Invalid JSON response: {e}") from e

        # Handle error responses
        if not response.is_success:
            self._handle_error_response(response.status_code, payload, path)

        return payload

    def _handle_error_response(
        self, status_code: int, payload: dict[str, Any] | list[Any], path: str
    ) -> None:
        """Handle error responses from the API.

        Args:
            status_code: HTTP status code
            payload: Parsed response body
            path: Request path (for context)

        Raises:
            Various UserError subclasses based on error type
        """
        if isinstance(payload, dict):
            error_code = payload.get("code", "unknown_error")
            error_msg = payload.get("message", "Unknown error")
        else:
            error_code = "unknown_error"
            error_msg = "Unknown error"

        if status_code == 401:
            raise PermissionDeniedError("authentication required")
        if status_code == 403:
            raise PermissionDeniedError("this operation")
        if status_code == 404:
            not_found = _not_found_error(path)
            raise not_found if not_found else WordPressApiError(error_code, error_msg)
        if status_code == 429:
            retry_after = None
            if isinstance(payload, dict) and "data" in payload:
                retry_after = payload["data"].get("retry_after")
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
