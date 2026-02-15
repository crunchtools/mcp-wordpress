"""WordPress MCP tools.

This package contains all the MCP tool implementations for WordPress operations.
"""

from .comments import (
    create_comment,
    delete_comment,
    get_comment,
    list_comments,
    moderate_comment,
    update_comment,
)
from .media import (
    delete_media,
    get_media,
    get_media_url,
    list_media,
    update_media,
    upload_media,
)
from .pages import (
    create_page,
    delete_page,
    get_page,
    list_page_revisions,
    list_pages,
    update_page,
)
from .posts import (
    create_post,
    delete_post,
    get_post,
    get_revision,
    list_categories,
    list_posts,
    list_revisions,
    list_tags,
    search_posts,
    update_post,
)
from .site import get_site_info, test_connection

__all__ = [
    # Site
    "get_site_info",
    "test_connection",
    # Posts
    "list_posts",
    "get_post",
    "search_posts",
    "create_post",
    "update_post",
    "delete_post",
    "list_revisions",
    "get_revision",
    "list_categories",
    "list_tags",
    # Pages
    "list_pages",
    "get_page",
    "create_page",
    "update_page",
    "delete_page",
    "list_page_revisions",
    # Media
    "list_media",
    "get_media",
    "upload_media",
    "update_media",
    "delete_media",
    "get_media_url",
    # Comments
    "list_comments",
    "get_comment",
    "create_comment",
    "update_comment",
    "delete_comment",
    "moderate_comment",
]
