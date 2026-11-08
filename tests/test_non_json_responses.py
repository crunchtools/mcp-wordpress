"""A non-JSON reply has to say which site and URL produced it (RT #1596).

The Educated Confusion instance failed every call with a bare
``Invalid JSON response: Expecting value: line 1 column 1 (char 0)``, which
does not distinguish a site that is down from a base URL that redirects.
"""

import os
from importlib.metadata import version
from unittest.mock import patch

import pytest

from mcp_wordpress_crunchtools.client import MAX_RESPONSE_SIZE, USER_AGENT, get_client
from mcp_wordpress_crunchtools.config import Config
from mcp_wordpress_crunchtools.errors import ConfigurationError, WordPressApiError
from mcp_wordpress_crunchtools.tools import list_posts

from .conftest import _mock_raw_response, _mock_wp_response, _patch_wp_client


class TestRedirectResponses:
    """A 3xx is reported as a redirect, not as unparseable JSON."""

    @pytest.mark.asyncio
    async def test_redirect_names_the_url_and_the_destination(self) -> None:
        response = _mock_raw_response(
            status_code=301,
            body=b"<html><head><title>301 Moved Permanently</title></head></html>",
            headers={"location": "https://wp.example.com/wp-json/wp/v2/posts"},
            url="http://wp.example.com/wp-json/wp/v2/posts",
        )
        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        message = str(exc_info.value)
        assert "unexpected_redirect" in message
        assert "http://wp.example.com/wp-json/wp/v2/posts" in message
        assert "redirected to https://wp.example.com/wp-json/wp/v2/posts" in message
        # The configured site, so the reader knows which instance to fix.
        assert "WORDPRESS_URL is set to https://wp.example.com" in message
        assert "Expecting value" not in message

    @pytest.mark.asyncio
    async def test_redirect_is_not_followed(self) -> None:
        """Following would forward the Basic Auth header to another host."""
        response = _mock_raw_response(
            status_code=302,
            body=b"<html>moved</html>",
            headers={"location": "https://attacker.example.net/wp-json/wp/v2/posts"},
        )
        async with _patch_wp_client(response=response) as mock_request:
            with pytest.raises(WordPressApiError):
                await list_posts(per_page=5)

        assert mock_request.await_count == 1


class TestNonJsonBodies:
    """An HTML body on a 2xx or an error status is reported with context."""

    @pytest.mark.asyncio
    async def test_html_on_success_names_site_url_and_content_type(self) -> None:
        response = _mock_raw_response(
            status_code=200,
            body=b"<!DOCTYPE html><html><body>Attention Required! Cloudflare</body></html>",
        )
        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        message = str(exc_info.value)
        assert "invalid_json" in message
        assert "GET https://wp.example.com/wp-json/wp/v2/posts" in message
        assert "HTTP 200" in message
        assert "text/html" in message
        assert "Cloudflare" in message

    @pytest.mark.asyncio
    async def test_html_error_page_reports_the_status_not_invalid_json(self) -> None:
        response = _mock_raw_response(
            status_code=502,
            body=b"<html><head><title>502 Bad Gateway</title></head></html>",
        )
        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        message = str(exc_info.value)
        assert "http_error" in message
        assert "HTTP 502" in message
        assert "invalid_json" not in message

    @pytest.mark.asyncio
    async def test_empty_body_is_described_as_empty(self) -> None:
        response = _mock_raw_response(status_code=200, body=b"", content_type="text/plain")
        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        assert "<empty body>" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_long_body_is_truncated(self) -> None:
        response = _mock_raw_response(status_code=200, body=b"x" * 5000)
        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        message = str(exc_info.value)
        assert "..." in message
        assert len(message) < 600

    @pytest.mark.asyncio
    async def test_the_app_password_is_never_quoted_back(self) -> None:
        """A body that echoes the credential is still scrubbed."""
        response = _mock_raw_response(
            status_code=200,
            body=b"<html>rejected credential test_app_password</html>",
        )
        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        message = str(exc_info.value)
        assert "test_app_password" not in message
        assert "***" in message


class TestHttpsIsForced:
    """Plain http off loopback is upgraded, not warned about."""

    def test_http_url_is_upgraded_to_https(self) -> None:
        env = {
            "WORDPRESS_URL": "http://educatedconfusion.example.com",
            "WORDPRESS_USERNAME": "u",
            "WORDPRESS_APP_PASSWORD": "p",
        }
        with patch.dict(os.environ, env, clear=True):
            config = Config()

        assert config.base_url == "https://educatedconfusion.example.com"
        assert config.api_base_url == "https://educatedconfusion.example.com/wp-json/wp/v2"

    @pytest.mark.parametrize(
        "url",
        [
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://[::1]:8080",
            "http://LOCALHOST",
        ],
    )
    def test_loopback_keeps_http(self, url: str) -> None:
        env = {
            "WORDPRESS_URL": url,
            "WORDPRESS_USERNAME": "u",
            "WORDPRESS_APP_PASSWORD": "p",
        }
        with patch.dict(os.environ, env, clear=True):
            config = Config()

        assert config.base_url.startswith("http://")

    def test_a_host_merely_containing_localhost_is_still_upgraded(self) -> None:
        env = {
            "WORDPRESS_URL": "http://localhost.attacker.example.net",
            "WORDPRESS_USERNAME": "u",
            "WORDPRESS_APP_PASSWORD": "p",
        }
        with patch.dict(os.environ, env, clear=True):
            config = Config()

        assert config.base_url == "https://localhost.attacker.example.net"

    def test_a_url_with_no_host_is_still_refused(self) -> None:
        env = {
            "WORDPRESS_URL": "not-a-url",
            "WORDPRESS_USERNAME": "u",
            "WORDPRESS_APP_PASSWORD": "p",
        }
        with patch.dict(os.environ, env, clear=True), pytest.raises(ConfigurationError):
            Config()


class TestUserAgent:
    """The client identifies itself rather than sending httpx's default."""

    @pytest.mark.asyncio
    async def test_the_client_sends_a_named_user_agent(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=[])):
            await list_posts(per_page=1)
            client = get_client()
            http_client = await client._get_client()

        user_agent = http_client.headers["user-agent"]
        assert user_agent.startswith("mcp-wordpress-crunchtools/")
        assert "github.com/crunchtools/mcp-wordpress" in user_agent
        assert "httpx" not in user_agent

    def test_the_user_agent_carries_the_installed_version(self) -> None:
        installed = version("mcp-wordpress-crunchtools")
        assert f"mcp-wordpress-crunchtools/{installed}" in USER_AGENT


class TestOversizeResponses:
    """An oversize reply names the site and URL like every other failure."""

    @pytest.mark.asyncio
    async def test_too_large_names_the_url_and_the_sizes(self) -> None:
        response = _mock_raw_response(
            status_code=200,
            body=b"{}",
            content_type="application/json",
            headers={"content-length": str(50 * 1024 * 1024)},
        )
        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        message = str(exc_info.value)
        assert "response_too_large" in message
        assert "GET https://wp.example.com/wp-json/wp/v2/posts" in message
        assert str(MAX_RESPONSE_SIZE) in message

    @pytest.mark.asyncio
    async def test_a_megabyte_html_body_is_still_a_short_message(self) -> None:
        """The snippet is built from a bounded prefix, not the whole body."""
        body = b"<html>" + b"<div>filler</div>" * 100_000 + b"</html>"
        response = _mock_raw_response(status_code=200, body=body)
        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        message = str(exc_info.value)
        assert message.endswith("...")
        assert len(message) < 600
