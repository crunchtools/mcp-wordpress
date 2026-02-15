"""Post management tools.

Tools for creating, reading, updating, and deleting WordPress posts.
"""

from typing import Any

from ..client import get_client
from ..models import validate_post_id


async def list_posts(
    status: str | None = None,
    search: str | None = None,
    categories: list[int] | None = None,
    tags: list[int] | None = None,
    page: int = 1,
    per_page: int = 10,
    orderby: str = "date",
    order: str = "desc",
) -> dict[str, Any]:
    """List posts with filtering and pagination.

    Args:
        status: Filter by status (publish, draft, pending, private, future)
        search: Search posts by keyword
        categories: Filter by category IDs
        tags: Filter by tag IDs
        page: Page number for pagination
        per_page: Results per page (max 100)
        orderby: Sort by field (date, title, id, modified)
        order: Sort direction (asc, desc)

    Returns:
        Dictionary containing posts list and pagination info
    """
    client = get_client()

    params: dict[str, Any] = {
        "page": page,
        "per_page": min(per_page, 100),
        "orderby": orderby,
        "order": order,
        "_embed": "true",  # Include embedded data like featured images
    }

    if status:
        params["status"] = status
    if search:
        params["search"] = search
    if categories:
        params["categories"] = ",".join(str(c) for c in categories)
    if tags:
        params["tags"] = ",".join(str(t) for t in tags)

    response = await client.get("/posts", params=params)

    # Format response
    posts = []
    if isinstance(response, list):
        for post in response:
            posts.append(_format_post(post))

    return {
        "posts": posts,
        "page": page,
        "per_page": per_page,
    }


async def get_post(post_id: int) -> dict[str, Any]:
    """Get a single post by ID with full content.

    Args:
        post_id: Post ID

    Returns:
        Full post details including content
    """
    client = get_client()
    post_id = validate_post_id(post_id)

    response = await client.get(f"/posts/{post_id}", params={"_embed": "true"})

    if isinstance(response, dict):
        return {"post": _format_post(response, include_content=True)}

    return {"error": "Unexpected response format"}


async def search_posts(
    keyword: str,
    page: int = 1,
    per_page: int = 10,
) -> dict[str, Any]:
    """Search posts by keyword in title and content.

    Args:
        keyword: Search keyword
        page: Page number
        per_page: Results per page

    Returns:
        Search results
    """
    return await list_posts(search=keyword, page=page, per_page=per_page)


async def create_post(
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
    """Create a new post.

    Args:
        title: Post title
        content: Post content (HTML or block editor format)
        status: Post status (publish, draft, pending, private, future)
        excerpt: Post excerpt
        slug: Post slug for URL
        categories: List of category IDs
        tags: List of tag IDs
        featured_media: Featured image media ID
        date: Publication date (ISO 8601 format for scheduling)
        post_format: Post format (standard, aside, gallery, etc.)

    Returns:
        Created post details
    """
    client = get_client()

    post_data: dict[str, Any] = {
        "title": title,
        "content": content,
        "status": status,
    }

    if excerpt is not None:
        post_data["excerpt"] = excerpt
    if slug is not None:
        post_data["slug"] = slug
    if categories is not None:
        post_data["categories"] = categories
    if tags is not None:
        post_data["tags"] = tags
    if featured_media is not None:
        post_data["featured_media"] = featured_media
    if date is not None:
        post_data["date"] = date
    if post_format is not None:
        post_data["format"] = post_format

    response = await client.post("/posts", json_data=post_data)

    if isinstance(response, dict):
        return {"post": _format_post(response, include_content=True)}

    return {"error": "Unexpected response format"}


async def update_post(
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
    """Update an existing post.

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
    client = get_client()
    post_id = validate_post_id(post_id)

    post_data: dict[str, Any] = {}

    if title is not None:
        post_data["title"] = title
    if content is not None:
        post_data["content"] = content
    if status is not None:
        post_data["status"] = status
    if excerpt is not None:
        post_data["excerpt"] = excerpt
    if slug is not None:
        post_data["slug"] = slug
    if categories is not None:
        post_data["categories"] = categories
    if tags is not None:
        post_data["tags"] = tags
    if featured_media is not None:
        post_data["featured_media"] = featured_media
    if date is not None:
        post_data["date"] = date
    if post_format is not None:
        post_data["format"] = post_format

    if not post_data:
        return {"error": "No fields to update"}

    response = await client.patch(f"/posts/{post_id}", json_data=post_data)

    if isinstance(response, dict):
        return {"post": _format_post(response, include_content=True)}

    return {"error": "Unexpected response format"}


async def delete_post(post_id: int, force: bool = False) -> dict[str, Any]:
    """Delete or trash a post.

    Args:
        post_id: Post ID to delete
        force: If True, permanently delete. If False, move to trash.

    Returns:
        Deletion confirmation
    """
    client = get_client()
    post_id = validate_post_id(post_id)

    params = {"force": str(force).lower()}
    response = await client.delete(f"/posts/{post_id}", params=params)

    if isinstance(response, dict):
        return {
            "success": True,
            "message": "Post permanently deleted" if force else "Post moved to trash",
            "post_id": post_id,
        }

    return {"success": True, "post_id": post_id}


async def list_revisions(post_id: int) -> dict[str, Any]:
    """List revisions for a post.

    Args:
        post_id: Post ID

    Returns:
        List of revisions
    """
    client = get_client()
    post_id = validate_post_id(post_id)

    response = await client.get(f"/posts/{post_id}/revisions")

    revisions = []
    if isinstance(response, list):
        for rev in response:
            revisions.append({
                "id": rev.get("id"),
                "author": rev.get("author"),
                "date": rev.get("date"),
                "modified": rev.get("modified"),
                "title": _get_rendered(rev.get("title")),
            })

    return {"revisions": revisions, "post_id": post_id}


async def get_revision(post_id: int, revision_id: int) -> dict[str, Any]:
    """Get a specific revision of a post.

    Args:
        post_id: Post ID
        revision_id: Revision ID

    Returns:
        Revision details with content
    """
    client = get_client()
    post_id = validate_post_id(post_id)
    revision_id = validate_post_id(revision_id)  # Same validation

    response = await client.get(f"/posts/{post_id}/revisions/{revision_id}")

    if isinstance(response, dict):
        return {
            "revision": {
                "id": response.get("id"),
                "author": response.get("author"),
                "date": response.get("date"),
                "title": _get_rendered(response.get("title")),
                "content": _get_rendered(response.get("content")),
                "excerpt": _get_rendered(response.get("excerpt")),
            }
        }

    return {"error": "Unexpected response format"}


async def list_categories(
    page: int = 1,
    per_page: int = 100,
    search: str | None = None,
) -> dict[str, Any]:
    """List available categories.

    Args:
        page: Page number
        per_page: Results per page
        search: Search categories by name

    Returns:
        List of categories
    """
    client = get_client()

    params: dict[str, Any] = {
        "page": page,
        "per_page": min(per_page, 100),
    }
    if search:
        params["search"] = search

    response = await client.get("/categories", params=params)

    categories = []
    if isinstance(response, list):
        for cat in response:
            categories.append({
                "id": cat.get("id"),
                "name": cat.get("name"),
                "slug": cat.get("slug"),
                "description": cat.get("description"),
                "count": cat.get("count"),
                "parent": cat.get("parent"),
            })

    return {"categories": categories}


async def list_tags(
    page: int = 1,
    per_page: int = 100,
    search: str | None = None,
) -> dict[str, Any]:
    """List available tags.

    Args:
        page: Page number
        per_page: Results per page
        search: Search tags by name

    Returns:
        List of tags
    """
    client = get_client()

    params: dict[str, Any] = {
        "page": page,
        "per_page": min(per_page, 100),
    }
    if search:
        params["search"] = search

    response = await client.get("/tags", params=params)

    tags = []
    if isinstance(response, list):
        for tag in response:
            tags.append({
                "id": tag.get("id"),
                "name": tag.get("name"),
                "slug": tag.get("slug"),
                "description": tag.get("description"),
                "count": tag.get("count"),
            })

    return {"tags": tags}


def _get_rendered(field: dict[str, Any] | str | None) -> str:
    """Extract rendered content from WordPress response field."""
    if field is None:
        return ""
    if isinstance(field, str):
        return field
    if isinstance(field, dict):
        rendered = field.get("rendered", "")
        return str(rendered) if rendered else ""
    return ""


def _format_post(post: dict[str, Any], include_content: bool = False) -> dict[str, Any]:
    """Format a post response for cleaner output."""
    formatted = {
        "id": post.get("id"),
        "title": _get_rendered(post.get("title")),
        "slug": post.get("slug"),
        "status": post.get("status"),
        "date": post.get("date"),
        "modified": post.get("modified"),
        "link": post.get("link"),
        "author": post.get("author"),
        "excerpt": _get_rendered(post.get("excerpt")),
        "categories": post.get("categories", []),
        "tags": post.get("tags", []),
        "featured_media": post.get("featured_media"),
        "format": post.get("format", "standard"),
    }

    if include_content:
        formatted["content"] = _get_rendered(post.get("content"))

    # Include embedded author info if available
    embedded = post.get("_embedded", {})
    if author_list := embedded.get("author"):
        author = author_list[0]
        formatted["author_name"] = author.get("name")

    return formatted
