"""Factory for creating FilesystemStorage instances per request.

This module provides a factory adapter that creates FilesystemStorage
instances dynamically based on booking context, allowing the storage
to be configured after construction.
"""

from pathlib import Path
from typing import Optional

from voucher_merger.adapters.filesystem_storage import FilesystemStorage
from voucher_merger.ports.document_renderer import RenderedDocument, RenderedHtmlDocument
from voucher_merger.ports.voucher_storage import StorageUrl, VoucherMetadata


class StorageFactory:
    """Factory for creating FilesystemStorage instances per request.

    This adapter wraps FilesystemStorage and provides a configure()
    method to set the booking context before storage operations.
    This allows the storage to be injected into use cases that
    don't know the booking context at construction time.
    """

    def __init__(self, base_path: Path) -> None:
        """Initialize the storage factory.

        Args:
            base_path: Root directory for storing vouchers.
        """
        self._base_path = base_path
        self._current_storage: Optional[FilesystemStorage] = None

    def configure(self, booking_id: str, service_date: str) -> None:
        """Configure storage for a specific booking.

        Args:
            booking_id: Booking identifier for the voucher.
            service_date: Service date in ISO format (YYYY-MM-DD).
        """
        self._current_storage = FilesystemStorage(
            base_path=self._base_path,
            booking_id=booking_id,
            service_date=service_date,
        )

    def find_existing(self) -> VoucherMetadata | None:
        """Check for existing voucher using the configured storage.

        Returns:
            VoucherMetadata if a voucher exists, None otherwise.
        """
        if self._current_storage is None:
            return None
        return self._current_storage.find_existing()

    def store(self, document: RenderedDocument) -> StorageUrl:
        """Store a document using the configured storage.

        Args:
            document: The rendered PDF document to store.

        Returns:
            StorageUrl with URL to the stored document.

        Raises:
            RuntimeError: If storage has not been configured.
        """
        if self._current_storage is None:
            raise RuntimeError("Storage not configured. Call configure() first.")
        return self._current_storage.store(document)

    def store_html(self, document: RenderedHtmlDocument) -> StorageUrl:
        """Store HTML document using the configured storage.

        Args:
            document: The rendered HTML document to store.

        Returns:
            StorageUrl with URL to the stored document.

        Raises:
            RuntimeError: If storage has not been configured.
        """
        if self._current_storage is None:
            raise RuntimeError("Storage not configured. Call configure() first.")
        return self._current_storage.store_html(document)
