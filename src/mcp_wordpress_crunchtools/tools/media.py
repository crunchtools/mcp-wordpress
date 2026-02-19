"""Media management tools.

Tools for uploading, managing, and retrieving WordPress media items.
"""

import mimetypes
import os
from typing import Any

from ..client import get_client
from ..models import validate_media_id

# Maximum upload size (50MB)
MAX_UPLOAD_SIZE = 50 * 1024 * 1024


async def list_media(
    media_type: str | None = None,
    mime_type: str | None = None,
    search: str | None = None,
    page: int = 1,
    per_page: int = 10,
    orderby: str = "date",
    order: str = "desc",
) -> dict[str, Any]:
    """List media items with filtering.

    Args:
        media_type: Filter by type (image, video, audio, application)
        mime_type: Filter by MIME type (e.g., image/jpeg)
        search: Search media by keyword
        page: Page number for pagination
        per_page: Results per page (max 100)
        orderby: Sort by field (date, title, id)
        order: Sort direction (asc, desc)

    Returns:
        Dictionary containing media items and pagination info
    """
    client = get_client()

    params: dict[str, Any] = {
        "page": page,
        "per_page": min(per_page, 100),
        "orderby": orderby,
        "order": order,
    }

    if media_type:
        params["media_type"] = media_type
    if mime_type:
        params["mime_type"] = mime_type
    if search:
        params["search"] = search

    response = await client.get("/media", params=params)

    media_items = []
    if isinstance(response, list):
        for item in response:
            media_items.append(_format_media(item))

    return {
        "media": media_items,
        "page": page,
        "per_page": per_page,
    }


async def get_media(media_id: int) -> dict[str, Any]:
    """Get a single media item by ID.

    Args:
        media_id: Media ID

    Returns:
        Media item details
    """
    client = get_client()
    media_id = validate_media_id(media_id)

    response = await client.get(f"/media/{media_id}")

    if isinstance(response, dict):
        return {"media": _format_media(response, include_details=True)}

    return {"error": "Unexpected response format"}


def _read_upload_file(
    file_path: str,
) -> tuple[str | None, bytes, str, str]:
    """Validate and read a file for upload.

    Returns:
        Tuple of (error_message, file_bytes, filename, content_type).
        error_message is None on success.
    """
    if not os.path.isabs(file_path):
        return ("file_path must be an absolute path", b"", "", "")
    if not os.path.isfile(file_path):
        return (
            f"File not found: {file_path}. If running as a container, place files in "
            "the host upload directory (default: ~/.local/share/mcp-wordpress/uploads/) "
            "which is mounted to the MCP_UPLOAD_DIR inside the container.",
            b"",
            "",
            "",
        )

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        return ("File is empty", b"", "", "")
    if file_size > MAX_UPLOAD_SIZE:
        max_mb = MAX_UPLOAD_SIZE // (1024 * 1024)
        return (f"File too large ({file_size} bytes). Max: {max_mb}MB.", b"", "", "")

    filename = os.path.basename(file_path)
    content_type, _ = mimetypes.guess_type(filename)
    if not content_type:
        content_type = "application/octet-stream"

    try:
        with open(file_path, "rb") as f:
            file_bytes = f.read()
    except OSError as e:
        return (f"Cannot read file: {e}", b"", "", "")

    return (None, file_bytes, filename, content_type)


async def upload_media(
    file_path: str,
    title: str | None = None,
    alt_text: str | None = None,
    caption: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Upload a media file from a local file path.

    Args:
        file_path: Absolute path to the file on disk
        title: Media title
        alt_text: Alt text for accessibility
        caption: Media caption
        description: Media description

    Returns:
        Uploaded media item details
    """
    client = get_client()

    # Validate file path and read contents
    error, file_bytes, filename, content_type = _read_upload_file(file_path)
    if error:
        return {"error": error}

    # WordPress expects multipart/form-data with the file
    files = {
        "file": (filename, file_bytes, content_type),
    }

    # Additional metadata as form data
    form_data: dict[str, Any] = {}
    if title:
        form_data["title"] = title
    if alt_text:
        form_data["alt_text"] = alt_text
    if caption:
        form_data["caption"] = caption
    if description:
        form_data["description"] = description

    response = await client.post("/media", data=form_data, files=files)

    if isinstance(response, dict):
        return {"media": _format_media(response, include_details=True)}

    return {"error": "Unexpected response format"}


async def update_media(
    media_id: int,
    title: str | None = None,
    alt_text: str | None = None,
    caption: str | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """Update media item metadata.

    Args:
        media_id: Media ID to update
        title: New title
        alt_text: New alt text
        caption: New caption
        description: New description

    Returns:
        Updated media item details
    """
    client = get_client()
    media_id = validate_media_id(media_id)

    media_data: dict[str, Any] = {}

    if title is not None:
        media_data["title"] = title
    if alt_text is not None:
        media_data["alt_text"] = alt_text
    if caption is not None:
        media_data["caption"] = caption
    if description is not None:
        media_data["description"] = description

    if not media_data:
        return {"error": "No fields to update"}

    response = await client.patch(f"/media/{media_id}", json_data=media_data)

    if isinstance(response, dict):
        return {"media": _format_media(response, include_details=True)}

    return {"error": "Unexpected response format"}


async def delete_media(media_id: int, force: bool = True) -> dict[str, Any]:  # noqa: ARG001
    """Delete a media item.

    Args:
        media_id: Media ID to delete
        force: Must be True for media (media cannot be trashed)

    Returns:
        Deletion confirmation
    """
    client = get_client()
    media_id = validate_media_id(media_id)

    # Media deletion requires force=true
    params = {"force": "true"}
    response = await client.delete(f"/media/{media_id}", params=params)

    if isinstance(response, dict):
        return {
            "success": True,
            "message": "Media permanently deleted",
            "media_id": media_id,
        }

    return {"success": True, "media_id": media_id}


async def get_media_url(media_id: int, size: str = "full") -> dict[str, Any]:
    """Get the public URL for a media item.

    Args:
        media_id: Media ID
        size: Image size (thumbnail, medium, large, full)

    Returns:
        Media URL information
    """
    client = get_client()
    media_id = validate_media_id(media_id)

    response = await client.get(f"/media/{media_id}")

    if isinstance(response, dict):
        media_details = response.get("media_details", {})
        sizes = media_details.get("sizes", {})

        # Get the requested size or fall back to source_url
        url = response.get("source_url", "")
        if size in sizes:
            url = sizes[size].get("source_url", url)
        elif size != "full" and sizes:
            # Try full as fallback
            url = sizes.get("full", {}).get("source_url", url)

        return {
            "media_id": media_id,
            "url": url,
            "size": size,
            "available_sizes": list(sizes.keys()),
            "mime_type": response.get("mime_type"),
        }

    return {"error": "Unexpected response format"}


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


def _format_media(media: dict[str, Any], include_details: bool = False) -> dict[str, Any]:
    """Format a media response for cleaner output."""
    formatted = {
        "id": media.get("id"),
        "title": _get_rendered(media.get("title")),
        "slug": media.get("slug"),
        "date": media.get("date"),
        "modified": media.get("modified"),
        "link": media.get("link"),
        "source_url": media.get("source_url"),
        "mime_type": media.get("mime_type"),
        "media_type": media.get("media_type"),
        "alt_text": media.get("alt_text", ""),
    }

    if include_details:
        formatted["caption"] = _get_rendered(media.get("caption"))
        formatted["description"] = _get_rendered(media.get("description"))

        # Include size information for images
        media_details = media.get("media_details", {})
        if media_details:
            formatted["width"] = media_details.get("width")
            formatted["height"] = media_details.get("height")
            formatted["file"] = media_details.get("file")

            # Include available sizes
            sizes = media_details.get("sizes", {})
            if sizes:
                formatted["available_sizes"] = {
                    name: {
                        "width": info.get("width"),
                        "height": info.get("height"),
                        "url": info.get("source_url"),
                    }
                    for name, info in sizes.items()
                }

    return formatted
