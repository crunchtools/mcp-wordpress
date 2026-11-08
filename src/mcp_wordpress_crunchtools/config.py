"""Secure configuration handling.

This module handles all configuration including sensitive credentials.
Credentials are stored as SecretStr to prevent accidental logging.
"""

import logging
import os
from urllib.parse import SplitResult, urlsplit

from pydantic import SecretStr

from .errors import ConfigurationError

logger = logging.getLogger(__name__)


LOCAL_HOSTS = frozenset({"localhost", "127.0.0.1", "::1"})


def _authority(parsed: SplitResult) -> str:
    """Host and port, with any ``user:password@`` dropped.

    The base URL is quoted back in log lines and error messages, so a
    credential someone put in ``WORDPRESS_URL`` must not survive into it.
    Credentials belong in ``WORDPRESS_USERNAME`` and
    ``WORDPRESS_APP_PASSWORD``, where they are held as a ``SecretStr``.
    """
    host = parsed.hostname or ""
    if ":" in host:  # an IPv6 literal, which a URL writes in brackets
        host = f"[{host}]"
    try:
        port = parsed.port
    except ValueError as e:
        raise ConfigurationError(f"WORDPRESS_URL has an invalid port: {e}") from e
    return host if port is None else f"{host}:{port}"


class Config:
    """Secure configuration handling.

    The application password is stored as a SecretStr and should only be accessed
    via the password property when actually needed for API calls.
    """

    def __init__(self) -> None:
        """Initialize configuration from environment variables.

        Raises:
            ConfigurationError: If required environment variables are missing.
        """
        # WordPress URL
        url = os.environ.get("WORDPRESS_URL")
        if not url:
            raise ConfigurationError(
                "WORDPRESS_URL environment variable required. Example: https://example.com"
            )

        parsed = urlsplit(url)
        authority = _authority(parsed)
        if not parsed.scheme or not authority:
            raise ConfigurationError(
                "WORDPRESS_URL must be a valid URL (e.g., https://example.com)"
            )

        # Force HTTPS everywhere but a local development site: a plain-http
        # base URL sends the application password in the clear. Upgrading the
        # scheme is both the safe and the working choice, so do it rather than
        # warn and carry on.
        scheme = parsed.scheme
        if scheme != "https" and (parsed.hostname or "") not in LOCAL_HOSTS:
            logger.warning(
                "WORDPRESS_URL uses %s://%s; upgrading to https so the "
                "application password is not sent in the clear",
                scheme,
                authority,
            )
            scheme = "https"

        # Store normalized base URL (without trailing slash)
        self._base_url = f"{scheme}://{authority}".rstrip("/")

        # WordPress username
        username = os.environ.get("WORDPRESS_USERNAME")
        if not username:
            raise ConfigurationError("WORDPRESS_USERNAME environment variable required.")
        self._username = username

        # WordPress application password
        password = os.environ.get("WORDPRESS_APP_PASSWORD")
        if not password:
            raise ConfigurationError(
                "WORDPRESS_APP_PASSWORD environment variable required. "
                "Create an application password in WordPress: "
                "Users -> Profile -> Application Passwords"
            )

        # Store as SecretStr to prevent accidental logging
        self._password = SecretStr(password)
        logger.info("Configuration loaded successfully")

    @property
    def base_url(self) -> str:
        """Get the WordPress site base URL."""
        return self._base_url

    @property
    def api_base_url(self) -> str:
        """Get the WordPress REST API base URL.

        This is hardcoded to the standard WordPress REST API path
        to prevent SSRF attacks.
        """
        return f"{self._base_url}/wp-json/wp/v2"

    @property
    def username(self) -> str:
        """Get the WordPress username."""
        return self._username

    @property
    def password(self) -> str:
        """Get the application password value for API calls.

        Use sparingly - only when making actual API calls.
        """
        return self._password.get_secret_value()

    def __repr__(self) -> str:
        """Safe repr that never exposes the password."""
        return f"Config(url={self._base_url}, username={self._username}, password=***)"

    def __str__(self) -> str:
        """Safe str that never exposes the password."""
        return f"Config(url={self._base_url}, username={self._username}, password=***)"


# Global configuration instance - initialized on first import
_config: Config | None = None


def get_config() -> Config:
    """Get the global configuration instance.

    This function lazily initializes the configuration on first call.
    Subsequent calls return the same instance.

    Returns:
        The global Config instance.

    Raises:
        ConfigurationError: If configuration is invalid.
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
