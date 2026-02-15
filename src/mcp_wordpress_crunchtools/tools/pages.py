"""Page management tools.

Tools for creating, reading, updating, and deleting WordPress pages.
"""

from typing import Any

from ..client import get_client
from ..models import validate_page_id


async def list_pages(
    status: str | None = None,
    search: str | None = None,
    parent: int | None = None,
    page: int = 1,
    per_page: int = 10,
    orderby: str = "date",
    order: str = "desc",
) -> dict[str, Any]:
    """List pages with filtering and pagination.

    Args:
        status: Filter by status (publish, draft, pending, private, future)
        search: Search pages by keyword
        parent: Filter by parent page ID
        page: Page number for pagination
        per_page: Results per page (max 100)
        orderby: Sort by field (date, title, id, modified, menu_order)
        order: Sort direction (asc, desc)

    Returns:
        Dictionary containing pages list and pagination info
    """
    client = get_client()

    params: dict[str, Any] = {
        "page": page,
        "per_page": min(per_page, 100),
        "orderby": orderby,
        "order": order,
        "_embed": "true",
    }

    if status:
        params["status"] = status
    if search:
        params["search"] = search
    if parent is not None:
        params["parent"] = parent

    response = await client.get("/pages", params=params)

    pages = []
    if isinstance(response, list):
        for pg in response:
            pages.append(_format_page(pg))

    return {
        "pages": pages,
        "page": page,
        "per_page": per_page,
    }


async def get_page(page_id: int) -> dict[str, Any]:
    """Get a single page by ID with full content.

    Args:
        page_id: Page ID

    Returns:
        Full page details including content
    """
    client = get_client()
    page_id = validate_page_id(page_id)

    response = await client.get(f"/pages/{page_id}", params={"_embed": "true"})

    if isinstance(response, dict):
        return {"page": _format_page(response, include_content=True)}

    return {"error": "Unexpected response format"}


async def create_page(
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
    """Create a new page.

    Args:
        title: Page title
        content: Page content (HTML or block editor format)
        status: Page status (publish, draft, pending, private, future)
        excerpt: Page excerpt
        slug: Page slug for URL
        parent: Parent page ID
        menu_order: Menu order
        template: Page template file
        featured_media: Featured image media ID
        date: Publication date (ISO 8601 format)

    Returns:
        Created page details
    """
    client = get_client()

    page_data: dict[str, Any] = {
        "title": title,
        "content": content,
        "status": status,
    }

    if excerpt is not None:
        page_data["excerpt"] = excerpt
    if slug is not None:
        page_data["slug"] = slug
    if parent is not None:
        page_data["parent"] = parent
    if menu_order is not None:
        page_data["menu_order"] = menu_order
    if template is not None:
        page_data["template"] = template
    if featured_media is not None:
        page_data["featured_media"] = featured_media
    if date is not None:
        page_data["date"] = date

    response = await client.post("/pages", json_data=page_data)

    if isinstance(response, dict):
        return {"page": _format_page(response, include_content=True)}

    return {"error": "Unexpected response format"}


async def update_page(
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
    """Update an existing page.

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
    client = get_client()
    page_id = validate_page_id(page_id)

    page_data: dict[str, Any] = {}

    if title is not None:
        page_data["title"] = title
    if content is not None:
        page_data["content"] = content
    if status is not None:
        page_data["status"] = status
    if excerpt is not None:
        page_data["excerpt"] = excerpt
    if slug is not None:
        page_data["slug"] = slug
    if parent is not None:
        page_data["parent"] = parent
    if menu_order is not None:
        page_data["menu_order"] = menu_order
    if template is not None:
        page_data["template"] = template
    if featured_media is not None:
        page_data["featured_media"] = featured_media
    if date is not None:
        page_data["date"] = date

    if not page_data:
        return {"error": "No fields to update"}

    response = await client.patch(f"/pages/{page_id}", json_data=page_data)

    if isinstance(response, dict):
        return {"page": _format_page(response, include_content=True)}

    return {"error": "Unexpected response format"}


async def delete_page(page_id: int, force: bool = False) -> dict[str, Any]:
    """Delete or trash a page.

    Args:
        page_id: Page ID to delete
        force: If True, permanently delete. If False, move to trash.

    Returns:
        Deletion confirmation
    """
    client = get_client()
    page_id = validate_page_id(page_id)

    params = {"force": str(force).lower()}
    response = await client.delete(f"/pages/{page_id}", params=params)

    if isinstance(response, dict):
        return {
            "success": True,
            "message": "Page permanently deleted" if force else "Page moved to trash",
            "page_id": page_id,
        }

    return {"success": True, "page_id": page_id}


async def list_page_revisions(page_id: int) -> dict[str, Any]:
    """List revisions for a page.

    Args:
        page_id: Page ID

    Returns:
        List of revisions
    """
    client = get_client()
    page_id = validate_page_id(page_id)

    response = await client.get(f"/pages/{page_id}/revisions")

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

    return {"revisions": revisions, "page_id": page_id}


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


def _format_page(page: dict[str, Any], include_content: bool = False) -> dict[str, Any]:
    """Format a page response for cleaner output."""
    formatted = {
        "id": page.get("id"),
        "title": _get_rendered(page.get("title")),
        "slug": page.get("slug"),
        "status": page.get("status"),
        "date": page.get("date"),
        "modified": page.get("modified"),
        "link": page.get("link"),
        "author": page.get("author"),
        "excerpt": _get_rendered(page.get("excerpt")),
        "parent": page.get("parent"),
        "menu_order": page.get("menu_order"),
        "template": page.get("template", ""),
        "featured_media": page.get("featured_media"),
    }

    if include_content:
        formatted["content"] = _get_rendered(page.get("content"))

    # Include embedded author info if available
    embedded = page.get("_embedded", {})
    if author_list := embedded.get("author"):
        author = author_list[0]
        formatted["author_name"] = author.get("name")

    return formatted
