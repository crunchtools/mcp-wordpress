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
POST_FORMATS = frozenset({
    "standard", "aside", "chat", "gallery", "link",
    "image", "quote", "status", "video", "audio"
})


def validate_positive_id(value: int) -> int:
    """Validate that an ID is a positive integer."""
    if value <= 0:
        raise ValueError("ID must be a positive integer")
    return value


def validate_post_id(post_id: int) -> int:
    """Validate a post ID is a positive integer."""
    return validate_positive_id(post_id)


def validate_page_id(page_id: int) -> int:
    """Validate a page ID is a positive integer."""
    return validate_positive_id(page_id)


def validate_media_id(media_id: int) -> int:
    """Validate a media ID is a positive integer."""
    return validate_positive_id(media_id)


def validate_comment_id(comment_id: int) -> int:
    """Validate a comment ID is a positive integer."""
    return validate_positive_id(comment_id)


class PostInput(BaseModel):
    """Validated post input for creation."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ..., min_length=1, max_length=500, description="Post title"
    )
    content: str = Field(
        ..., min_length=1, description="Post content (HTML or Markdown)"
    )
    status: Literal["publish", "future", "draft", "pending", "private"] = Field(
        default="draft", description="Post status"
    )
    excerpt: str | None = Field(
        default=None, max_length=1000, description="Post excerpt"
    )
    slug: str | None = Field(
        default=None, max_length=200, description="Post slug for URL"
    )
    categories: list[int] | None = Field(
        default=None, description="List of category IDs"
    )
    tags: list[int] | None = Field(
        default=None, description="List of tag IDs"
    )
    featured_media: int | None = Field(
        default=None, ge=0, description="Featured image media ID"
    )
    date: str | None = Field(
        default=None, description="Publication date (ISO 8601 format for scheduling)"
    )
    format: str | None = Field(
        default=None, description="Post format (standard, aside, gallery, etc.)"
    )

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v_lower = v.lower()
        if v_lower not in POST_FORMATS:
            allowed = ", ".join(sorted(POST_FORMATS))
            raise ValueError(f"Invalid post format. Allowed: {allowed}")
        return v_lower


class PostUpdateInput(BaseModel):
    """Validated post input for updates."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None, min_length=1, max_length=500, description="Post title"
    )
    content: str | None = Field(
        default=None, description="Post content"
    )
    status: Literal["publish", "future", "draft", "pending", "private"] | None = Field(
        default=None, description="Post status"
    )
    excerpt: str | None = Field(
        default=None, max_length=1000, description="Post excerpt"
    )
    slug: str | None = Field(
        default=None, max_length=200, description="Post slug"
    )
    categories: list[int] | None = Field(
        default=None, description="List of category IDs"
    )
    tags: list[int] | None = Field(
        default=None, description="List of tag IDs"
    )
    featured_media: int | None = Field(
        default=None, ge=0, description="Featured image media ID"
    )
    date: str | None = Field(
        default=None, description="Publication date (ISO 8601)"
    )
    format: str | None = Field(
        default=None, description="Post format"
    )

    @field_validator("format")
    @classmethod
    def validate_format(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v_lower = v.lower()
        if v_lower not in POST_FORMATS:
            allowed = ", ".join(sorted(POST_FORMATS))
            raise ValueError(f"Invalid post format. Allowed: {allowed}")
        return v_lower


class PageInput(BaseModel):
    """Validated page input for creation."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(
        ..., min_length=1, max_length=500, description="Page title"
    )
    content: str = Field(
        ..., min_length=1, description="Page content (HTML or Markdown)"
    )
    status: Literal["publish", "future", "draft", "pending", "private"] = Field(
        default="draft", description="Page status"
    )
    excerpt: str | None = Field(
        default=None, max_length=1000, description="Page excerpt"
    )
    slug: str | None = Field(
        default=None, max_length=200, description="Page slug for URL"
    )
    parent: int | None = Field(
        default=None, ge=0, description="Parent page ID"
    )
    menu_order: int | None = Field(
        default=None, ge=0, description="Menu order"
    )
    template: str | None = Field(
        default=None, max_length=200, description="Page template"
    )
    featured_media: int | None = Field(
        default=None, ge=0, description="Featured image media ID"
    )
    date: str | None = Field(
        default=None, description="Publication date (ISO 8601 format)"
    )


class PageUpdateInput(BaseModel):
    """Validated page input for updates."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None, min_length=1, max_length=500, description="Page title"
    )
    content: str | None = Field(
        default=None, description="Page content"
    )
    status: Literal["publish", "future", "draft", "pending", "private"] | None = Field(
        default=None, description="Page status"
    )
    excerpt: str | None = Field(
        default=None, max_length=1000, description="Page excerpt"
    )
    slug: str | None = Field(
        default=None, max_length=200, description="Page slug"
    )
    parent: int | None = Field(
        default=None, ge=0, description="Parent page ID"
    )
    menu_order: int | None = Field(
        default=None, ge=0, description="Menu order"
    )
    template: str | None = Field(
        default=None, max_length=200, description="Page template"
    )
    featured_media: int | None = Field(
        default=None, ge=0, description="Featured image media ID"
    )
    date: str | None = Field(
        default=None, description="Publication date (ISO 8601)"
    )


class MediaInput(BaseModel):
    """Validated media input for upload."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None, max_length=500, description="Media title"
    )
    alt_text: str | None = Field(
        default=None, max_length=500, description="Alt text for accessibility"
    )
    caption: str | None = Field(
        default=None, max_length=2000, description="Media caption"
    )
    description: str | None = Field(
        default=None, description="Media description"
    )


class MediaUpdateInput(BaseModel):
    """Validated media input for updates."""

    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(
        default=None, max_length=500, description="Media title"
    )
    alt_text: str | None = Field(
        default=None, max_length=500, description="Alt text"
    )
    caption: str | None = Field(
        default=None, max_length=2000, description="Caption"
    )
    description: str | None = Field(
        default=None, description="Description"
    )


class CommentInput(BaseModel):
    """Validated comment input for creation."""

    model_config = ConfigDict(extra="forbid")

    post: int = Field(
        ..., ge=1, description="Post ID to comment on"
    )
    content: str = Field(
        ..., min_length=1, max_length=10000, description="Comment content"
    )
    parent: int | None = Field(
        default=None, ge=0, description="Parent comment ID for replies"
    )
    author_name: str | None = Field(
        default=None, max_length=100, description="Comment author name"
    )
    author_email: str | None = Field(
        default=None, max_length=200, description="Comment author email"
    )


class CommentUpdateInput(BaseModel):
    """Validated comment input for updates."""

    model_config = ConfigDict(extra="forbid")

    content: str | None = Field(
        default=None, min_length=1, max_length=10000, description="Comment content"
    )
    status: Literal["approved", "hold", "spam", "trash"] | None = Field(
        default=None, description="Comment status"
    )
