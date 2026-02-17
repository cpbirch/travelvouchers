"""Port interface for document rendering."""

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class MergedContent:
    """Merged template content ready for rendering.

    Attributes:
        html: The HTML content with all placeholders replaced.
    """

    html: str


@dataclass(frozen=True)
class RenderedDocument:
    """Rendered PDF document.

    Attributes:
        content: The PDF content as bytes.
        filename: Suggested filename for the document.
    """

    content: bytes
    filename: str


class DocumentRenderer(Protocol):
    """Driven port for rendering documents to PDF.

    This port defines the contract for converting merged HTML content
    into PDF documents. Adapters implementing this port may use various
    PDF generation libraries (WeasyPrint, wkhtmltopdf, etc.).
    """

    def render_pdf(self, merged_content: MergedContent) -> RenderedDocument:
        """Render merged content to a PDF document.

        Args:
            merged_content: The merged HTML content to render.

        Returns:
            The rendered PDF document.

        Raises:
            RenderingError: If the content cannot be rendered to PDF.
        """
        ...
