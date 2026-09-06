"""Shared shaping of WordPress REST responses.

WordPress returns most text fields as ``{"rendered": "..."}`` and repeats the
same envelope for posts, pages, media and comments. Every tool module used to
carry its own copy of both helpers.
"""

from __future__ import annotations

from typing import Any


def get_rendered(field: dict[str, Any] | str | None) -> str:
    """Pull the rendered text out of a WordPress field, whatever shape it is."""
    if field is None:
        return ""
    if isinstance(field, str):
        return field
    if isinstance(field, dict):
        rendered = field.get("rendered", "")
        return str(rendered) if rendered else ""
    return ""


def format_common(item: dict[str, Any]) -> dict[str, Any]:
    """The fields posts and pages share."""
    return {
        "id": item.get("id"),
        "title": get_rendered(item.get("title")),
        "slug": item.get("slug"),
        "status": item.get("status"),
        "date": item.get("date"),
        "modified": item.get("modified"),
        "link": item.get("link"),
        "author": item.get("author"),
        "excerpt": get_rendered(item.get("excerpt")),
        "featured_media": item.get("featured_media"),
    }


def add_embedded_author(formatted: dict[str, Any], item: dict[str, Any]) -> None:
    """Copy the embedded author name across when ``_embed`` was requested."""
    if author_list := item.get("_embedded", {}).get("author"):
        formatted["author_name"] = author_list[0].get("name")
