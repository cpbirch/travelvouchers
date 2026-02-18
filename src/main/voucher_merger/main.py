"""FastAPI application factory for voucher merger service.

This module provides the application factory that wires up all adapters
and creates the FastAPI application instance.
"""

from pathlib import Path
from typing import Optional

from fastapi import FastAPI
from voucher_merger.adapters.filesystem_storage import FilesystemStorage
from voucher_merger.adapters.hardcoded_template_repository import (
    HardcodedTemplateRepository,
)
from voucher_merger.adapters.libreoffice_renderer import LibreOfficeRenderer
from voucher_merger.adapters.rest_api import create_voucher_router
from voucher_merger.application.generate_voucher import GenerateVoucher
from voucher_merger.ports.document_renderer import DocumentRenderer
from voucher_merger.ports.template_repository import TemplateRepository
from voucher_merger.ports.voucher_storage import VoucherStorage


def create_app(
    generate_voucher: Optional[GenerateVoucher] = None,
    template_repository: Optional[TemplateRepository] = None,
    document_renderer: Optional[DocumentRenderer] = None,
    voucher_storage: Optional[VoucherStorage] = None,
) -> FastAPI:
    """Create and configure the FastAPI application.

    This factory function allows dependency injection for testing.
    If no dependencies are provided, production adapters are used.

    Args:
        generate_voucher: Optional pre-configured use case (for testing).
        template_repository: Optional template repository implementation.
        document_renderer: Optional document renderer implementation.
        voucher_storage: Optional voucher storage implementation.

    Returns:
        Configured FastAPI application instance.
    """
    app = FastAPI(
        title="Voucher Merger Service",
        description="Generate vouchers from templates with customer and service data",
        version="0.1.0",
    )

    # If use case is provided directly (for testing), use it
    if generate_voucher is not None:
        router = create_voucher_router(generate_voucher)
        app.include_router(router)
        return app

    # Otherwise, wire up production adapters
    # Use provided adapters or create default ones
    if template_repository is None:
        template_repository = HardcodedTemplateRepository()

    if document_renderer is None:
        document_renderer = LibreOfficeRenderer()

    # For storage, we need to create a factory since FilesystemStorage
    # requires booking_id and service_date at construction time
    # This is a temporary solution for the walking skeleton
    # TODO: Refactor FilesystemStorage to not require these at construction
    storage_base_path = Path("/tmp/voucher-merger")

    # Create a wrapper class that creates storage per-request
    class StorageFactory:
        """Factory for creating FilesystemStorage instances per request."""

        def __init__(self, base_path: Path):
            self._base_path = base_path
            self._current_storage: Optional[FilesystemStorage] = None

        def configure(self, booking_id: str, service_date: str) -> None:
            """Configure storage for a specific booking."""
            self._current_storage = FilesystemStorage(
                base_path=self._base_path,
                booking_id=booking_id,
                service_date=service_date,
            )

        def find_existing(self):
            """Check for existing voucher using the configured storage."""
            if self._current_storage is None:
                return None
            return self._current_storage.find_existing()

        def store(self, document):
            """Store a document using the configured storage."""
            if self._current_storage is None:
                raise RuntimeError("Storage not configured. Call configure() first.")
            return self._current_storage.store(document)

        def store_html(self, document):
            """Store HTML document using the configured storage."""
            if self._current_storage is None:
                raise RuntimeError("Storage not configured. Call configure() first.")
            return self._current_storage.store_html(document)

    storage_factory = StorageFactory(storage_base_path)

    # For the walking skeleton, we need to hook into the request flow
    # to configure storage. For now, use a simplified approach where
    # storage is configured inline. This will be refactored in later steps.

    # Create use case with a storage adapter that configures itself
    use_case = GenerateVoucher(
        template_repository=template_repository,
        document_renderer=document_renderer,
        voucher_storage=storage_factory,
    )

    # Create and include router
    router = create_voucher_router(use_case)
    app.include_router(router)

    return app
