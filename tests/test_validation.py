"""Tests for Pydantic model validation."""

import pytest
from pydantic import ValidationError

from mcp_wordpress_crunchtools.models import (
    CommentInput,
    CommentUpdateInput,
    MediaInput,
    MediaUpdateInput,
    PageInput,
    PageUpdateInput,
    PostInput,
    PostUpdateInput,
    validate_comment_id,
    validate_media_id,
    validate_page_id,
    validate_post_id,
)


class TestIdValidation:
    """Tests for ID validation functions."""

    def test_validate_post_id_valid(self) -> None:
        """Test valid post ID."""
        assert validate_post_id(1) == 1
        assert validate_post_id(100) == 100
        assert validate_post_id(999999) == 999999

    def test_validate_post_id_invalid(self) -> None:
        """Test invalid post ID."""
        with pytest.raises(ValueError, match="positive integer"):
            validate_post_id(0)
        with pytest.raises(ValueError, match="positive integer"):
            validate_post_id(-1)

    def test_validate_page_id_valid(self) -> None:
        """Test valid page ID."""
        assert validate_page_id(1) == 1
        assert validate_page_id(42) == 42

    def test_validate_page_id_invalid(self) -> None:
        """Test invalid page ID."""
        with pytest.raises(ValueError, match="positive integer"):
            validate_page_id(0)

    def test_validate_media_id_valid(self) -> None:
        """Test valid media ID."""
        assert validate_media_id(1) == 1

    def test_validate_media_id_invalid(self) -> None:
        """Test invalid media ID."""
        with pytest.raises(ValueError, match="positive integer"):
            validate_media_id(-5)

    def test_validate_comment_id_valid(self) -> None:
        """Test valid comment ID."""
        assert validate_comment_id(1) == 1

    def test_validate_comment_id_invalid(self) -> None:
        """Test invalid comment ID."""
        with pytest.raises(ValueError, match="positive integer"):
            validate_comment_id(0)


class TestPostInput:
    """Tests for PostInput model."""

    def test_valid_minimal_post(self) -> None:
        """Test minimal valid post input."""
        post = PostInput(title="Test Post", content="Hello world")
        assert post.title == "Test Post"
        assert post.content == "Hello world"
        assert post.status == "draft"

    def test_valid_full_post(self) -> None:
        """Test full valid post input."""
        post = PostInput(
            title="Test Post",
            content="Hello world",
            status="publish",
            excerpt="Short summary",
            slug="test-post",
            categories=[1, 2, 3],
            tags=[4, 5],
            featured_media=10,
            date="2024-12-25T10:00:00",
            format="standard",
        )
        assert post.status == "publish"
        assert post.categories == [1, 2, 3]
        assert post.format == "standard"

    def test_invalid_status(self) -> None:
        """Test invalid post status."""
        with pytest.raises(ValidationError):
            PostInput(title="Test", content="Content", status="invalid")  # type: ignore[arg-type]

    def test_empty_title(self) -> None:
        """Test empty title is rejected."""
        with pytest.raises(ValidationError):
            PostInput(title="", content="Content")

    def test_valid_post_format(self) -> None:
        """Test valid post formats."""
        for fmt in ["standard", "aside", "gallery", "link", "image", "quote"]:
            post = PostInput(title="Test", content="Content", format=fmt)
            assert post.format == fmt

    def test_invalid_post_format(self) -> None:
        """Test invalid post format."""
        with pytest.raises(ValidationError, match="Invalid post format"):
            PostInput(title="Test", content="Content", format="invalid")


class TestPostUpdateInput:
    """Tests for PostUpdateInput model."""

    def test_empty_update(self) -> None:
        """Test empty update (all fields optional)."""
        update = PostUpdateInput()
        assert update.title is None
        assert update.content is None

    def test_partial_update(self) -> None:
        """Test partial update."""
        update = PostUpdateInput(title="New Title", status="publish")
        assert update.title == "New Title"
        assert update.status == "publish"
        assert update.content is None


class TestPageInput:
    """Tests for PageInput model."""

    def test_valid_minimal_page(self) -> None:
        """Test minimal valid page input."""
        page = PageInput(title="Test Page", content="Page content")
        assert page.title == "Test Page"
        assert page.status == "draft"

    def test_valid_full_page(self) -> None:
        """Test full valid page input."""
        page = PageInput(
            title="Test Page",
            content="Page content",
            status="publish",
            parent=5,
            menu_order=10,
            template="full-width.php",
        )
        assert page.parent == 5
        assert page.menu_order == 10
        assert page.template == "full-width.php"


class TestPageUpdateInput:
    """Tests for PageUpdateInput model."""

    def test_partial_update(self) -> None:
        """Test partial page update."""
        update = PageUpdateInput(menu_order=5, template="sidebar.php")
        assert update.menu_order == 5
        assert update.template == "sidebar.php"


class TestMediaInput:
    """Tests for MediaInput model."""

    def test_valid_media_input(self) -> None:
        """Test valid media input."""
        media = MediaInput(
            title="My Image",
            alt_text="A beautiful sunset",
            caption="Sunset over the mountains",
        )
        assert media.title == "My Image"
        assert media.alt_text == "A beautiful sunset"

    def test_empty_media_input(self) -> None:
        """Test all fields optional."""
        media = MediaInput()
        assert media.title is None


class TestMediaUpdateInput:
    """Tests for MediaUpdateInput model."""

    def test_partial_update(self) -> None:
        """Test partial media update."""
        update = MediaUpdateInput(alt_text="New alt text")
        assert update.alt_text == "New alt text"
        assert update.title is None


class TestCommentInput:
    """Tests for CommentInput model."""

    def test_valid_comment(self) -> None:
        """Test valid comment input."""
        comment = CommentInput(post=1, content="Great article!")
        assert comment.post == 1
        assert comment.content == "Great article!"

    def test_comment_with_parent(self) -> None:
        """Test comment reply."""
        comment = CommentInput(post=1, content="Reply", parent=5)
        assert comment.parent == 5

    def test_anonymous_comment(self) -> None:
        """Test anonymous comment."""
        comment = CommentInput(
            post=1,
            content="Anonymous comment",
            author_name="John Doe",
            author_email="john@example.com",
        )
        assert comment.author_name == "John Doe"
        assert comment.author_email == "john@example.com"

    def test_invalid_post_id(self) -> None:
        """Test invalid post ID."""
        with pytest.raises(ValidationError):
            CommentInput(post=0, content="Test")


class TestCommentUpdateInput:
    """Tests for CommentUpdateInput model."""

    def test_valid_status_update(self) -> None:
        """Test valid status update."""
        for status in ["approved", "hold", "spam", "trash"]:
            update = CommentUpdateInput(status=status)  # type: ignore[arg-type]
            assert update.status == status

    def test_invalid_status(self) -> None:
        """Test invalid status."""
        with pytest.raises(ValidationError):
            CommentUpdateInput(status="invalid")  # type: ignore[arg-type]
