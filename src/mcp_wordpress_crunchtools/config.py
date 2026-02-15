"""Secure configuration handling.

This module handles all configuration including sensitive credentials.
Credentials are stored as SecretStr to prevent accidental logging.
"""

import logging
import os
from urllib.parse import urlparse

from pydantic import SecretStr

from .errors import ConfigurationError

logger = logging.getLogger(__name__)


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
                "WORDPRESS_URL environment variable required. "
                "Example: https://example.com"
            )

        # Validate and normalize URL
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ConfigurationError(
                "WORDPRESS_URL must be a valid URL (e.g., https://example.com)"
            )

        # Force HTTPS in production
        if parsed.scheme != "https" and "localhost" not in parsed.netloc:
            logger.warning("WORDPRESS_URL should use HTTPS for security")

        # Store normalized base URL (without trailing slash)
        self._base_url = f"{parsed.scheme}://{parsed.netloc}".rstrip("/")

        # WordPress username
        username = os.environ.get("WORDPRESS_USERNAME")
        if not username:
            raise ConfigurationError(
                "WORDPRESS_USERNAME environment variable required."
            )
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
