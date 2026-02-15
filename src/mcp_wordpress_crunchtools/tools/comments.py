"""Comment management tools.

Tools for managing WordPress comments.
"""

from typing import Any

from ..client import get_client
from ..models import validate_comment_id


async def list_comments(
    post: int | None = None,
    status: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 10,
    orderby: str = "date",
    order: str = "desc",
) -> dict[str, Any]:
    """List comments with filtering.

    Args:
        post: Filter by post ID
        status: Filter by status (approved, hold, spam, trash)
        search: Search comments by content
        page: Page number for pagination
        per_page: Results per page (max 100)
        orderby: Sort by field (date, id)
        order: Sort direction (asc, desc)

    Returns:
        Dictionary containing comments list and pagination info
    """
    client = get_client()

    params: dict[str, Any] = {
        "page": page,
        "per_page": min(per_page, 100),
        "orderby": orderby,
        "order": order,
    }

    if post is not None:
        params["post"] = post
    if status:
        params["status"] = status
    if search:
        params["search"] = search

    response = await client.get("/comments", params=params)

    comments = []
    if isinstance(response, list):
        for comment in response:
            comments.append(_format_comment(comment))

    return {
        "comments": comments,
        "page": page,
        "per_page": per_page,
    }


async def get_comment(comment_id: int) -> dict[str, Any]:
    """Get a single comment by ID.

    Args:
        comment_id: Comment ID

    Returns:
        Comment details
    """
    client = get_client()
    comment_id = validate_comment_id(comment_id)

    response = await client.get(f"/comments/{comment_id}")

    if isinstance(response, dict):
        return {"comment": _format_comment(response, include_content=True)}

    return {"error": "Unexpected response format"}


async def create_comment(
    post: int,
    content: str,
    parent: int | None = None,
    author_name: str | None = None,
    author_email: str | None = None,
) -> dict[str, Any]:
    """Create a new comment on a post.

    Args:
        post: Post ID to comment on
        content: Comment content
        parent: Parent comment ID for replies
        author_name: Comment author name (for anonymous comments)
        author_email: Comment author email (for anonymous comments)

    Returns:
        Created comment details
    """
    client = get_client()

    comment_data: dict[str, Any] = {
        "post": post,
        "content": content,
    }

    if parent is not None:
        comment_data["parent"] = parent
    if author_name is not None:
        comment_data["author_name"] = author_name
    if author_email is not None:
        comment_data["author_email"] = author_email

    response = await client.post("/comments", json_data=comment_data)

    if isinstance(response, dict):
        return {"comment": _format_comment(response, include_content=True)}

    return {"error": "Unexpected response format"}


async def update_comment(
    comment_id: int,
    content: str | None = None,
    status: str | None = None,
) -> dict[str, Any]:
    """Update an existing comment.

    Args:
        comment_id: Comment ID to update
        content: New comment content
        status: New status (approved, hold, spam, trash)

    Returns:
        Updated comment details
    """
    client = get_client()
    comment_id = validate_comment_id(comment_id)

    comment_data: dict[str, Any] = {}

    if content is not None:
        comment_data["content"] = content
    if status is not None:
        comment_data["status"] = status

    if not comment_data:
        return {"error": "No fields to update"}

    response = await client.patch(f"/comments/{comment_id}", json_data=comment_data)

    if isinstance(response, dict):
        return {"comment": _format_comment(response, include_content=True)}

    return {"error": "Unexpected response format"}


async def delete_comment(comment_id: int, force: bool = False) -> dict[str, Any]:
    """Delete or trash a comment.

    Args:
        comment_id: Comment ID to delete
        force: If True, permanently delete. If False, move to trash.

    Returns:
        Deletion confirmation
    """
    client = get_client()
    comment_id = validate_comment_id(comment_id)

    params = {"force": str(force).lower()}
    response = await client.delete(f"/comments/{comment_id}", params=params)

    if isinstance(response, dict):
        return {
            "success": True,
            "message": "Comment permanently deleted" if force else "Comment moved to trash",
            "comment_id": comment_id,
        }

    return {"success": True, "comment_id": comment_id}


async def moderate_comment(
    comment_id: int,
    action: str,
) -> dict[str, Any]:
    """Moderate a comment by changing its status.

    Args:
        comment_id: Comment ID to moderate
        action: Moderation action (approve, hold, spam, trash)

    Returns:
        Updated comment details
    """
    # Map action to status
    action_to_status = {
        "approve": "approved",
        "hold": "hold",
        "spam": "spam",
        "trash": "trash",
    }

    if action not in action_to_status:
        return {
            "error": f"Invalid action. Must be one of: {', '.join(action_to_status.keys())}"
        }

    return await update_comment(comment_id, status=action_to_status[action])


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


def _format_comment(
    comment: dict[str, Any], include_content: bool = False
) -> dict[str, Any]:
    """Format a comment response for cleaner output."""
    formatted = {
        "id": comment.get("id"),
        "post": comment.get("post"),
        "parent": comment.get("parent"),
        "author": comment.get("author"),
        "author_name": comment.get("author_name"),
        "date": comment.get("date"),
        "status": comment.get("status"),
        "link": comment.get("link"),
    }

    if include_content:
        formatted["content"] = _get_rendered(comment.get("content"))
        formatted["author_email"] = comment.get("author_email", "")
        formatted["author_url"] = comment.get("author_url", "")

    return formatted
