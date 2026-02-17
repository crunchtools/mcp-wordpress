"""Tests for media upload file validation."""

import os
import tempfile

from mcp_wordpress_crunchtools.tools.media import _read_upload_file


class TestReadUploadFile:
    """Tests for _read_upload_file validation."""

    def test_relative_path_rejected(self) -> None:
        """Test that relative paths are rejected."""
        error, _, _, _ = _read_upload_file("relative/path/image.png")
        assert error is not None
        assert "absolute path" in error

    def test_file_not_found_mentions_container_mount(self) -> None:
        """Test that file-not-found error mentions container mount path."""
        error, _, _, _ = _read_upload_file("/nonexistent/path/image.png")
        assert error is not None
        assert "File not found" in error
        assert "container" in error
        assert "/tmp/mcp-uploads/" in error  # noqa: S108

    def test_empty_file_rejected(self) -> None:
        """Test that empty files are rejected."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"")
            tmp_path = f.name
        try:
            error, _, _, _ = _read_upload_file(tmp_path)
            assert error is not None
            assert "empty" in error.lower()
        finally:
            os.unlink(tmp_path)

    def test_valid_file_returns_no_error(self) -> None:
        """Test that a valid file returns no error."""
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
            tmp_path = f.name
        try:
            error, file_bytes, filename, content_type = _read_upload_file(tmp_path)
            assert error is None
            assert len(file_bytes) == 108
            assert filename.endswith(".png")
            assert content_type == "image/png"
        finally:
            os.unlink(tmp_path)

    def test_valid_file_detects_jpeg_mime(self) -> None:
        """Test that JPEG files get correct MIME type."""
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
            f.write(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
            tmp_path = f.name
        try:
            error, _, _, content_type = _read_upload_file(tmp_path)
            assert error is None
            assert content_type == "image/jpeg"
        finally:
            os.unlink(tmp_path)

    def test_unknown_extension_gets_octet_stream(self) -> None:
        """Test that unknown extensions get application/octet-stream."""
        with tempfile.NamedTemporaryFile(suffix=".xyz123", delete=False) as f:
            f.write(b"some data")
            tmp_path = f.name
        try:
            error, _, _, content_type = _read_upload_file(tmp_path)
            assert error is None
            assert content_type == "application/octet-stream"
        finally:
            os.unlink(tmp_path)
