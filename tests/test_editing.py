"""Source reads, edits by replacement, and the guards on full-content writes."""

from typing import Any

import pydantic
import pytest

from mcp_wordpress_crunchtools.errors import ValidationError
from mcp_wordpress_crunchtools.tools import (
    edit_draft,
    edit_page,
    edit_post,
    get_page,
    get_post,
    get_revision,
    update_page,
    update_post,
)
from mcp_wordpress_crunchtools.tools.formatting import source_version
from tests.conftest import _mock_wp_response, _patch_wp_client

SOURCE = (
    "<!-- wp:paragraph -->\n<p>[SERIES NOTE: old]</p>\n<!-- /wp:paragraph -->\n\n"
    "<!-- wp:paragraph -->\n<p>Body text.</p>\n<!-- /wp:paragraph -->"
)
RENDERED = (
    '<p>[SERIES NOTE: old]</p>\n<div id="ez-toc-container">TOC</div>\n'
    '<h2><span class="ez-toc-section" id="a"></span>A</h2>\n<p>Body text.</p>'
)
MODIFIED = "2026-10-27T15:27:35"


def _item(status: str = "draft", content: str = SOURCE, version: str = MODIFIED) -> dict[str, Any]:
    """A post or page as WordPress returns it with context=edit."""
    return {
        "id": 6489,
        "title": {"raw": "Choosing an L2 Classifier", "rendered": "Choosing an L2 Classifier"},
        "status": status,
        "slug": "choosing",
        "date": "2026-10-27T11:27:35",
        "modified": "2026-10-27T11:27:35",
        "modified_gmt": version,
        "link": "https://wp.example.com/?p=6489",
        "author": 1,
        "excerpt": {"raw": "Excerpt.", "rendered": "<p>Excerpt.</p>\n"},
        "content": {"raw": content, "rendered": RENDERED},
        "categories": [],
        "tags": [],
        "featured_media": 0,
        "format": "standard",
    }


VERSION = source_version(_item())


def _sent(mock: Any, call: int) -> dict[str, Any]:
    """The keyword arguments of one request the client made."""
    return dict(mock.call_args_list[call].kwargs)


class TestSourceReads:
    @pytest.mark.asyncio
    async def test_get_post_returns_source(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=_item())) as mock:
            result = await get_post(6489)
        post = result["post"]
        assert post["content"] == SOURCE
        assert "ez-toc" not in post["content"]
        assert post["excerpt"] == "Excerpt."
        assert post["version"] == VERSION
        assert _sent(mock, 0)["params"]["context"] == "edit"

    @pytest.mark.asyncio
    async def test_get_page_returns_source(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=_item())) as mock:
            result = await get_page(6489)
        assert result["page"]["content"] == SOURCE
        assert _sent(mock, 0)["params"]["context"] == "edit"

    @pytest.mark.asyncio
    async def test_get_revision_returns_source(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=_item())) as mock:
            result = await get_revision(6489, 7)
        assert result["revision"]["content"] == SOURCE
        assert _sent(mock, 0)["params"]["context"] == "edit"

    @pytest.mark.asyncio
    async def test_rendered_only_response_falls_back(self) -> None:
        item = _item()
        item["content"] = {"rendered": "<p>Hello</p>"}
        async with _patch_wp_client(response=_mock_wp_response(json_data=item)):
            result = await get_post(6489)
        assert result["post"]["content"] == "<p>Hello</p>"


class TestEditPost:
    @pytest.mark.asyncio
    async def test_replaces_once_and_returns_summary(self) -> None:
        edited = SOURCE.replace("<p>[SERIES NOTE: old]</p>", "<p>New note</p>")
        responses = [
            _mock_wp_response(json_data=_item()),
            _mock_wp_response(json_data=_item(content=edited, version="2026-10-27T16:00:00")),
        ]
        async with _patch_wp_client(side_effect=responses) as mock:
            result = await edit_post(
                6489, "<p>[SERIES NOTE: old]</p>", "<p>New note</p>", expected_version=VERSION
            )
        assert _sent(mock, 1)["json"] == {"content": edited}
        assert result["post"]["replacements"] == 1
        assert result["post"]["version"] == source_version(
            _item(content=edited, version="2026-10-27T16:00:00")
        )
        assert result["post"]["version"] != VERSION
        assert "content" not in result["post"]

    @pytest.mark.asyncio
    async def test_missing_text_is_refused(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=_item())) as mock:
            with pytest.raises(ValidationError, match="not found"):
                await edit_post(6489, "not there", "x")
        assert mock.call_count == 1

    @pytest.mark.asyncio
    async def test_ambiguous_text_is_refused(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=_item())):
            with pytest.raises(ValidationError, match="appears 2 times"):
                await edit_post(6489, "<!-- wp:paragraph -->", "x")

    @pytest.mark.asyncio
    async def test_replace_all(self) -> None:
        responses = [_mock_wp_response(json_data=_item()), _mock_wp_response(json_data=_item())]
        async with _patch_wp_client(side_effect=responses) as mock:
            result = await edit_post(6489, "paragraph", "para", replace_all=True)
        assert result["post"]["replacements"] == 4
        assert "paragraph" not in _sent(mock, 1)["json"]["content"]

    @pytest.mark.asyncio
    async def test_empty_text_is_refused_before_any_request(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=_item())) as mock:
            with pytest.raises(pydantic.ValidationError):
                await edit_post(6489, "", "x")
        assert mock.call_count == 0

    @pytest.mark.asyncio
    async def test_non_dict_read_is_refused(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=[])) as mock:
            with pytest.raises(ValidationError, match="Unexpected response"):
                await edit_post(6489, "Body text.", "x")
        assert mock.call_count == 1

    @pytest.mark.asyncio
    async def test_non_dict_write_is_refused(self) -> None:
        responses = [_mock_wp_response(json_data=_item()), _mock_wp_response(json_data=[])]
        async with _patch_wp_client(side_effect=responses):
            with pytest.raises(ValidationError, match="Unexpected response"):
                await edit_post(6489, "Body text.", "x")

    @pytest.mark.asyncio
    async def test_stale_version_is_refused(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=_item())) as mock:
            with pytest.raises(ValidationError, match="Changed since it was read"):
                await edit_post(6489, "Body text.", "x", expected_version="2026-01-01T00:00:00")
        assert mock.call_count == 1

    @pytest.mark.asyncio
    async def test_edit_page(self) -> None:
        responses = [_mock_wp_response(json_data=_item()), _mock_wp_response(json_data=_item())]
        async with _patch_wp_client(side_effect=responses) as mock:
            result = await edit_page(6489, "Body text.", "New body.")
        assert result["page"]["replacements"] == 1
        assert "/pages/6489" in str(_sent(mock, 1)["url"])


class TestVersion:
    def test_same_second_content_change_is_a_new_version(self) -> None:
        assert source_version(_item(content=SOURCE + "x")) != VERSION

    def test_same_source_is_the_same_version(self) -> None:
        assert source_version(_item()) == VERSION


class TestEditDraft:
    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", ["draft", "pending"])
    async def test_edits_unpublished_and_pins_the_status(self, status: str) -> None:
        responses = [
            _mock_wp_response(json_data=_item(status=status)),
            _mock_wp_response(json_data=_item(status=status)),
        ]
        async with _patch_wp_client(side_effect=responses) as mock:
            result = await edit_draft(6489, "Body text.", "New body.")
        assert result["post"]["replacements"] == 1
        # Published between the read and the write: the write sends it back to draft.
        assert _sent(mock, 1)["json"]["status"] == status

    @pytest.mark.asyncio
    async def test_edit_post_leaves_status_alone(self) -> None:
        responses = [_mock_wp_response(json_data=_item()), _mock_wp_response(json_data=_item())]
        async with _patch_wp_client(side_effect=responses) as mock:
            await edit_post(6489, "Body text.", "New body.")
        assert "status" not in _sent(mock, 1)["json"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", ["publish", "future", "private", "auto-draft"])
    async def test_refuses_anything_else(self, status: str) -> None:
        async with _patch_wp_client(
            response=_mock_wp_response(json_data=_item(status=status))
        ) as mock:
            with pytest.raises(ValidationError, match="Only drafts"):
                await edit_draft(6489, "Body text.", "New body.")
        assert mock.call_count == 1


class TestGuardedUpdate:
    @pytest.mark.asyncio
    async def test_rendered_content_is_refused(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=_item())) as mock:
            with pytest.raises(ValidationError, match="rendered output"):
                await update_post(6489, content=RENDERED)
        assert mock.call_count == 1

    @pytest.mark.asyncio
    async def test_stripping_block_markup_is_refused(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=_item())):
            with pytest.raises(ValidationError, match="block markup"):
                await update_page(6489, content="<p>Body text.</p>")

    @pytest.mark.asyncio
    async def test_source_content_is_written(self) -> None:
        new = SOURCE.replace("Body text.", "New body.")
        responses = [_mock_wp_response(json_data=_item()), _mock_wp_response(json_data=_item())]
        async with _patch_wp_client(side_effect=responses) as mock:
            result = await update_post(6489, content=new, expected_version=VERSION)
        assert _sent(mock, 1)["json"] == {"content": new}
        assert result["post"]["version"] == VERSION

    @pytest.mark.asyncio
    async def test_stale_version_is_refused(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=_item())):
            with pytest.raises(ValidationError, match="Changed since it was read"):
                await update_post(6489, title="New", expected_version="2026-01-01T00:00:00")

    @pytest.mark.asyncio
    async def test_non_dict_write_is_refused(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=[])):
            with pytest.raises(ValidationError, match="Unexpected response"):
                await update_post(6489, title="New")

    @pytest.mark.asyncio
    async def test_metadata_only_update_skips_the_read(self) -> None:
        async with _patch_wp_client(response=_mock_wp_response(json_data=_item())) as mock:
            await update_post(6489, title="New")
        assert mock.call_count == 1
