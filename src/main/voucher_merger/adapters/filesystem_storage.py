"""Filesystem storage adapter for voucher documents."""

from pathlib import Path

from voucher_merger.ports.document_renderer import RenderedDocument
from voucher_merger.ports.voucher_storage import StorageUrl


class FilesystemStorage:
    """Stores voucher documents on the local filesystem.

    This adapter implements the VoucherStorage protocol by writing
    PDF documents to a structured directory path and returning
    file:// URLs for local access.
    """

    def __init__(
        self,
        base_path: Path,
        booking_id: str,
        service_date: str,
    ) -> None:
        """Initialize the filesystem storage adapter.

        Args:
            base_path: Root directory for storing vouchers.
            booking_id: Booking identifier for the voucher.
            service_date: Service date in ISO format (YYYY-MM-DD).
        """
        self._base_path = base_path
        self._booking_id = booking_id
        self._service_date = service_date

    def store(self, document: RenderedDocument) -> StorageUrl:
        """Store a rendered voucher document on the filesystem.

        Creates the directory structure /vouchers/{booking_id}/{service_date}/
        if it doesn't exist, writes the PDF content to voucher.pdf, and
        returns a file:// URL pointing to the stored file.

        Args:
            document: The rendered PDF document to store.

        Returns:
            StorageUrl with file:// URL to the stored document.
        """
        storage_dir = (
            self._base_path / "vouchers" / self._booking_id / self._service_date
        )
        storage_dir.mkdir(parents=True, exist_ok=True)

        file_path = storage_dir / "voucher.pdf"
        file_path.write_bytes(document.content)

        return StorageUrl(url=f"file://{file_path}")
