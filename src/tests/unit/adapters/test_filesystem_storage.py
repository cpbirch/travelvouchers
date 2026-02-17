"""Unit tests for FilesystemStorage adapter."""

from pathlib import Path

from voucher_merger.ports.document_renderer import RenderedDocument
from voucher_merger.ports.voucher_storage import StorageUrl


class TestFilesystemStorage:
    """Tests for FilesystemStorage driven port adapter."""

    def test_stores_pdf_at_correct_path_structure(self, tmp_path: Path) -> None:
        """store() writes PDF to /vouchers/{booking_id}/{service_date}/voucher.pdf."""
        from voucher_merger.adapters.filesystem_storage import FilesystemStorage

        storage = FilesystemStorage(
            base_path=tmp_path,
            booking_id="BK-12345",
            service_date="2026-03-15",
        )
        pdf_content = b"%PDF-1.4 test content"
        document = RenderedDocument(content=pdf_content, filename="voucher.pdf")

        storage.store(document)

        expected_path = (
            tmp_path / "vouchers" / "BK-12345" / "2026-03-15" / "voucher.pdf"
        )
        assert expected_path.exists()
        assert expected_path.read_bytes() == b"%PDF-1.4 test content"

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
