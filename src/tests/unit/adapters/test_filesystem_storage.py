"""Unit tests for FilesystemStorage adapter.

Test Budget: 3 behaviors x 2 = 6 tests max
- Behavior 1: Store PDF at correct path structure
- Behavior 2: Store HTML at correct path structure
- Behavior 3: Handle filesystem write failures
"""

from pathlib import Path

import pytest

from voucher_merger.ports.document_renderer import RenderedDocument, RenderedHtmlDocument
from voucher_merger.ports.voucher_storage import StorageUrl

# Test constants
TEST_BOOKING_ID = "BK-12345"
TEST_SERVICE_DATE = "2026-03-15"
TEST_PDF_CONTENT = b"%PDF-1.4 test content"
TEST_HTML_CONTENT = "<!DOCTYPE html><html><body>Test</body></html>"


class TestFilesystemStorage:
    """Tests for FilesystemStorage driven port adapter."""

    def test_stores_pdf_at_correct_path_structure(self, tmp_path: Path) -> None:
        """store() writes PDF to /vouchers/{booking_id}/{service_date}/voucher.pdf."""
        from voucher_merger.adapters.filesystem_storage import FilesystemStorage

        storage = FilesystemStorage(
            base_path=tmp_path,
            booking_id=TEST_BOOKING_ID,
            service_date=TEST_SERVICE_DATE,
        )
        document = RenderedDocument(content=TEST_PDF_CONTENT, filename="voucher.pdf")

        storage.store(document)

        expected_path = (
            tmp_path / "vouchers" / TEST_BOOKING_ID / TEST_SERVICE_DATE / "voucher.pdf"
        )
        assert expected_path.exists()
        assert expected_path.read_bytes() == TEST_PDF_CONTENT

    def test_returns_file_url_for_stored_document(self, tmp_path: Path) -> None:
        """store() returns StorageUrl with file:// URL pointing to stored file."""
        from voucher_merger.adapters.filesystem_storage import FilesystemStorage

        storage = FilesystemStorage(
            base_path=tmp_path,
            booking_id="BK-67890",
            service_date="2026-04-20",
        )
        document = RenderedDocument(content=b"%PDF-1.4 content", filename="voucher.pdf")

        result = storage.store(document)

        assert isinstance(result, StorageUrl)
        expected_file_path = (
            tmp_path / "vouchers" / "BK-67890" / "2026-04-20" / "voucher.pdf"
        )
        assert result.url == f"file://{expected_file_path}"

    def test_creates_directory_structure_if_not_exists(self, tmp_path: Path) -> None:
        """store() creates parent directories when they don't exist."""
        from voucher_merger.adapters.filesystem_storage import FilesystemStorage

        storage = FilesystemStorage(
            base_path=tmp_path,
            booking_id="BK-NEW",
            service_date="2026-05-01",
        )
        document = RenderedDocument(content=b"%PDF-1.4 new", filename="voucher.pdf")

        # Verify directories don't exist yet
        vouchers_dir = tmp_path / "vouchers" / "BK-NEW" / "2026-05-01"
        assert not vouchers_dir.exists()

        storage.store(document)

        assert vouchers_dir.exists()
        assert vouchers_dir.is_dir()

    def test_stores_html_at_correct_path_structure(self, tmp_path: Path) -> None:
        """store_html() writes HTML to /vouchers/{booking_id}/{service_date}/voucher.html."""
        from voucher_merger.adapters.filesystem_storage import FilesystemStorage

        storage = FilesystemStorage(
            base_path=tmp_path,
            booking_id=TEST_BOOKING_ID,
            service_date=TEST_SERVICE_DATE,
        )
        document = RenderedHtmlDocument(content=TEST_HTML_CONTENT, filename="voucher.html")

        storage.store_html(document)

        expected_path = (
            tmp_path / "vouchers" / TEST_BOOKING_ID / TEST_SERVICE_DATE / "voucher.html"
        )
        assert expected_path.exists()
        assert expected_path.read_text(encoding="utf-8") == TEST_HTML_CONTENT

    def test_returns_file_url_for_stored_html_document(self, tmp_path: Path) -> None:
        """store_html() returns StorageUrl with file:// URL pointing to stored HTML."""
        from voucher_merger.adapters.filesystem_storage import FilesystemStorage

        storage = FilesystemStorage(
            base_path=tmp_path,
            booking_id="BK-67890",
            service_date="2026-04-20",
        )
        document = RenderedHtmlDocument(
            content="<html><body>Content</body></html>",
            filename="voucher.html",
        )

        result = storage.store_html(document)

        assert isinstance(result, StorageUrl)
        expected_file_path = (
            tmp_path / "vouchers" / "BK-67890" / "2026-04-20" / "voucher.html"
        )
        assert result.url == f"file://{expected_file_path}"

    def test_raises_storage_error_when_write_fails(self, tmp_path: Path) -> None:
        """store() raises StorageError when filesystem write fails."""
        from voucher_merger.adapters.filesystem_storage import FilesystemStorage
        from voucher_merger.ports.voucher_storage import StorageError

        # Create a read-only directory to simulate write failure
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o444)

        storage = FilesystemStorage(
            base_path=read_only_dir,
            booking_id="BK-FAIL",
            service_date="2026-05-01",
        )
        document = RenderedDocument(content=b"%PDF-1.4 test", filename="voucher.pdf")

        try:
            with pytest.raises(StorageError) as exc_info:
                storage.store(document)
            assert "BK-FAIL" in str(exc_info.value) or "Permission" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            read_only_dir.chmod(0o755)

    def test_raises_storage_error_when_html_write_fails(self, tmp_path: Path) -> None:
        """store_html() raises StorageError when filesystem write fails."""
        from voucher_merger.adapters.filesystem_storage import FilesystemStorage
        from voucher_merger.ports.voucher_storage import StorageError

        # Create a read-only directory to simulate write failure
        read_only_dir = tmp_path / "readonly_html"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o444)

        storage = FilesystemStorage(
            base_path=read_only_dir,
            booking_id="BK-FAIL-HTML",
            service_date="2026-05-01",
        )
        document = RenderedHtmlDocument(content="<html></html>", filename="voucher.html")

        try:
            with pytest.raises(StorageError) as exc_info:
                storage.store_html(document)
            assert "BK-FAIL-HTML" in str(exc_info.value) or "Permission" in str(exc_info.value)
        finally:
            # Restore permissions for cleanup
            read_only_dir.chmod(0o755)
