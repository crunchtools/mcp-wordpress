"""Tests for tool functions."""

from mcp_wordpress_crunchtools.errors import (
    CommentNotFoundError,
    ConfigurationError,
    InvalidCommentIdError,
    InvalidMediaIdError,
    InvalidPageIdError,
    InvalidPostIdError,
    MediaNotFoundError,
    PageNotFoundError,
    PermissionDeniedError,
    PostNotFoundError,
    RateLimitError,
    UserError,
    ValidationError,
    WordPressApiError,
)


class TestErrorHierarchy:
    """Tests for error class hierarchy."""

    def test_user_error_is_exception(self) -> None:
        """Test UserError inherits from Exception."""
        assert issubclass(UserError, Exception)

    def test_all_errors_are_user_errors(self) -> None:
        """Test all custom errors inherit from UserError."""
        error_classes = [
            ConfigurationError,
            InvalidPostIdError,
            InvalidPageIdError,
            InvalidMediaIdError,
            InvalidCommentIdError,
            PostNotFoundError,
            PageNotFoundError,
            MediaNotFoundError,
            CommentNotFoundError,
            PermissionDeniedError,
            RateLimitError,
            WordPressApiError,
            ValidationError,
        ]
        for error_class in error_classes:
            assert issubclass(error_class, UserError)


class TestErrorMessages:
    """Tests for error message formatting."""

    def test_invalid_post_id_error_message(self) -> None:
        """Test InvalidPostIdError message."""
        error = InvalidPostIdError()
        assert "post_id" in str(error)
        assert "positive integer" in str(error)

    def test_invalid_page_id_error_message(self) -> None:
        """Test InvalidPageIdError message."""
        error = InvalidPageIdError()
        assert "page_id" in str(error)

    def test_invalid_media_id_error_message(self) -> None:
        """Test InvalidMediaIdError message."""
        error = InvalidMediaIdError()
        assert "media_id" in str(error)

    def test_invalid_comment_id_error_message(self) -> None:
        """Test InvalidCommentIdError message."""
        error = InvalidCommentIdError()
        assert "comment_id" in str(error)

    def test_post_not_found_error_message(self) -> None:
        """Test PostNotFoundError message."""
        error = PostNotFoundError(123)
        assert "123" in str(error)
        assert "not found" in str(error).lower()

    def test_page_not_found_error_message(self) -> None:
        """Test PageNotFoundError message."""
        error = PageNotFoundError("about")
        assert "about" in str(error)

    def test_permission_denied_error_message(self) -> None:
        """Test PermissionDeniedError message."""
        error = PermissionDeniedError("editing posts")
        assert "editing posts" in str(error)
        assert "denied" in str(error).lower()

    def test_rate_limit_error_without_retry(self) -> None:
        """Test RateLimitError without retry_after."""
        error = RateLimitError()
        assert "rate limit" in str(error).lower()

    def test_rate_limit_error_with_retry(self) -> None:
        """Test RateLimitError with retry_after."""
        error = RateLimitError(retry_after=60)
        assert "60" in str(error)
        assert "retry" in str(error).lower()

    def test_wordpress_api_error_sanitizes_password(self) -> None:
        """Test WordPressApiError sanitizes password from message."""
        import os

        # Set a test password
        os.environ["WORDPRESS_APP_PASSWORD"] = "secret_password_123"

        error = WordPressApiError("auth_error", "Failed with secret_password_123")
        error_msg = str(error)

        # Password should be masked
        assert "secret_password_123" not in error_msg
        assert "***" in error_msg

        # Cleanup
        del os.environ["WORDPRESS_APP_PASSWORD"]

    def test_wordpress_api_error_includes_code(self) -> None:
        """Test WordPressApiError includes error code."""
        error = WordPressApiError("rest_forbidden", "You are not allowed")
        assert "rest_forbidden" in str(error)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_configuration_error(self) -> None:
        """Test ConfigurationError message."""
        error = ConfigurationError("Missing API token")
        assert "Missing API token" in str(error)


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error(self) -> None:
        """Test ValidationError message."""
        error = ValidationError("Invalid input format")
        assert "Invalid input format" in str(error)
