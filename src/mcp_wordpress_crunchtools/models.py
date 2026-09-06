"""Pydantic models for input validation.

All tool inputs are validated through these models to prevent injection attacks
and ensure data integrity before making API calls.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Valid post/page statuses
POST_STATUSES = frozenset({"publish", "future", "draft", "pending", "private"})
PAGE_STATUSES = frozenset({"publish", "future", "draft", "pending", "private"})

# Valid comment statuses
COMMENT_STATUSES = frozenset({"approved", "hold", "spam", "trash"})

# Valid post formats
POST_FORMATS = frozenset(
    {"standard", "aside", "chat", "gallery", "link", "image", "quote", "status", "video", "audio"}
)


MAX_TITLE = 500
MAX_EXCERPT = 1000
MAX_SLUG = 200
MAX_COMMENT_AUTHOR = 200
MAX_COMMENT_CONTENT = 2000
MAX_ALT_TEXT = 500
MAX_CAPTION = 10000


def validate_post_format(post_format: str) -> str:
    """Normalise a post format to lower case and check it is supported."""
    lowered = post_format.lower()
    if lowered not in POST_FORMATS:
        allowed = ", ".join(sorted(POST_FORMATS))
        raise ValueError(f"Invalid post format. Allowed: {allowed}")
    return lowered


def validate_positive_id(value: int) -> int:
    """Validate that an ID is a positive integer."""
    if value <= 0:
        raise ValueError("ID must be a positive integer")
    return value


class PostInput(BaseModel):
    """Validated post input for creation."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=MAX_TITLE, description="Post title")
    content: str = Field(..., min_length=1, description="Post content (HTML or Markdown)")
    status: Literal["publish", "future", "draft", "pending", "private"] = Field(
        default="draft", description="Post status"
    )
    excerpt: str | None = Field(default=None, max_length=MAX_EXCERPT, description="Post excerpt")
    slug: str | None = Field(default=None, max_length=MAX_SLUG, description="Post slug for URL")
    categories: list[int] | None = Field(default=None, description="List of category IDs")
    tags: list[int] | None = Field(default=None, description="List of tag IDs")
    featured_media: int | None = Field(default=None, ge=0, description="Featured image media ID")
    date: str | None = Field(
        default=None, description="Publication date (ISO 8601 format for scheduling)"
    )
    format: str | None = Field(
        default=None, description="Post format (standard, aside, gallery, etc.)"
    )

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str | None) -> str | None:
        return None if v is None else validate_post_format(v)


class PostUpdateInput(BaseModel):
    """Validated post input for updates."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None, min_length=1, max_length=MAX_TITLE, description="Post title"
    )
    content: str | None = Field(default=None, description="Post content")
    status: Literal["publish", "future", "draft", "pending", "private"] | None = Field(
        default=None, description="Post status"
    )
    excerpt: str | None = Field(default=None, max_length=MAX_EXCERPT, description="Post excerpt")
    slug: str | None = Field(default=None, max_length=MAX_SLUG, description="Post slug")
    categories: list[int] | None = Field(default=None, description="List of category IDs")
    tags: list[int] | None = Field(default=None, description="List of tag IDs")
    featured_media: int | None = Field(default=None, ge=0, description="Featured image media ID")
    date: str | None = Field(default=None, description="Publication date (ISO 8601)")
    format: str | None = Field(default=None, description="Post format")

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str | None) -> str | None:
        return None if v is None else validate_post_format(v)


class PageInput(BaseModel):
    """Validated page input for creation."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(..., min_length=1, max_length=MAX_TITLE, description="Page title")
    content: str = Field(..., min_length=1, description="Page content (HTML or Markdown)")
    status: Literal["publish", "future", "draft", "pending", "private"] = Field(
        default="draft", description="Page status"
    )
    excerpt: str | None = Field(default=None, max_length=MAX_EXCERPT, description="Page excerpt")
    slug: str | None = Field(default=None, max_length=MAX_SLUG, description="Page slug for URL")
    parent: int | None = Field(default=None, ge=0, description="Parent page ID")
    menu_order: int | None = Field(default=None, ge=0, description="Menu order")
    template: str | None = Field(default=None, max_length=MAX_SLUG, description="Page template")
    featured_media: int | None = Field(default=None, ge=0, description="Featured image media ID")
    date: str | None = Field(default=None, description="Publication date (ISO 8601 format)")


class PageUpdateInput(BaseModel):
    """Validated page input for updates."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None, min_length=1, max_length=MAX_TITLE, description="Page title"
    )
    content: str | None = Field(default=None, description="Page content")
    status: Literal["publish", "future", "draft", "pending", "private"] | None = Field(
        default=None, description="Page status"
    )
    excerpt: str | None = Field(default=None, max_length=MAX_EXCERPT, description="Page excerpt")
    slug: str | None = Field(default=None, max_length=MAX_SLUG, description="Page slug")
    parent: int | None = Field(default=None, ge=0, description="Parent page ID")
    menu_order: int | None = Field(default=None, ge=0, description="Menu order")
    template: str | None = Field(default=None, max_length=MAX_SLUG, description="Page template")
    featured_media: int | None = Field(default=None, ge=0, description="Featured image media ID")
    date: str | None = Field(default=None, description="Publication date (ISO 8601)")


class MediaInput(BaseModel):
    """Validated media input for upload."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=MAX_TITLE, description="Media title")
    alt_text: str | None = Field(
        default=None, max_length=MAX_TITLE, description="Alt text for accessibility"
    )
    caption: str | None = Field(
        default=None, max_length=MAX_COMMENT_CONTENT, description="Media caption"
    )
    description: str | None = Field(default=None, description="Media description")


class MediaUpdateInput(BaseModel):
    """Validated media input for updates."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, max_length=MAX_TITLE, description="Media title")
    alt_text: str | None = Field(default=None, max_length=MAX_TITLE, description="Alt text")
    caption: str | None = Field(default=None, max_length=MAX_COMMENT_CONTENT, description="Caption")
    description: str | None = Field(default=None, description="Description")


class CommentInput(BaseModel):
    """Validated comment input for creation."""

    model_config = ConfigDict(extra="forbid")

    post: int = Field(..., ge=1, description="Post ID to comment on")
    content: str = Field(..., min_length=1, max_length=MAX_CAPTION, description="Comment content")
    parent: int | None = Field(default=None, ge=0, description="Parent comment ID for replies")
    author_name: str | None = Field(default=None, max_length=100, description="Comment author name")
    author_email: str | None = Field(
        default=None, max_length=MAX_SLUG, description="Comment author email"
    )


class CommentUpdateInput(BaseModel):
    """Validated comment input for updates."""

    model_config = ConfigDict(extra="forbid")

    content: str | None = Field(
        default=None, min_length=1, max_length=MAX_CAPTION, description="Comment content"
    )
    status: Literal["approved", "hold", "spam", "trash"] | None = Field(
        default=None, description="Comment status"
    )
