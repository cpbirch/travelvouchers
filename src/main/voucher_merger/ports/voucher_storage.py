"""Port interface for voucher storage."""

from dataclasses import dataclass
from typing import Protocol

from voucher_merger.ports.document_renderer import RenderedDocument, RenderedHtmlDocument


@dataclass(frozen=True)
class StorageUrl:
    """URL where a voucher document is stored.

    Attributes:
        url: The URL where the document can be accessed.
        expires_at: Optional expiration time for the URL (ISO format).
    """

    url: str
    expires_at: str | None = None


class VoucherStorage(Protocol):
    """Driven port for storing voucher documents.

    This port defines the contract for persisting rendered voucher
    documents. Adapters implementing this port may store documents in
    various backends (local filesystem, S3, Azure Blob, etc.).
    """

    def store(self, document: RenderedDocument) -> StorageUrl:
        """Store a rendered voucher document.

        Args:
            document: The rendered PDF document to store.

        Returns:
            The URL where the stored document can be accessed.

        Raises:
            StorageError: If the document cannot be stored.
        """
        ...

    def store_html(self, document: RenderedHtmlDocument) -> StorageUrl:
        """Store a rendered HTML voucher document.

        Args:
            document: The rendered HTML document to store.

        Returns:
            The URL where the stored document can be accessed.

        Raises:
            StorageError: If the document cannot be stored.
        """
        ...
