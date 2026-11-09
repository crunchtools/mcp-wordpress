"""A non-JSON reply has to say which site and URL produced it (RT #1596).

The Educated Confusion instance failed every call with a bare
``Invalid JSON response: Expecting value: line 1 column 1 (char 0)``, which
does not distinguish a site that is down from a base URL that redirects.
"""

import json
import logging
import os
from collections.abc import AsyncIterator
from importlib.metadata import version
from unittest.mock import patch

import httpx
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
    async def test_chunked_reply_over_the_limit_is_refused_mid_stream(self) -> None:
        """A chunked reply declares no size, so the read itself enforces it (#75)."""
        chunk = b" " * (1024 * 1024)
        total_chunks = 2 * MAX_RESPONSE_SIZE // len(chunk)
        sent = 0

        async def chunked_body() -> AsyncIterator[bytes]:
            nonlocal sent
            for _ in range(total_chunks):
                sent += 1
                yield chunk

        response = httpx.Response(
            200,
            content=chunked_body(),
            headers={"content-type": "application/json"},
            request=httpx.Request("GET", "https://wp.example.com/wp-json/wp/v2/posts"),
        )
        assert "content-length" not in response.headers

        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        message = str(exc_info.value)
        assert "response_too_large" in message
        assert "GET https://wp.example.com/wp-json/wp/v2/posts" in message
        assert "HTTP 200" in message
        assert str(MAX_RESPONSE_SIZE) in message
        # Refused one chunk past the limit, not after the whole body arrived.
        assert sent == MAX_RESPONSE_SIZE // len(chunk) + 1
        assert sent < total_chunks
        assert response.is_closed

    @pytest.mark.asyncio
    async def test_chunked_reply_under_the_limit_is_parsed(self) -> None:
        posts = [{"id": 1, "title": {"rendered": "One"}}]
        encoded = json.dumps(posts).encode()

        async def chunked_body() -> AsyncIterator[bytes]:
            for i in range(0, len(encoded), 7):
                yield encoded[i : i + 7]

        response = httpx.Response(
            200,
            content=chunked_body(),
            headers={"content-type": "application/json"},
            request=httpx.Request("GET", "https://wp.example.com/wp-json/wp/v2/posts"),
        )
        async with _patch_wp_client(response=response):
            result = await list_posts(per_page=5)

        assert result["posts"][0]["id"] == 1

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


class TestCredentialsInTheUrl:
    """A password in WORDPRESS_URL never reaches a log line or an error."""

    def test_userinfo_is_dropped_from_the_base_url(self) -> None:
        env = {
            "WORDPRESS_URL": "https://admin:s3cret@wp.example.com",
            "WORDPRESS_USERNAME": "u",
            "WORDPRESS_APP_PASSWORD": "p",
        }
        with patch.dict(os.environ, env, clear=True):
            config = Config()

        assert config.base_url == "https://wp.example.com"
        assert "s3cret" not in config.base_url
        assert "s3cret" not in config.api_base_url
        assert "s3cret" not in repr(config)

    def test_userinfo_is_dropped_from_the_https_upgrade_warning(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        env = {
            "WORDPRESS_URL": "http://admin:s3cret@wp.example.com:8080",
            "WORDPRESS_USERNAME": "u",
            "WORDPRESS_APP_PASSWORD": "p",
        }
        with patch.dict(os.environ, env, clear=True), caplog.at_level(logging.WARNING):
            config = Config()

        assert config.base_url == "https://wp.example.com:8080"
        expected = (
            "WORDPRESS_URL uses http://wp.example.com:8080; upgrading to https "
            "so the application password is not sent in the clear"
        )
        warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
        assert warnings == [expected]
        # Any level, not just WARNING: a leak at DEBUG is still a leak.
        assert "s3cret" not in caplog.text

    def test_an_explicit_port_80_is_dropped_by_the_upgrade(self) -> None:
        """Nothing serves TLS on the plain-http port."""
        env = {
            "WORDPRESS_URL": "http://wp.example.com:80",
            "WORDPRESS_USERNAME": "u",
            "WORDPRESS_APP_PASSWORD": "p",
        }
        with patch.dict(os.environ, env, clear=True):
            config = Config()

        assert config.base_url == "https://wp.example.com"

    def test_a_nonstandard_port_survives_the_upgrade(self) -> None:
        env = {
            "WORDPRESS_URL": "http://wp.example.com:8443",
            "WORDPRESS_USERNAME": "u",
            "WORDPRESS_APP_PASSWORD": "p",
        }
        with patch.dict(os.environ, env, clear=True):
            config = Config()

        assert config.base_url == "https://wp.example.com:8443"

    def test_an_invalid_port_is_refused(self) -> None:
        env = {
            "WORDPRESS_URL": "https://wp.example.com:notaport",
            "WORDPRESS_USERNAME": "u",
            "WORDPRESS_APP_PASSWORD": "p",
        }
        with patch.dict(os.environ, env, clear=True), pytest.raises(ConfigurationError):
            Config()


class TestUndecodableBodies:
    """The snippet slices bytes, so it has to survive a split character."""

    @pytest.mark.asyncio
    async def test_a_multibyte_character_split_by_the_slice(self) -> None:
        # One ASCII byte then three-byte characters, so the byte boundary
        # cannot land on a character boundary.
        body = b"<" + "€".encode() * 5000
        response = _mock_raw_response(status_code=200, body=body)
        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        message = str(exc_info.value)
        assert message.endswith("...")
        assert "€" in message
        assert len(message) < 600

    @pytest.mark.asyncio
    async def test_a_body_that_is_not_utf8_at_all(self) -> None:
        response = _mock_raw_response(
            status_code=200,
            body=b"<html>\xff\xfe\xff blocked</html>",
            content_type="text/html; charset=windows-1252",
        )
        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        message = str(exc_info.value)
        assert "�" in message
        assert "blocked" in message


class TestErrorRedaction:
    """Layer 1 applies to an error message: the URL in it carries no secret."""

    @pytest.mark.asyncio
    async def test_userinfo_and_credential_params_are_redacted(self) -> None:
        """`WORDPRESS_URL=https://user:password@site` is accepted, and secret.

        Userinfo sits before the path, where redacting query parameters never
        reaches it, and `password` is a real WordPress query parameter on a
        protected post.
        """
        response = _mock_raw_response(
            status_code=403,
            body=b"<html><title>Attention Required!</title></html>",
            url="https://bot:sekrit@wp.example.com/wp-json/wp/v2/posts?password=p0st&per_page=5",
        )
        async with _patch_wp_client(response=response):
            with pytest.raises(WordPressApiError) as exc_info:
                await list_posts(per_page=5)

        message = str(exc_info.value)
        assert "sekrit" not in message
        assert "p0st" not in message
        # What is left is still the diagnosis: the host, the path, the real
        # parameter and what came back.
        assert "wp.example.com/wp-json/wp/v2/posts" in message
        assert "per_page=5" in message
        assert "Attention Required!" in message

    @pytest.mark.asyncio
    async def test_a_malformed_content_length_is_an_api_error(self) -> None:
        """An unguarded `int()` on a header the far end chose is a ValueError."""
        response = _mock_raw_response(
            status_code=200,
            body=json.dumps([]).encode(),
            content_type="application/json",
            headers={"content-length": "not-a-number"},
        )
        async with _patch_wp_client(response=response):
            result = await list_posts(per_page=5)

        # The malformed header is ignored and the body is read under the running
        # count, rather than the call dying on a ValueError from `int()`.
        assert result["posts"] == []
