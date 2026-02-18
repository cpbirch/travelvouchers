"""Port interface for voucher storage."""

from dataclasses import dataclass
from typing import Protocol

from voucher_merger.ports.document_renderer import RenderedDocument, RenderedHtmlDocument


class StorageError(Exception):
    """Raised when storage operations fail.

    This exception indicates that a voucher could not be stored due to
    infrastructure issues (filesystem errors, network problems, etc.).
    """

    pass


@dataclass(frozen=True)
class StorageUrl:
    """URL where a voucher document is stored.

    Attributes:
        url: The URL where the document can be accessed.
        expires_at: Optional expiration time for the URL (ISO format).
    """

    url: str
    expires_at: str | None = None


@dataclass(frozen=True)
class VoucherMetadata:
    """Metadata for an existing voucher.

    Attributes:
        voucher_id: Unique identifier for the voucher.
        booking_id: Associated booking identifier.
        service_date: Service date in ISO format.
        template_id: Template used for generation.
        generated_at: ISO timestamp when the voucher was generated.
        pdf_url: URL to the stored PDF.
        html_url: URL to the stored HTML.
    """

    voucher_id: str
    booking_id: str
    service_date: str
    template_id: str
    generated_at: str
    pdf_url: str
    html_url: str


class VoucherStorage(Protocol):
    """Driven port for storing voucher documents.

    This port defines the contract for persisting rendered voucher
    documents. Adapters implementing this port may store documents in
    various backends (local filesystem, S3, Azure Blob, etc.).
    """

    def find_existing(self) -> VoucherMetadata | None:
        """Check if a voucher already exists for the configured booking/date.

        Returns:
            VoucherMetadata if a voucher exists, None otherwise.

        This method supports idempotency by checking for existing vouchers
        before generating new ones.
        """
        ...

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
