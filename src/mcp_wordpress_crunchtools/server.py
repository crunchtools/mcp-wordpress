"""FastMCP server setup for WordPress MCP.

This module creates and configures the MCP server with all tools.
"""

import logging
from typing import Any

from fastmcp import FastMCP

from .tools import (
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

logger = logging.getLogger(__name__)

# Create the FastMCP server
mcp = FastMCP(
    name="mcp-wordpress-crunchtools",
    version="0.1.0",
    instructions="Secure MCP server for WordPress content management",
)


# =============================================================================
# Site Tools
# =============================================================================


@mcp.tool()
async def wordpress_get_site_info() -> dict[str, Any]:
    """Get WordPress site information.

    Returns site title, description, URL, timezone, and other settings.
    """
    return await get_site_info()


@mcp.tool()
async def wordpress_test_connection() -> dict[str, Any]:
    """Test connection to WordPress REST API.

    Verifies API credentials and returns connection status.
    """
    return await test_connection()


# =============================================================================
# Post Tools
# =============================================================================


@mcp.tool()
async def wordpress_list_posts(
    status: str | None = None,
    search: str | None = None,
    categories: list[int] | None = None,
    tags: list[int] | None = None,
    page: int = 1,
    per_page: int = 10,
    orderby: str = "date",
    order: str = "desc",
) -> dict[str, Any]:
    """List WordPress posts with filtering and pagination.

    Args:
        status: Filter by status (publish, draft, pending, private, future)
        search: Search posts by keyword
        categories: Filter by category IDs
        tags: Filter by tag IDs
        page: Page number (default: 1)
        per_page: Results per page, max 100 (default: 10)
        orderby: Sort by field (date, title, id, modified)
        order: Sort direction (asc, desc)

    Returns:
        List of posts with pagination info
    """
    return await list_posts(
        status=status,
        search=search,
        categories=categories,
        tags=tags,
        page=page,
        per_page=per_page,
        orderby=orderby,
        order=order,
    )


@mcp.tool()
async def wordpress_get_post(post_id: int) -> dict[str, Any]:
    """Get a single WordPress post by ID with full content.

    Args:
        post_id: Post ID

    Returns:
        Full post details including content
    """
    return await get_post(post_id=post_id)


@mcp.tool()
async def wordpress_search_posts(
    keyword: str,
    page: int = 1,
    per_page: int = 10,
) -> dict[str, Any]:
    """Search WordPress posts by keyword in title and content.

    Args:
        keyword: Search keyword
        page: Page number (default: 1)
        per_page: Results per page (default: 10)

    Returns:
        Search results
    """
    return await search_posts(keyword=keyword, page=page, per_page=per_page)


@mcp.tool()
async def wordpress_create_post(
    title: str,
    content: str,
    status: str = "draft",
    excerpt: str | None = None,
    slug: str | None = None,
    categories: list[int] | None = None,
    tags: list[int] | None = None,
    featured_media: int | None = None,
    date: str | None = None,
    post_format: str | None = None,
) -> dict[str, Any]:
    """Create a new WordPress post.

    Args:
        title: Post title
        content: Post content (HTML or block format)
        status: Post status - publish, draft, pending, private, future (default: draft)
        excerpt: Post excerpt
        slug: URL slug
        categories: List of category IDs
        tags: List of tag IDs
        featured_media: Featured image media ID
        date: Publication date (ISO 8601 for scheduling, e.g., 2024-12-25T10:00:00)
        post_format: Format - standard, aside, gallery, link, image, quote, status, video, audio

    Returns:
        Created post details
    """
    return await create_post(
        title=title,
        content=content,
        status=status,
        excerpt=excerpt,
        slug=slug,
        categories=categories,
        tags=tags,
        featured_media=featured_media,
        date=date,
        post_format=post_format,
    )


@mcp.tool()
async def wordpress_update_post(
    post_id: int,
    title: str | None = None,
    content: str | None = None,
    status: str | None = None,
    excerpt: str | None = None,
    slug: str | None = None,
    categories: list[int] | None = None,
    tags: list[int] | None = None,
    featured_media: int | None = None,
    date: str | None = None,
    post_format: str | None = None,
) -> dict[str, Any]:
    """Update an existing WordPress post.

    Args:
        post_id: Post ID to update
        title: New title
        content: New content
        status: New status
        excerpt: New excerpt
        slug: New slug
        categories: New category IDs
        tags: New tag IDs
        featured_media: New featured image ID
        date: New publication date
        post_format: New post format

    Returns:
        Updated post details
    """
    return await update_post(
        post_id=post_id,
        title=title,
        content=content,
        status=status,
        excerpt=excerpt,
        slug=slug,
        categories=categories,
        tags=tags,
        featured_media=featured_media,
        date=date,
        post_format=post_format,
    )


@mcp.tool()
async def wordpress_delete_post(post_id: int, force: bool = False) -> dict[str, Any]:
    """Delete or trash a WordPress post.

    Args:
        post_id: Post ID to delete
        force: If true, permanently delete. If false, move to trash.

    Returns:
        Deletion confirmation
    """
    return await delete_post(post_id=post_id, force=force)


@mcp.tool()
async def wordpress_list_revisions(post_id: int) -> dict[str, Any]:
    """List revisions for a WordPress post.

    Args:
        post_id: Post ID

    Returns:
        List of revisions
    """
    return await list_revisions(post_id=post_id)


@mcp.tool()
async def wordpress_get_revision(post_id: int, revision_id: int) -> dict[str, Any]:
    """Get a specific revision of a WordPress post.

    Args:
        post_id: Post ID
        revision_id: Revision ID

    Returns:
        Revision details with content
    """
    return await get_revision(post_id=post_id, revision_id=revision_id)


@mcp.tool()
async def wordpress_list_categories(
    page: int = 1,
    per_page: int = 100,
    search: str | None = None,
) -> dict[str, Any]:
    """List available WordPress categories.

    Args:
        page: Page number
        per_page: Results per page (max 100)
        search: Search categories by name

    Returns:
        List of categories
    """
    return await list_categories(page=page, per_page=per_page, search=search)


@mcp.tool()
async def wordpress_list_tags(
    page: int = 1,
    per_page: int = 100,
    search: str | None = None,
) -> dict[str, Any]:
    """List available WordPress tags.

    Args:
        page: Page number
        per_page: Results per page (max 100)
        search: Search tags by name

    Returns:
        List of tags
    """
    return await list_tags(page=page, per_page=per_page, search=search)


# =============================================================================
# Page Tools
# =============================================================================


@mcp.tool()
async def wordpress_list_pages(
    status: str | None = None,
    search: str | None = None,
    parent: int | None = None,
    page: int = 1,
    per_page: int = 10,
    orderby: str = "date",
    order: str = "desc",
) -> dict[str, Any]:
    """List WordPress pages with filtering and pagination.

    Args:
        status: Filter by status (publish, draft, pending, private, future)
        search: Search pages by keyword
        parent: Filter by parent page ID
        page: Page number (default: 1)
        per_page: Results per page, max 100 (default: 10)
        orderby: Sort by field (date, title, id, modified, menu_order)
        order: Sort direction (asc, desc)

    Returns:
        List of pages with pagination info
    """
    return await list_pages(
        status=status,
        search=search,
        parent=parent,
        page=page,
        per_page=per_page,
        orderby=orderby,
        order=order,
    )


@mcp.tool()
async def wordpress_get_page(page_id: int) -> dict[str, Any]:
    """Get a single WordPress page by ID with full content.

    Args:
        page_id: Page ID

    Returns:
        Full page details including content
    """
    return await get_page(page_id=page_id)


@mcp.tool()
async def wordpress_create_page(
    title: str,
    content: str,
    status: str = "draft",
    excerpt: str | None = None,
    slug: str | None = None,
    parent: int | None = None,
    menu_order: int | None = None,
    template: str | None = None,
    featured_media: int | None = None,
    date: str | None = None,
) -> dict[str, Any]:
    """Create a new WordPress page.

    Args:
        title: Page title
        content: Page content (HTML or block format)
        status: Page status - publish, draft, pending, private, future (default: draft)
        excerpt: Page excerpt
        slug: URL slug
        parent: Parent page ID
        menu_order: Menu order
        template: Page template file
        featured_media: Featured image media ID
        date: Publication date (ISO 8601)

    Returns:
        Created page details
    """
    return await create_page(
        title=title,
        content=content,
        status=status,
        excerpt=excerpt,
        slug=slug,
        parent=parent,
        menu_order=menu_order,
        template=template,
        featured_media=featured_media,
        date=date,
    )


@mcp.tool()
async def wordpress_update_page(
    page_id: int,
    title: str | None = None,
    content: str | None = None,
    status: str | None = None,
    excerpt: str | None = None,
    slug: str | None = None,
    parent: int | None = None,
    menu_order: int | None = None,
    template: str | None = None,
    featured_media: int | None = None,
    date: str | None = None,
) -> dict[str, Any]:
    """Update an existing WordPress page.

    Args:
        page_id: Page ID to update
        title: New title
        content: New content
        status: New status
        excerpt: New excerpt
        slug: New slug
        parent: New parent page ID
        menu_order: New menu order
        template: New template
        featured_media: New featured image ID
        date: New publication date

    Returns:
        Updated page details
    """
    return await update_page(
        page_id=page_id,
        title=title,
        content=content,
        status=status,
        excerpt=excerpt,
        slug=slug,
        parent=parent,
        menu_order=menu_order,
        template=template,
        featured_media=featured_media,
        date=date,
    )


@mcp.tool()
async def wordpress_delete_page(page_id: int, force: bool = False) -> dict[str, Any]:
    """Delete or trash a WordPress page.

    Args:
        page_id: Page ID to delete
        force: If true, permanently delete. If false, move to trash.

    Returns:
        Deletion confirmation
    """
    return await delete_page(page_id=page_id, force=force)


@mcp.tool()
async def wordpress_list_page_revisions(page_id: int) -> dict[str, Any]:
    """List revisions for a WordPress page.

    Args:
        page_id: Page ID

    Returns:
        List of revisions
    """
    return await list_page_revisions(page_id=page_id)


# =============================================================================
# Media Tools
# =============================================================================


@mcp.tool()
async def wordpress_list_media(
    media_type: str | None = None,
    mime_type: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 10,
    orderby: str = "date",
    order: str = "desc",
) -> dict[str, Any]:
    """List WordPress media items with filtering.

    Args:
        media_type: Filter by type (image, video, audio, application)
        mime_type: Filter by MIME type (e.g., image/jpeg)
        search: Search media by keyword
        page: Page number (default: 1)
        per_page: Results per page, max 100 (default: 10)
        orderby: Sort by field (date, title, id)
        order: Sort direction (asc, desc)

    Returns:
        List of media items with pagination info
    """
    return await list_media(
        media_type=media_type,
        mime_type=mime_type,
        search=search,
        page=page,
        per_page=per_page,
        orderby=orderby,
        order=order,
    )


@mcp.tool()
async def wordpress_get_media(media_id: int) -> dict[str, Any]:
    """Get a single WordPress media item by ID.

    Args:
        media_id: Media ID

    Returns:
        Media item details
    """
    return await get_media(media_id=media_id)


@mcp.tool()
async def wordpress_upload_media(
    file_path: str,
    title: str | None = None,
    alt_text: str | None = None,
    caption: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Upload a media file to WordPress from a local file path.

    The file is read directly from disk, avoiding large base64 payloads
    over the MCP protocol. Provide an absolute path to the file.

    Args:
        file_path: Absolute path to the file on disk (e.g., /tmp/image.png)
        title: Media title
        alt_text: Alt text for accessibility
        caption: Media caption
        description: Media description

    Returns:
        Uploaded media item details
    """
    return await upload_media(
        file_path=file_path,
        title=title,
        alt_text=alt_text,
        caption=caption,
        description=description,
    )


@mcp.tool()
async def wordpress_update_media(
    media_id: int,
    title: str | None = None,
    alt_text: str | None = None,
    caption: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Update WordPress media item metadata.

    Args:
        media_id: Media ID to update
        title: New title
        alt_text: New alt text
        caption: New caption
        description: New description

    Returns:
        Updated media item details
    """
    return await update_media(
        media_id=media_id,
        title=title,
        alt_text=alt_text,
        caption=caption,
        description=description,
    )


@mcp.tool()
async def wordpress_delete_media(media_id: int, force: bool = True) -> dict[str, Any]:
    """Delete a WordPress media item.

    Args:
        media_id: Media ID to delete
        force: Must be true for media (media cannot be trashed)

    Returns:
        Deletion confirmation
    """
    return await delete_media(media_id=media_id, force=force)


@mcp.tool()
async def wordpress_get_media_url(media_id: int, size: str = "full") -> dict[str, Any]:
    """Get the public URL for a WordPress media item.

    Args:
        media_id: Media ID
        size: Image size (thumbnail, medium, large, full)

    Returns:
        Media URL information
    """
    return await get_media_url(media_id=media_id, size=size)


# =============================================================================
# Comment Tools
# =============================================================================


@mcp.tool()
async def wordpress_list_comments(
    post: int | None = None,
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 10,
    orderby: str = "date",
    order: str = "desc",
) -> dict[str, Any]:
    """List WordPress comments with filtering.

    Args:
        post: Filter by post ID
        status: Filter by status (approved, hold, spam, trash)
        search: Search comments by content
        page: Page number (default: 1)
        per_page: Results per page, max 100 (default: 10)
        orderby: Sort by field (date, id)
        order: Sort direction (asc, desc)

    Returns:
        List of comments with pagination info
    """
    return await list_comments(
        post=post,
        status=status,
        search=search,
        page=page,
        per_page=per_page,
        orderby=orderby,
        order=order,
    )


@mcp.tool()
async def wordpress_get_comment(comment_id: int) -> dict[str, Any]:
    """Get a single WordPress comment by ID.

    Args:
        comment_id: Comment ID

    Returns:
        Comment details
    """
    return await get_comment(comment_id=comment_id)


@mcp.tool()
async def wordpress_create_comment(
    post: int,
    content: str,
    parent: int | None = None,
    author_name: str | None = None,
    author_email: str | None = None,
) -> dict[str, Any]:
    """Create a new comment on a WordPress post.

    Args:
        post: Post ID to comment on
        content: Comment content
        parent: Parent comment ID for replies
        author_name: Comment author name (for anonymous comments)
        author_email: Comment author email (for anonymous comments)

    Returns:
        Created comment details
    """
    return await create_comment(
        post=post,
        content=content,
        parent=parent,
        author_name=author_name,
        author_email=author_email,
    )


@mcp.tool()
async def wordpress_update_comment(
    comment_id: int,
    content: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Update an existing WordPress comment.

    Args:
        comment_id: Comment ID to update
        content: New comment content
        status: New status (approved, hold, spam, trash)

    Returns:
        Updated comment details
    """
    return await update_comment(
        comment_id=comment_id,
        content=content,
        status=status,
    )


@mcp.tool()
async def wordpress_delete_comment(
    comment_id: int, force: bool = False
) -> dict[str, Any]:
    """Delete or trash a WordPress comment.

    Args:
        comment_id: Comment ID to delete
        force: If true, permanently delete. If false, move to trash.

    Returns:
        Deletion confirmation
    """
    return await delete_comment(comment_id=comment_id, force=force)


@mcp.tool()
async def wordpress_moderate_comment(
    comment_id: int,
    action: str,
) -> dict[str, Any]:
    """Moderate a WordPress comment by changing its status.

    Args:
        comment_id: Comment ID to moderate
        action: Moderation action (approve, hold, spam, trash)

    Returns:
        Updated comment details
    """
    return await moderate_comment(comment_id=comment_id, action=action)
