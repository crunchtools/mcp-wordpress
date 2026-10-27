"""Shared shaping of WordPress REST responses.

WordPress returns most text fields as ``{"rendered": "..."}``, plus ``"raw"``
when asked with ``context=edit``, and repeats the same envelope for posts,
pages, media and comments. Every tool module used to carry its own copy of
these helpers.
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


def get_source(field: dict[str, Any] | str | None) -> str:
    """The saved source of a field (``raw``, sent with ``context=edit``).

    Falls back to the rendered text when the response carries no ``raw``.
    """
    if isinstance(field, dict) and field.get("raw") is not None:
        return str(field["raw"])
    return get_rendered(field)


def format_common(item: dict[str, Any]) -> dict[str, Any]:
    """The fields posts and pages share."""
    return {
        "id": item.get("id"),
        "title": get_source(item.get("title")),
        "slug": item.get("slug"),
        "status": item.get("status"),
        "date": item.get("date"),
        "modified": item.get("modified"),
        "link": item.get("link"),
        "author": item.get("author"),
        "excerpt": get_source(item.get("excerpt")),
        "featured_media": item.get("featured_media"),
        "version": item.get("modified_gmt"),
    }


def add_embedded_author(formatted: dict[str, Any], item: dict[str, Any]) -> None:
    """Copy the embedded author name across when ``_embed`` was requested."""
    if author_list := item.get("_embedded", {}).get("author"):
        formatted["author_name"] = author_list[0].get("name")
