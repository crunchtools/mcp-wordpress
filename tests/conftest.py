"""Shared test fixtures for mcp-wordpress tests."""

import json
import os
from collections.abc import AsyncIterator, Generator
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import AsyncMock, patch

import httpx
import pytest


@pytest.fixture(autouse=True)
def _reset_client_singleton() -> Generator[None, None, None]:
    """Reset the WordPress client and config singletons between tests."""
    import mcp_wordpress_crunchtools.client as client_mod
    import mcp_wordpress_crunchtools.config as config_mod

    client_mod._client = None
    config_mod._config = None
    yield
    client_mod._client = None
    config_mod._config = None


def _mock_wp_response(
    status_code: int = 200,
    json_data: dict[str, Any] | list[Any] | None = None,
) -> httpx.Response:
    """Build a mock WordPress REST API JSON response."""
    if json_data is None:
        json_data = {}
    return httpx.Response(
        status_code,
        content=json.dumps(json_data).encode(),
        headers={"content-type": "application/json"},
        request=httpx.Request("GET", "https://wp.example.com/wp-json/wp/v2"),
    )


@asynccontextmanager
async def _patch_wp_client(
    method: str = "request",
    response: httpx.Response | None = None,
    side_effect: list[httpx.Response] | None = None,
) -> AsyncIterator[AsyncMock]:
    """Patch httpx.AsyncClient to return mock WordPress responses."""
    env = {
        "WORDPRESS_URL": "https://wp.example.com",
        "WORDPRESS_USERNAME": "test_user",
        "WORDPRESS_APP_PASSWORD": "test_app_password",
    }
    mock_method = AsyncMock()
    if side_effect is not None:
        mock_method.side_effect = side_effect
    elif response is not None:
        mock_method.return_value = response
    else:
        mock_method.return_value = _mock_wp_response()

    with patch.dict(os.environ, env, clear=True), patch(
        f"httpx.AsyncClient.{method}", mock_method
    ):
        yield mock_method
