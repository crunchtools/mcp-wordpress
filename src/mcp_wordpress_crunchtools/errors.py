"""Safe error types that can be shown to users.

This module defines exception classes that are safe to expose to MCP clients.
Internal errors should be caught and converted to UserError before propagating.
"""

import os


class UserError(Exception):
    """Base class for safe errors that can be shown to users.

    All error messages in UserError subclasses must be carefully crafted
    to avoid leaking sensitive information like passwords or internal paths.
    """

    pass


class ConfigurationError(UserError):
    """Error in server configuration."""

    pass


class InvalidPostIdError(UserError):
    """Invalid post ID format."""

    def __init__(self) -> None:
        super().__init__("Invalid post_id format. Expected positive integer.")


class InvalidPageIdError(UserError):
    """Invalid page ID format."""

    def __init__(self) -> None:
        super().__init__("Invalid page_id format. Expected positive integer.")


class InvalidMediaIdError(UserError):
    """Invalid media ID format."""

    def __init__(self) -> None:
        super().__init__("Invalid media_id format. Expected positive integer.")


class InvalidCommentIdError(UserError):
    """Invalid comment ID format."""

    def __init__(self) -> None:
        super().__init__("Invalid comment_id format. Expected positive integer.")


class PostNotFoundError(UserError):
    """Post not found or not accessible."""

    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Post not found or not accessible: {identifier}")


class PageNotFoundError(UserError):
    """Page not found or not accessible."""

    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Page not found or not accessible: {identifier}")


class MediaNotFoundError(UserError):
    """Media item not found or not accessible."""

    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Media item not found or not accessible: {identifier}")


class CommentNotFoundError(UserError):
    """Comment not found or not accessible."""

    def __init__(self, identifier: int | str) -> None:
        super().__init__(f"Comment not found or not accessible: {identifier}")


class PermissionDeniedError(UserError):
    """Permission denied for the requested operation."""

    def __init__(self, operation: str = "this operation") -> None:
        super().__init__(f"Permission denied for {operation}.")


class RateLimitError(UserError):
    """Rate limit exceeded."""

    def __init__(self, retry_after: int | None = None) -> None:
        msg = "Rate limit exceeded."
        if retry_after:
            msg += f" Retry after {retry_after} seconds."
        super().__init__(msg)


class WordPressApiError(UserError):
    """Error from WordPress REST API.

    The message is sanitized to remove any potential password references.
    """

    def __init__(self, code: str, message: str) -> None:
        # Sanitize message to remove any password references
        password = os.environ.get("WORDPRESS_APP_PASSWORD", "")
        safe_message = message.replace(password, "***") if password else message
        super().__init__(f"WordPress API error [{code}]: {safe_message}")


class ValidationError(UserError):
    """Input validation error."""

    pass
