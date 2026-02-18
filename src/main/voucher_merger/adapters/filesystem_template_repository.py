"""Filesystem template repository adapter for loading .docx and .odt templates."""

from pathlib import Path

from docx import Document
from odf.opendocument import load as load_odt

from voucher_merger.ports.template_repository import Template


class FilesystemTemplateRepository:
    """Filesystem implementation of TemplateRepository.

    This adapter loads templates from a configurable directory, supporting
    both .docx (Microsoft Word) and .odt (LibreOffice) formats.

    The templates are expected to be named as {template_id}.docx or {template_id}.odt.
    If both formats exist for the same template_id, .docx is preferred.
    """

    def __init__(self, templates_dir: Path) -> None:
        """Initialize repository with templates directory.

        Args:
            templates_dir: Path to directory containing template files.
        """
        self._templates_dir = Path(templates_dir)

    def find_by_id(self, template_id: str) -> Template | None:
        """Find a template by its identifier.

        Searches for {template_id}.docx first, then {template_id}.odt.
        Returns None if no matching template file is found.

        Args:
            template_id: Unique identifier for the template (filename without extension).

        Returns:
            The template if found, None otherwise.
        """
        if not template_id:
            return None

        # Try .docx first (preferred)
        docx_path = self._templates_dir / f"{template_id}.docx"
        if docx_path.exists():
            content = self._load_docx(docx_path)
            return Template(template_id=template_id, content=content)

        # Try .odt next
        odt_path = self._templates_dir / f"{template_id}.odt"
        if odt_path.exists():
            content = self._load_odt(odt_path)
            return Template(template_id=template_id, content=content)

        return None

    def _load_docx(self, path: Path) -> str:
        """Load content from a .docx file.

        Extracts text content from all paragraphs while preserving
        placeholder markers like {{customer.name}}.

        Args:
            path: Path to the .docx file.

        Returns:
            Extracted text content as HTML-like markup.
        """
        doc = Document(path)
        paragraphs = []

        for para in doc.paragraphs:
            text = para.text.strip()
            if text:
                # Determine if this is a heading based on style
                style_name = para.style.name if para.style else ""
                if "Heading" in style_name or "Title" in style_name:
                    level = 1 if "1" in style_name or "Title" in style_name else 2
                    paragraphs.append(f"<h{level}>{text}</h{level}>")
                else:
                    paragraphs.append(f"<p>{text}</p>")

        return "\n".join(paragraphs)

    def _load_odt(self, path: Path) -> str:
        """Load content from an .odt file.

        Extracts text content from all paragraphs while preserving
        placeholder markers like {{customer.name}}.

        Args:
            path: Path to the .odt file.

        Returns:
            Extracted text content as HTML-like markup.
        """
        doc = load_odt(str(path))
        paragraphs = []

        for element in doc.text.childNodes:
            if element.qname[1] == "h":
                # Heading element
                text = self._extract_odt_text(element)
                if text:
                    level = element.getAttribute("outlinelevel") or 1
                    paragraphs.append(f"<h{level}>{text}</h{level}>")
            elif element.qname[1] == "p":
                # Paragraph element
                text = self._extract_odt_text(element)
                if text:
                    paragraphs.append(f"<p>{text}</p>")

        return "\n".join(paragraphs)

    def _extract_odt_text(self, element) -> str:
        """Extract text content from an ODF element.

        Args:
            element: ODF element (P, H, etc.)

        Returns:
            Text content of the element.
        """
        text_parts = []
        for node in element.childNodes:
            if hasattr(node, "data"):
                text_parts.append(node.data)
            elif hasattr(node, "childNodes"):
                text_parts.append(self._extract_odt_text(node))
        return "".join(text_parts).strip()
