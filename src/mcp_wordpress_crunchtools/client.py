"""WordPress REST API client with security hardening.

This module provides a secure async HTTP client for the WordPress REST API.
All requests go through this client to ensure consistent security practices.
"""

import base64
import json
import logging
from importlib.metadata import version
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

# Identify this client by name. httpx otherwise sends `python-httpx/<version>`,
# which Cloudflare's bot protection answers with an HTML challenge page instead
# of the REST API: that is what broke the Educated Confusion instance
# (RT #1596), whose zone has the protection on. A client that says what it is
# and where to complain is also simply the polite thing to send.
USER_AGENT = (
    f"mcp-wordpress-crunchtools/{version('mcp-wordpress-crunchtools')} "
    "(+https://github.com/crunchtools/mcp-wordpress)"
)


# WordPress returns a bare 404 for every collection, so the path is the only
# clue to which kind of thing was missing.
_NOT_FOUND_BY_COLLECTION = {
    "posts": PostNotFoundError,
    "pages": PageNotFoundError,
    "media": MediaNotFoundError,
    "comments": CommentNotFoundError,
}


# How much of a non-JSON body to quote back. Enough to recognise an HTML
# redirect page, a proxy error or a WAF block; short enough to stay readable.
BODY_SNIPPET_CHARS = 200


def _body_snippet(body: bytes) -> str:
    """A short, single-line excerpt of a response body, for an error message."""
    # Slice the bytes, then decode and normalise only that. A WAF page or a
    # proxy error can be megabytes, and decoding all of it to keep the first
    # 200 characters would copy it twice for nothing. Four times the snippet is
    # enough slack for the whitespace a collapse removes. `replace` covers the
    # multi-byte character the slice may cut in half.
    prefix = body[: BODY_SNIPPET_CHARS * 4]
    collapsed = " ".join(prefix.decode("utf-8", errors="replace").split())
    if not collapsed:
        return "<empty body>"
    if len(collapsed) > BODY_SNIPPET_CHARS or len(body) > len(prefix):
        return collapsed[:BODY_SNIPPET_CHARS] + "..."
    return collapsed


def _where(method: str, response: httpx.Response) -> str:
    """Which site and URL a response came from, for an error message."""
    return f"{method} {response.request.url} (HTTP {response.status_code})"


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
                    "User-Agent": USER_AGENT,
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

        # Stream the reply rather than letting httpx buffer it, so the size
        # limit holds for a chunked body that declares no Content-Length.
        try:
            request = client.build_request(**request_kwargs)
            response = await client.send(request, stream=True)
            try:
                body = await self._read_body(method, response)
            finally:
                await response.aclose()
        except httpx.TimeoutException as e:
            raise WordPressApiError("timeout", f"Request timeout: {e}") from e
        except httpx.RequestError as e:
            raise WordPressApiError("request_failed", f"Request failed: {e}") from e

        payload = self._payload(method, response, body)

        # Handle error responses
        if not response.is_success:
            self._handle_error_response(response.status_code, payload, path)

        return payload

    async def _read_body(self, method: str, response: httpx.Response) -> bytes:
        """The response body, refused as soon as it passes MAX_RESPONSE_SIZE.

        The Content-Length check is a cheap early exit for a site that is
        honest about the size; the running count is what enforces the limit,
        because a chunked reply sends no such header (#75).
        """
        content_length = response.headers.get("content-length")
        if content_length and int(content_length) > MAX_RESPONSE_SIZE:
            raise WordPressApiError(
                "response_too_large",
                f"{_where(method, response)} returned {content_length} bytes, "
                f"over the {MAX_RESPONSE_SIZE} byte limit.",
            )

        body = bytearray()
        async for chunk in response.aiter_bytes():
            body += chunk
            if len(body) > MAX_RESPONSE_SIZE:
                raise WordPressApiError(
                    "response_too_large",
                    f"{_where(method, response)} returned more than "
                    f"{MAX_RESPONSE_SIZE} bytes, over the byte limit.",
                )
        return bytes(body)

    def _payload(
        self, method: str, response: httpx.Response, body: bytes
    ) -> dict[str, Any] | list[Any]:
        """The decoded JSON body, or an error saying what came back instead.

        Every failure here names the site, the URL and the status, because a
        bare decode error cannot tell a site that is down from a base URL
        that redirects (RT #1596).
        """
        # A redirect is never a WordPress REST answer, and its HTML body is
        # what used to surface as "invalid JSON" with nothing to act on.
        # Redirects are not followed, because this client carries a Basic Auth
        # header that must not be forwarded to another host.
        if response.is_redirect:
            # ``is_redirect`` is only true when a Location header is present.
            location = response.headers["location"]
            raise WordPressApiError(
                "unexpected_redirect",
                f"{_where(method, response)} redirected to {location}. "
                f"WORDPRESS_URL is set to {self._config.base_url}; set it to the "
                "URL the site actually serves the REST API on, with no redirect.",
            )

        try:
            payload: dict[str, Any] | list[Any] = json.loads(body)
        except ValueError as e:
            content_type = response.headers.get("content-type", "<none>")
            detail = (
                f"{_where(method, response)} returned {content_type}, "
                f"not JSON: {_body_snippet(body)}"
            )
            if not response.is_success:
                raise WordPressApiError("http_error", detail) from e
            raise WordPressApiError("invalid_json", detail) from e

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
