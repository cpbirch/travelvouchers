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


@dataclass(frozen=True)
class RenderedHtmlDocument:
    """Rendered HTML document for email compatibility.

    Attributes:
        content: The HTML content as string with inline CSS.
        filename: Suggested filename for the document.
    """

    content: str
    filename: str


class DocumentRenderer(Protocol):
    """Driven port for rendering documents to PDF and HTML.

    This port defines the contract for converting merged HTML content
    into PDF and email-compatible HTML documents. Adapters implementing
    this port may use various libraries (LibreOffice, WeasyPrint, etc.).
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

    def render_html(self, merged_content: MergedContent) -> RenderedHtmlDocument:
        """Render merged content to email-compatible HTML.

        Generates HTML with inline CSS (no external stylesheets) and
        embedded images as base64 data URIs for email compatibility.

        Args:
            merged_content: The merged HTML content to render.

        Returns:
            The rendered HTML document with inline styles.

        Raises:
            RenderingError: If the content cannot be rendered to HTML.
        """
        ...
