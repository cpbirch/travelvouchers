"""Shared mock implementations for test doubles.

L3 Responsibilities / L4 Abstractions: Extract mock classes from individual
test files into a shared module to reduce duplication.

These mocks implement the driven port interfaces for testing without
external dependencies like LibreOffice or filesystem operations.
"""

from pathlib import Path
from typing import Optional

from .constants import (
    DEFAULT_HTML_URL,
    DEFAULT_PDF_URL,
    PDF_TEST_CONTENT,
)


class MockDocumentRenderer:
    """Mock document renderer for acceptance tests.

    Produces valid PDF/HTML structures without LibreOffice dependency.
    Captures rendered content for test assertions.
    """

    def __init__(self) -> None:
        self.captured_merged_content: str = ""
        self.captured_pdf_bytes: bytes = b""
        self.captured_html_content: str = ""

    def render_pdf(self, merged_content) -> "RenderedDocument":
        """Generate mock PDF with merged content."""
        from voucher_merger.ports.document_renderer import RenderedDocument

        self.captured_merged_content = merged_content.html
        pdf_content = PDF_TEST_CONTENT
        self.captured_pdf_bytes = pdf_content

        return RenderedDocument(
            content=pdf_content,
            filename="voucher.pdf",
        )

    def render_html(self, merged_content) -> "RenderedHtmlDocument":
        """Generate mock HTML with merged content."""
        from voucher_merger.ports.document_renderer import RenderedHtmlDocument

        self.captured_merged_content = merged_content.html
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Voucher</title></head>
<body style="font-family: Arial;">{merged_content.html}</body>
</html>"""
        self.captured_html_content = html_content

        return RenderedHtmlDocument(
            content=html_content,
            filename="voucher.html",
        )


class MockVoucherStorage:
    """Mock voucher storage for acceptance tests.

    Stores vouchers in memory and returns predictable URLs.
    Supports idempotency checking via find_existing.
    """

    def __init__(self, base_url: str = DEFAULT_PDF_URL.rsplit("/", 1)[0]) -> None:
        self._base_url = base_url
        self._stored_vouchers: dict = {}

    def find_existing(self) -> Optional[dict]:
        """Check for existing voucher (no existing by default)."""
        return None

    def store(self, document) -> "StorageUrl":
        """Store PDF and return URL."""
        from voucher_merger.ports.voucher_storage import StorageUrl
        return StorageUrl(url=DEFAULT_PDF_URL)

    def store_html(self, document) -> "StorageUrl":
        """Store HTML and return URL."""
        from voucher_merger.ports.voucher_storage import StorageUrl
        return StorageUrl(url=DEFAULT_HTML_URL)


class FailingStorage:
    """Storage that always fails - for 503 error testing."""

    def find_existing(self) -> None:
        """No existing vouchers."""
        return None

    def store(self, document) -> None:
        """Raise StorageError to simulate unavailability."""
        from voucher_merger.ports.voucher_storage import StorageError
        raise StorageError("Storage service unavailable")

    def store_html(self, document) -> None:
        """Raise StorageError to simulate unavailability."""
        from voucher_merger.ports.voucher_storage import StorageError
        raise StorageError("Storage service unavailable")


class InMemoryTemplateRepository:
    """In-memory template repository for isolated testing.

    Allows adding/removing templates dynamically during tests.
    Supports marking templates as corrupted for error testing.
    """

    def __init__(self) -> None:
        self._templates: dict[str, str] = {}
        self._corrupted: set[str] = set()

    def add_template(self, template_id: str, content: str) -> None:
        """Add a template with given content."""
        self._templates[template_id] = content

    def mark_corrupted(self, template_id: str) -> None:
        """Mark a template as corrupted for error testing."""
        self._corrupted.add(template_id)

    def find_by_id(self, template_id: str):
        """Find template by ID."""
        from voucher_merger.ports.template_repository import Template

        if template_id in self._corrupted:
            raise ValueError(f"Template '{template_id}' is corrupted")

        content = self._templates.get(template_id)
        if content is None:
            return None
        return Template(template_id=template_id, content=content)


def create_standard_template_content() -> str:
    """Return standard template content for testing."""
    return "<p>Dear {{customer.first_name}} {{customer.last_name}}, your transfer is confirmed.</p>"
