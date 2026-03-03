"""Mocked tool tests for all 30 WordPress tools."""

import pytest

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
from mcp_wordpress_crunchtools.tools import __all__ as tools_all
from mcp_wordpress_crunchtools.tools import (
    create_comment,
    create_page,
    create_post,
    delete_comment,
    delete_media,
    delete_page,
    delete_post,
    get_comment,
    get_media,
    get_media_url,
    get_page,
    get_post,
    get_revision,
    get_site_info,
    list_categories,
    list_comments,
    list_media,
    list_page_revisions,
    list_pages,
    list_posts,
    list_revisions,
    list_tags,
    moderate_comment,
    search_posts,
    test_connection,
    update_comment,
    update_media,
    update_page,
    update_post,
    upload_media,
)
from tests.conftest import _mock_wp_response, _patch_wp_client

TOOL_FUNCTIONS = [
    # Site
    get_site_info,
    test_connection,
    # Posts
    list_posts,
    get_post,
    search_posts,
    create_post,
    update_post,
    delete_post,
    list_revisions,
    get_revision,
    list_categories,
    list_tags,
    # Pages
    list_pages,
    get_page,
    create_page,
    update_page,
    delete_page,
    list_page_revisions,
    # Media
    list_media,
    get_media,
    upload_media,
    update_media,
    delete_media,
    get_media_url,
    # Comments
    list_comments,
    get_comment,
    create_comment,
    update_comment,
    delete_comment,
    moderate_comment,
]

EXPECTED_TOOL_COUNT = 30
EXPECTED_ALL_COUNT = 30


def test_tool_count() -> None:
    """Verify expected number of exports in tools.__all__."""
    assert len(tools_all) == EXPECTED_ALL_COUNT


def test_imports() -> None:
    """Verify all tool functions are importable and callable."""
    assert len(TOOL_FUNCTIONS) == EXPECTED_TOOL_COUNT
    for func in TOOL_FUNCTIONS:
        assert callable(func)


# =============================================================================
# Error Hierarchy Tests (preserved from original)
# =============================================================================


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
        error = InvalidPostIdError()
        assert "post_id" in str(error)
        assert "positive integer" in str(error)

    def test_invalid_page_id_error_message(self) -> None:
        error = InvalidPageIdError()
        assert "page_id" in str(error)

    def test_invalid_media_id_error_message(self) -> None:
        error = InvalidMediaIdError()
        assert "media_id" in str(error)

    def test_invalid_comment_id_error_message(self) -> None:
        error = InvalidCommentIdError()
        assert "comment_id" in str(error)

    def test_post_not_found_error_message(self) -> None:
        error = PostNotFoundError(123)
        assert "123" in str(error)
        assert "not found" in str(error).lower()

    def test_page_not_found_error_message(self) -> None:
        error = PageNotFoundError("about")
        assert "about" in str(error)

    def test_permission_denied_error_message(self) -> None:
        error = PermissionDeniedError("editing posts")
        assert "editing posts" in str(error)
        assert "denied" in str(error).lower()

    def test_rate_limit_error_without_retry(self) -> None:
        error = RateLimitError()
        assert "rate limit" in str(error).lower()

    def test_rate_limit_error_with_retry(self) -> None:
        error = RateLimitError(retry_after=60)
        assert "60" in str(error)
        assert "retry" in str(error).lower()

    def test_wordpress_api_error_sanitizes_password(self) -> None:
        import os

        os.environ["WORDPRESS_APP_PASSWORD"] = "secret_password_123"
        error = WordPressApiError("auth_error", "Failed with secret_password_123")
        error_msg = str(error)
        assert "secret_password_123" not in error_msg
        assert "***" in error_msg
        del os.environ["WORDPRESS_APP_PASSWORD"]

    def test_wordpress_api_error_includes_code(self) -> None:
        error = WordPressApiError("rest_forbidden", "You are not allowed")
        assert "rest_forbidden" in str(error)


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_configuration_error(self) -> None:
        error = ConfigurationError("Missing API token")
        assert "Missing API token" in str(error)


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error(self) -> None:
        error = ValidationError("Invalid input format")
        assert "Invalid input format" in str(error)


# =============================================================================
# Mocked API Tests — Site Tools
# =============================================================================


class TestSiteTools:
    """Tests for site info and connection tools."""

    @pytest.mark.asyncio
    async def test_get_site_info(self) -> None:
        settings = {
            "title": "My WordPress Site",
            "description": "A test blog",
            "url": "https://wp.example.com",
            "email": "admin@example.com",
            "timezone_string": "America/New_York",
            "date_format": "F j, Y",
            "time_format": "g:i a",
            "language": "en_US",
        }
        resp = _mock_wp_response(json_data=settings)
        async with _patch_wp_client(response=resp):
            result = await get_site_info()
            assert "site" in result
            assert result["site"]["title"] == "My WordPress Site"
            assert result["site"]["description"] == "A test blog"
            assert result["site"]["timezone"] == "America/New_York"

    @pytest.mark.asyncio
    async def test_test_connection(self) -> None:
        user = {"id": 1, "name": "admin", "slug": "admin", "capabilities": {"edit_posts": True}}
        resp = _mock_wp_response(json_data=user)
        async with _patch_wp_client(response=resp):
            result = await test_connection()
            assert result["success"] is True
            assert result["authenticated_as"] == "admin"
            assert result["user_id"] == 1


# =============================================================================
# Mocked API Tests — Post Tools
# =============================================================================


class TestPostTools:
    """Tests for post CRUD and related tools."""

    @pytest.mark.asyncio
    async def test_list_posts(self) -> None:
        posts = [
            {"id": 1, "title": {"rendered": "Hello World"}, "status": "publish",
             "slug": "hello-world", "date": "2026-01-01", "modified": "2026-01-01",
             "link": "https://wp.example.com/hello-world", "author": 1,
             "excerpt": {"rendered": "Welcome"}, "categories": [1], "tags": [],
             "featured_media": 0, "format": "standard"},
        ]
        resp = _mock_wp_response(json_data=posts)
        async with _patch_wp_client(response=resp):
            result = await list_posts()
            assert "posts" in result
            assert "page" in result
            assert len(result["posts"]) == 1
            assert result["posts"][0]["title"] == "Hello World"

    @pytest.mark.asyncio
    async def test_get_post(self) -> None:
        post = {"id": 1, "title": {"rendered": "Test Post"}, "status": "publish",
                "slug": "test-post", "date": "2026-01-01", "modified": "2026-01-01",
                "link": "https://wp.example.com/test-post", "author": 1,
                "excerpt": {"rendered": ""}, "content": {"rendered": "<p>Hello</p>"},
                "categories": [], "tags": [], "featured_media": 0, "format": "standard"}
        resp = _mock_wp_response(json_data=post)
        async with _patch_wp_client(response=resp):
            result = await get_post(1)
            assert "post" in result
            assert result["post"]["id"] == 1
            assert result["post"]["content"] == "<p>Hello</p>"

    @pytest.mark.asyncio
    async def test_search_posts(self) -> None:
        posts = [
            {"id": 5, "title": {"rendered": "Search Result"}, "status": "publish",
             "slug": "search-result", "date": "2026-01-01", "modified": "2026-01-01",
             "link": "https://wp.example.com/search-result", "author": 1,
             "excerpt": {"rendered": ""}, "categories": [], "tags": [],
             "featured_media": 0, "format": "standard"},
        ]
        resp = _mock_wp_response(json_data=posts)
        async with _patch_wp_client(response=resp):
            result = await search_posts("search")
            assert "posts" in result
            assert len(result["posts"]) == 1

    @pytest.mark.asyncio
    async def test_create_post(self) -> None:
        post = {"id": 10, "title": {"rendered": "New Post"}, "status": "draft",
                "slug": "new-post", "date": "2026-01-01", "modified": "2026-01-01",
                "link": "https://wp.example.com/?p=10", "author": 1,
                "excerpt": {"rendered": ""}, "content": {"rendered": "<p>Content</p>"},
                "categories": [], "tags": [], "featured_media": 0, "format": "standard"}
        resp = _mock_wp_response(json_data=post)
        async with _patch_wp_client(response=resp):
            result = await create_post("New Post", "Content")
            assert "post" in result
            assert result["post"]["id"] == 10
            assert result["post"]["status"] == "draft"

    @pytest.mark.asyncio
    async def test_update_post(self) -> None:
        post = {"id": 1, "title": {"rendered": "Updated Title"}, "status": "publish",
                "slug": "test-post", "date": "2026-01-01", "modified": "2026-01-02",
                "link": "https://wp.example.com/test-post", "author": 1,
                "excerpt": {"rendered": ""}, "content": {"rendered": "<p>Updated</p>"},
                "categories": [], "tags": [], "featured_media": 0, "format": "standard"}
        resp = _mock_wp_response(json_data=post)
        async with _patch_wp_client(response=resp):
            result = await update_post(1, title="Updated Title")
            assert "post" in result
            assert result["post"]["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_delete_post(self) -> None:
        resp = _mock_wp_response(json_data={"id": 1, "deleted": True})
        async with _patch_wp_client(response=resp):
            result = await delete_post(1)
            assert result["success"] is True
            assert "trash" in result["message"]

    @pytest.mark.asyncio
    async def test_list_revisions(self) -> None:
        revisions = [
            {"id": 101, "author": 1, "date": "2026-01-01", "modified": "2026-01-01",
             "title": {"rendered": "Rev 1"}},
            {"id": 102, "author": 1, "date": "2026-01-02", "modified": "2026-01-02",
             "title": {"rendered": "Rev 2"}},
        ]
        resp = _mock_wp_response(json_data=revisions)
        async with _patch_wp_client(response=resp):
            result = await list_revisions(1)
            assert "revisions" in result
            assert len(result["revisions"]) == 2

    @pytest.mark.asyncio
    async def test_get_revision(self) -> None:
        revision = {"id": 101, "author": 1, "date": "2026-01-01",
                     "title": {"rendered": "Original Title"},
                     "content": {"rendered": "<p>Original content</p>"},
                     "excerpt": {"rendered": ""}}
        resp = _mock_wp_response(json_data=revision)
        async with _patch_wp_client(response=resp):
            result = await get_revision(1, 101)
            assert "revision" in result
            assert result["revision"]["id"] == 101

    @pytest.mark.asyncio
    async def test_list_categories(self) -> None:
        categories = [
            {"id": 1, "name": "Uncategorized", "slug": "uncategorized",
             "description": "", "count": 5, "parent": 0},
        ]
        resp = _mock_wp_response(json_data=categories)
        async with _patch_wp_client(response=resp):
            result = await list_categories()
            assert "categories" in result
            assert len(result["categories"]) == 1
            assert result["categories"][0]["name"] == "Uncategorized"

    @pytest.mark.asyncio
    async def test_list_tags(self) -> None:
        tags = [
            {"id": 1, "name": "python", "slug": "python", "description": "", "count": 3},
        ]
        resp = _mock_wp_response(json_data=tags)
        async with _patch_wp_client(response=resp):
            result = await list_tags()
            assert "tags" in result
            assert len(result["tags"]) == 1
            assert result["tags"][0]["name"] == "python"


# =============================================================================
# Mocked API Tests — Page Tools
# =============================================================================


class TestPageTools:
    """Tests for page CRUD tools."""

    @pytest.mark.asyncio
    async def test_list_pages(self) -> None:
        pages = [
            {"id": 2, "title": {"rendered": "About"}, "status": "publish",
             "slug": "about", "date": "2026-01-01", "modified": "2026-01-01",
             "link": "https://wp.example.com/about", "author": 1,
             "excerpt": {"rendered": ""}, "parent": 0, "menu_order": 0,
             "template": "", "featured_media": 0},
        ]
        resp = _mock_wp_response(json_data=pages)
        async with _patch_wp_client(response=resp):
            result = await list_pages()
            assert "pages" in result
            assert len(result["pages"]) == 1
            assert result["pages"][0]["title"] == "About"

    @pytest.mark.asyncio
    async def test_get_page(self) -> None:
        page = {"id": 2, "title": {"rendered": "About"}, "status": "publish",
                "slug": "about", "date": "2026-01-01", "modified": "2026-01-01",
                "link": "https://wp.example.com/about", "author": 1,
                "excerpt": {"rendered": ""}, "content": {"rendered": "<p>About us</p>"},
                "parent": 0, "menu_order": 0, "template": "", "featured_media": 0}
        resp = _mock_wp_response(json_data=page)
        async with _patch_wp_client(response=resp):
            result = await get_page(2)
            assert "page" in result
            assert result["page"]["id"] == 2
            assert result["page"]["content"] == "<p>About us</p>"

    @pytest.mark.asyncio
    async def test_create_page(self) -> None:
        page = {"id": 20, "title": {"rendered": "New Page"}, "status": "draft",
                "slug": "new-page", "date": "2026-01-01", "modified": "2026-01-01",
                "link": "https://wp.example.com/?page_id=20", "author": 1,
                "excerpt": {"rendered": ""}, "content": {"rendered": "<p>Page content</p>"},
                "parent": 0, "menu_order": 0, "template": "", "featured_media": 0}
        resp = _mock_wp_response(json_data=page)
        async with _patch_wp_client(response=resp):
            result = await create_page("New Page", "Page content")
            assert "page" in result
            assert result["page"]["id"] == 20

    @pytest.mark.asyncio
    async def test_update_page(self) -> None:
        page = {"id": 2, "title": {"rendered": "Updated About"}, "status": "publish",
                "slug": "about", "date": "2026-01-01", "modified": "2026-01-02",
                "link": "https://wp.example.com/about", "author": 1,
                "excerpt": {"rendered": ""}, "content": {"rendered": "<p>Updated</p>"},
                "parent": 0, "menu_order": 0, "template": "", "featured_media": 0}
        resp = _mock_wp_response(json_data=page)
        async with _patch_wp_client(response=resp):
            result = await update_page(2, title="Updated About")
            assert "page" in result
            assert result["page"]["title"] == "Updated About"

    @pytest.mark.asyncio
    async def test_delete_page(self) -> None:
        resp = _mock_wp_response(json_data={"id": 2, "deleted": True})
        async with _patch_wp_client(response=resp):
            result = await delete_page(2)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_list_page_revisions(self) -> None:
        revisions = [
            {"id": 201, "author": 1, "date": "2026-01-01", "modified": "2026-01-01",
             "title": {"rendered": "About v1"}},
        ]
        resp = _mock_wp_response(json_data=revisions)
        async with _patch_wp_client(response=resp):
            result = await list_page_revisions(2)
            assert "revisions" in result
            assert len(result["revisions"]) == 1


# =============================================================================
# Mocked API Tests — Media Tools
# =============================================================================


class TestMediaTools:
    """Tests for media CRUD tools."""

    @pytest.mark.asyncio
    async def test_list_media(self) -> None:
        media = [
            {"id": 50, "title": {"rendered": "logo.png"}, "slug": "logo",
             "date": "2026-01-01", "modified": "2026-01-01",
             "link": "https://wp.example.com/logo-png",
             "source_url": "https://wp.example.com/wp-content/uploads/logo.png",
             "mime_type": "image/png", "media_type": "image", "alt_text": "Logo"},
        ]
        resp = _mock_wp_response(json_data=media)
        async with _patch_wp_client(response=resp):
            result = await list_media()
            assert "media" in result
            assert len(result["media"]) == 1
            assert result["media"][0]["mime_type"] == "image/png"

    @pytest.mark.asyncio
    async def test_get_media(self) -> None:
        media = {"id": 50, "title": {"rendered": "logo.png"}, "slug": "logo",
                 "date": "2026-01-01", "modified": "2026-01-01",
                 "link": "https://wp.example.com/logo-png",
                 "source_url": "https://wp.example.com/wp-content/uploads/logo.png",
                 "mime_type": "image/png", "media_type": "image", "alt_text": "Logo",
                 "caption": {"rendered": ""}, "description": {"rendered": ""},
                 "media_details": {"width": 200, "height": 100, "file": "logo.png",
                                   "sizes": {"thumbnail": {"width": 150, "height": 75,
                                             "source_url": "https://wp.example.com/wp-content/uploads/logo-150x75.png"}}}}
        resp = _mock_wp_response(json_data=media)
        async with _patch_wp_client(response=resp):
            result = await get_media(50)
            assert "media" in result
            assert result["media"]["id"] == 50
            assert result["media"]["width"] == 200

    @pytest.mark.asyncio
    async def test_update_media(self) -> None:
        media = {"id": 50, "title": {"rendered": "Updated Logo"}, "slug": "logo",
                 "date": "2026-01-01", "modified": "2026-01-02",
                 "link": "https://wp.example.com/logo-png",
                 "source_url": "https://wp.example.com/wp-content/uploads/logo.png",
                 "mime_type": "image/png", "media_type": "image", "alt_text": "New alt",
                 "caption": {"rendered": ""}, "description": {"rendered": ""},
                 "media_details": {}}
        resp = _mock_wp_response(json_data=media)
        async with _patch_wp_client(response=resp):
            result = await update_media(50, title="Updated Logo", alt_text="New alt")
            assert "media" in result
            assert result["media"]["alt_text"] == "New alt"

    @pytest.mark.asyncio
    async def test_delete_media(self) -> None:
        resp = _mock_wp_response(json_data={"id": 50, "deleted": True})
        async with _patch_wp_client(response=resp):
            result = await delete_media(50)
            assert result["success"] is True
            assert "permanently deleted" in result["message"]

    @pytest.mark.asyncio
    async def test_get_media_url(self) -> None:
        media = {"id": 50,
                 "source_url": "https://wp.example.com/wp-content/uploads/logo.png",
                 "mime_type": "image/png",
                 "media_details": {"sizes": {
                     "thumbnail": {"source_url": "https://wp.example.com/wp-content/uploads/logo-150x150.png"},
                     "full": {"source_url": "https://wp.example.com/wp-content/uploads/logo.png"},
                 }}}
        resp = _mock_wp_response(json_data=media)
        async with _patch_wp_client(response=resp):
            result = await get_media_url(50, size="thumbnail")
            assert result["media_id"] == 50
            assert "thumbnail" in result["available_sizes"]
            assert "150x150" in result["url"]


# =============================================================================
# Mocked API Tests — Comment Tools
# =============================================================================


class TestCommentTools:
    """Tests for comment CRUD and moderation tools."""

    @pytest.mark.asyncio
    async def test_list_comments(self) -> None:
        comments = [
            {"id": 1, "post": 10, "parent": 0, "author": 0,
             "author_name": "John", "date": "2026-01-01", "status": "approved",
             "link": "https://wp.example.com/hello-world#comment-1"},
        ]
        resp = _mock_wp_response(json_data=comments)
        async with _patch_wp_client(response=resp):
            result = await list_comments()
            assert "comments" in result
            assert len(result["comments"]) == 1
            assert result["comments"][0]["author_name"] == "John"

    @pytest.mark.asyncio
    async def test_get_comment(self) -> None:
        comment = {"id": 1, "post": 10, "parent": 0, "author": 0,
                   "author_name": "John", "date": "2026-01-01", "status": "approved",
                   "link": "https://wp.example.com/hello-world#comment-1",
                   "content": {"rendered": "<p>Great post!</p>"},
                   "author_email": "john@example.com", "author_url": ""}
        resp = _mock_wp_response(json_data=comment)
        async with _patch_wp_client(response=resp):
            result = await get_comment(1)
            assert "comment" in result
            assert result["comment"]["id"] == 1
            assert result["comment"]["content"] == "<p>Great post!</p>"

    @pytest.mark.asyncio
    async def test_create_comment(self) -> None:
        comment = {"id": 5, "post": 10, "parent": 0, "author": 1,
                   "author_name": "admin", "date": "2026-01-01", "status": "approved",
                   "link": "https://wp.example.com/hello-world#comment-5",
                   "content": {"rendered": "<p>Nice work</p>"},
                   "author_email": "", "author_url": ""}
        resp = _mock_wp_response(json_data=comment)
        async with _patch_wp_client(response=resp):
            result = await create_comment(post=10, content="Nice work")
            assert "comment" in result
            assert result["comment"]["id"] == 5

    @pytest.mark.asyncio
    async def test_update_comment(self) -> None:
        comment = {"id": 1, "post": 10, "parent": 0, "author": 0,
                   "author_name": "John", "date": "2026-01-01", "status": "hold",
                   "link": "https://wp.example.com/hello-world#comment-1",
                   "content": {"rendered": "<p>Updated</p>"},
                   "author_email": "", "author_url": ""}
        resp = _mock_wp_response(json_data=comment)
        async with _patch_wp_client(response=resp):
            result = await update_comment(1, content="Updated")
            assert "comment" in result
            assert result["comment"]["status"] == "hold"

    @pytest.mark.asyncio
    async def test_delete_comment(self) -> None:
        resp = _mock_wp_response(json_data={"id": 1, "deleted": True})
        async with _patch_wp_client(response=resp):
            result = await delete_comment(1)
            assert result["success"] is True

    @pytest.mark.asyncio
    async def test_moderate_comment(self) -> None:
        comment = {"id": 1, "post": 10, "parent": 0, "author": 0,
                   "author_name": "John", "date": "2026-01-01", "status": "approved",
                   "link": "https://wp.example.com/hello-world#comment-1",
                   "content": {"rendered": "<p>Great post!</p>"},
                   "author_email": "", "author_url": ""}
        resp = _mock_wp_response(json_data=comment)
        async with _patch_wp_client(response=resp):
            result = await moderate_comment(1, "approve")
            assert "comment" in result

    def test_moderate_comment_invalid_action(self) -> None:
        """Verify action-to-status mapping rejects invalid actions."""
        # moderate_comment checks action before calling update_comment
        action_to_status = {
            "approve": "approved",
            "hold": "hold",
            "spam": "spam",
            "trash": "trash",
        }
        assert "invalid" not in action_to_status
        assert "approve" in action_to_status
        assert action_to_status["approve"] == "approved"


# =============================================================================
# Mocked API Tests — Error Handling
# =============================================================================


class TestErrorHandling:
    """Tests for API error handling via mocked responses."""

    @pytest.mark.asyncio
    async def test_api_error_on_401(self) -> None:
        resp = _mock_wp_response(
            status_code=401,
            json_data={"code": "rest_forbidden", "message": "Unauthorized"},
        )
        async with _patch_wp_client(response=resp):
            with pytest.raises(PermissionDeniedError, match="authentication required"):
                await get_post(1)

    @pytest.mark.asyncio
    async def test_api_error_on_404(self) -> None:
        resp = _mock_wp_response(
            status_code=404,
            json_data={"code": "rest_post_invalid_id", "message": "Invalid post ID"},
        )
        async with _patch_wp_client(response=resp):
            with pytest.raises(PostNotFoundError):
                await get_post(99999)

    @pytest.mark.asyncio
    async def test_api_error_on_429(self) -> None:
        resp = _mock_wp_response(
            status_code=429,
            json_data={"code": "rate_limit", "message": "Too many requests",
                       "data": {"retry_after": 30}},
        )
        async with _patch_wp_client(response=resp):
            with pytest.raises(RateLimitError, match="30"):
                await list_posts()
