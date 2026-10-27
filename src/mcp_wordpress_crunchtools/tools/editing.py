"""Editing posts and pages by their stored source.

WordPress serves two copies of every text field. ``raw`` is the source the
editor saved, block markup (``<!-- wp:... -->``) and all. ``rendered`` is that
source after filters and plugins ran: block markup removed, a table of contents
injected. Only ``raw`` survives being written back, so reads ask for
``context=edit`` and every write here works on ``raw``.

Edits are replacements made on the server: the caller sends the text to change
and its replacement, never the whole post, and the server refuses when the post
changed since the caller read it.

WordPress has no conditional write. The version check is made on a read one
round trip before the write, so it narrows a lost update to that window rather
than closing it. The draft-only boundary does not rely on that read: the write
itself carries the draft status, so a post published inside the window goes
back to draft rather than going live with the edit.
"""

from __future__ import annotations

from typing import Any

from ..client import get_client
from ..errors import ValidationError
from ..models import EditInput, validate_positive_id
from .formatting import get_source

# Statuses that have never been public. edit_draft refuses anything else.
DRAFT_STATUSES = frozenset({"draft", "pending"})

# Strings that appear only in rendered output, never in a saved source.
RENDERED_MARKERS = ("ez-toc-container", 'class="ez-toc-section"')
BLOCK_MARKER = "<!-- wp:"


async def read_source(collection: str, item_id: int) -> dict[str, Any]:
    """The item as the editor sees it, with ``raw`` fields."""
    response = await get_client().get(f"/{collection}/{item_id}", params={"context": "edit"})
    if not isinstance(response, dict):
        raise ValidationError("Unexpected response format")
    return response


def summary(item: dict[str, Any]) -> dict[str, Any]:
    """What a write returns: enough to chain the next edit, not the content."""
    return {
        "id": item.get("id"),
        "title": get_source(item.get("title")),
        "status": item.get("status"),
        "version": item.get("modified_gmt"),
        "link": item.get("link"),
    }


def check_version(current: dict[str, Any], expected: str | None) -> None:
    """Refuse a write against a copy that is no longer current."""
    if expected is not None and current.get("modified_gmt") != expected:
        raise ValidationError(
            f"Changed since it was read (version {current.get('modified_gmt')}, "
            f"expected {expected}). Read it again and redo the edit."
        )


def check_source(current_content: str, new_content: str) -> None:
    """Refuse content that is rendered output rather than source.

    This catches the one known way a full-content write corrupts a post:
    writing back what a rendered read returned, which carries plugin output
    and no block markup at all. It is not a block-structure validator. A
    caller that keeps block markup but deletes or rewrites blocks is making a
    deliberate edit, and that is allowed.
    """
    if any(marker in new_content for marker in RENDERED_MARKERS):
        raise ValidationError(
            "Content contains rendered output (a generated table of contents). "
            "Write the source a get_ tool returned, or use an edit_ tool to change part of it."
        )
    if BLOCK_MARKER in current_content and BLOCK_MARKER not in new_content:
        raise ValidationError(
            "Content would strip the post's block markup. "
            "Write the source a get_ tool returned, or use an edit_ tool to change part of it."
        )


def replace_text(source: str, old_text: str, new_text: str, replace_all: bool) -> tuple[str, int]:
    """Replace ``old_text`` in ``source``: exactly once, or everywhere if asked."""
    count = source.count(old_text)
    if count == 0:
        raise ValidationError(
            "old_text was not found in the source. Read it again and copy it exactly."
        )
    if count > 1 and not replace_all:
        raise ValidationError(
            f"old_text appears {count} times. Include more surrounding text, or set replace_all."
        )
    return source.replace(old_text, new_text), count


async def edit_source(
    collection: str,
    item_id: int,
    old_text: str,
    new_text: str,
    expected_version: str | None = None,
    replace_all: bool = False,
    drafts_only: bool = False,
) -> dict[str, Any]:
    """Replace text in an item's source and save it."""
    item_id = validate_positive_id(item_id)
    edit = EditInput.model_validate(
        {
            "old_text": old_text,
            "new_text": new_text,
            "expected_version": expected_version,
            "replace_all": replace_all,
        }
    )
    current = await read_source(collection, item_id)
    status = current.get("status")
    if drafts_only and status not in DRAFT_STATUSES:
        raise ValidationError(f"Only drafts can be edited with this tool; this one is {status}.")
    check_version(current, edit.expected_version)
    content, count = replace_text(
        get_source(current.get("content")), edit.old_text, edit.new_text, edit.replace_all
    )
    fields: dict[str, Any] = {"content": content}
    if drafts_only:
        fields["status"] = status
    response = await get_client().patch(f"/{collection}/{item_id}", json_data=fields)
    if not isinstance(response, dict):
        raise ValidationError("Unexpected response format")
    return {**summary(response), "replacements": count}


async def guarded_update(
    collection: str,
    item_id: int,
    fields: dict[str, Any],
    expected_version: str | None = None,
) -> dict[str, Any]:
    """Write fields to an item, refusing stale copies and rendered content."""
    if expected_version is not None or "content" in fields:
        current = await read_source(collection, item_id)
        check_version(current, expected_version)
        if "content" in fields:
            check_source(get_source(current.get("content")), fields["content"])
    response = await get_client().patch(f"/{collection}/{item_id}", json_data=fields)
    if not isinstance(response, dict):
        raise ValidationError("Unexpected response format")
    return summary(response)
