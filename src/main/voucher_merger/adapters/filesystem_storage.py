"""Filesystem storage adapter for voucher documents."""

import json
from pathlib import Path

from voucher_merger.ports.document_renderer import RenderedDocument, RenderedHtmlDocument
from voucher_merger.ports.voucher_storage import StorageError, StorageUrl, VoucherMetadata


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

    def _get_storage_dir(self) -> Path:
        """Get the storage directory for this voucher."""
        return self._base_path / "vouchers" / self._booking_id / self._service_date

    def find_existing(self) -> VoucherMetadata | None:
        """Check if a voucher already exists for this booking/date.

        Returns:
            VoucherMetadata if a voucher exists, None otherwise.
        """
        storage_dir = self._get_storage_dir()
        metadata_path = storage_dir / "metadata.json"

        if not metadata_path.exists():
            return None

        try:
            with open(metadata_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            return VoucherMetadata(
                voucher_id=data["voucher_id"],
                booking_id=data["booking_id"],
                service_date=data["service_date"],
                template_id=data["template_id"],
                generated_at=data["generated_at"],
                pdf_url=data["pdf_url"],
                html_url=data["html_url"],
            )
        except (OSError, json.JSONDecodeError, KeyError):
            return None

    def store_metadata(self, metadata: VoucherMetadata) -> None:
        """Store voucher metadata for idempotency checking.

        Args:
            metadata: The voucher metadata to store.
        """
        storage_dir = self._get_storage_dir()
        storage_dir.mkdir(parents=True, exist_ok=True)
        metadata_path = storage_dir / "metadata.json"

        data = {
            "voucher_id": metadata.voucher_id,
            "booking_id": metadata.booking_id,
            "service_date": metadata.service_date,
            "template_id": metadata.template_id,
            "generated_at": metadata.generated_at,
            "pdf_url": metadata.pdf_url,
            "html_url": metadata.html_url,
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(data, f)

    def store(self, document: RenderedDocument) -> StorageUrl:
        """Store a rendered voucher document on the filesystem.

        Creates the directory structure /vouchers/{booking_id}/{service_date}/
        if it doesn't exist, writes the PDF content to voucher.pdf, and
        returns a file:// URL pointing to the stored file.

        Args:
            document: The rendered PDF document to store.

        Returns:
            StorageUrl with file:// URL to the stored document.

        Raises:
            StorageError: If the document cannot be stored due to filesystem errors.
        """
        storage_dir = self._get_storage_dir()

        try:
            storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = storage_dir / "voucher.pdf"
            file_path.write_bytes(document.content)
        except OSError as e:
            raise StorageError(
                f"Failed to store PDF for booking {self._booking_id}: {e}"
            ) from e

        return StorageUrl(url=f"file://{file_path}")

    def store_html(self, document: RenderedHtmlDocument) -> StorageUrl:
        """Store a rendered HTML voucher document on the filesystem.

        Creates the directory structure /vouchers/{booking_id}/{service_date}/
        if it doesn't exist, writes the HTML content to voucher.html, and
        returns a file:// URL pointing to the stored file.

        Args:
            document: The rendered HTML document to store.

        Returns:
            StorageUrl with file:// URL to the stored document.

        Raises:
            StorageError: If the document cannot be stored due to filesystem errors.
        """
        storage_dir = self._get_storage_dir()

        try:
            storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = storage_dir / "voucher.html"
            file_path.write_text(document.content, encoding="utf-8")
        except OSError as e:
            raise StorageError(
                f"Failed to store HTML for booking {self._booking_id}: {e}"
            ) from e

        return StorageUrl(url=f"file://{file_path}")
