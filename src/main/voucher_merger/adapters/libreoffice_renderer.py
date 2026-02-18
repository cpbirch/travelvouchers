"""LibreOffice PDF and HTML renderer adapter."""

import base64
import re
import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from voucher_merger.ports.document_renderer import (
    MergedContent,
    RenderedDocument,
    RenderedHtmlDocument,
)


class RenderingError(Exception):
    """Raised when PDF rendering fails."""

    pass


class LibreOfficeNotFoundError(Exception):
    """Raised when LibreOffice is not installed or not in PATH."""

    pass


class LibreOfficeRenderer:
    """Adapter for rendering documents to PDF using LibreOffice headless.

    This adapter implements the DocumentRenderer port using LibreOffice's
    headless mode to convert HTML content to PDF documents.

    LibreOffice must be installed and available via the 'soffice' or
    'libreoffice' command for this adapter to work.
    """

    _SOFFICE_PATHS = [
        "soffice",
        "libreoffice",
        "/Applications/LibreOffice.app/Contents/MacOS/soffice",
        "/usr/bin/soffice",
        "/usr/bin/libreoffice",
    ]

    def __init__(self, soffice_path: str | None = None) -> None:
        """Initialize the renderer.

        Args:
            soffice_path: Optional explicit path to soffice executable.
                          If not provided, common paths will be searched.
        """
        self._soffice_path = soffice_path

    def render_pdf(self, merged_content: MergedContent) -> RenderedDocument:
        """Render merged HTML content to a PDF document.

        Args:
            merged_content: The merged HTML content to render.

        Returns:
            The rendered PDF document with content bytes and filename.

        Raises:
            LibreOfficeNotFoundError: If LibreOffice is not installed.
            RenderingError: If the conversion fails.
        """
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write HTML content to temporary file
            input_filename = f"input_{uuid4().hex}.html"
            input_path = Path(temp_dir) / input_filename
            input_path.write_text(merged_content.html, encoding="utf-8")

            # Expected output filename (LibreOffice replaces extension)
            output_filename = input_filename.replace(".html", ".pdf")
            output_path = Path(temp_dir) / output_filename

            # Run LibreOffice conversion
            self._run_conversion(input_path, temp_dir)

            # Read and return the PDF
            if not output_path.exists():
                raise RenderingError(
                    f"PDF output not found at {output_path}. "
                    "LibreOffice conversion may have failed silently."
                )

            pdf_bytes = output_path.read_bytes()
            return RenderedDocument(
                content=pdf_bytes,
                filename=f"voucher_{uuid4().hex[:8]}.pdf",
            )

    def _run_conversion(self, input_path: Path, output_dir: str) -> None:
        """Run LibreOffice headless conversion.

        Args:
            input_path: Path to the input HTML file.
            output_dir: Directory for output PDF.

        Raises:
            LibreOfficeNotFoundError: If soffice executable not found.
            RenderingError: If conversion process fails.
        """
        soffice_path = self._find_soffice()

        cmd = [
            soffice_path,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            output_dir,
            str(input_path),
        ]

        try:
            subprocess.run(
                cmd,
                check=True,
                capture_output=True,
                timeout=60,
            )
        except FileNotFoundError as e:
            raise LibreOfficeNotFoundError(
                f"LibreOffice not found at '{soffice_path}'. "
                "Please install LibreOffice and ensure it is in your PATH."
            ) from e
        except subprocess.CalledProcessError as e:
            stderr_msg = ""
            if e.stderr:
                stderr_msg = e.stderr.decode("utf-8", errors="replace")
            raise RenderingError(
                f"LibreOffice conversion failed with exit code {e.returncode}. "
                f"Stderr: {stderr_msg}"
            ) from e
        except subprocess.TimeoutExpired as e:
            raise RenderingError(
                "LibreOffice conversion timed out after 60 seconds."
            ) from e

    def _find_soffice(self) -> str:
        """Find the soffice executable.

        Returns:
            Path to soffice executable.

        Raises:
            LibreOfficeNotFoundError: If executable not found.
        """
        if self._soffice_path:
            return self._soffice_path

        # Return first path - actual availability checked at runtime
        return self._SOFFICE_PATHS[0]

    def render_html(self, merged_content: MergedContent) -> RenderedHtmlDocument:
        """Render merged HTML content to email-compatible HTML.

        Generates HTML with inline CSS (no external stylesheets) and
        embedded images as base64 data URIs for email compatibility.

        Args:
            merged_content: The merged HTML content to render.

        Returns:
            The rendered HTML document with inline styles.
        """
        html = merged_content.html

        # Convert CSS styles to inline styles
        html = self._inline_css(html)

        # Embed images as base64 data URIs
        html = self._embed_images_as_base64(html)

        # Ensure valid HTML5 structure
        html = self._ensure_html5_structure(html)

        return RenderedHtmlDocument(
            content=html,
            filename=f"voucher_{uuid4().hex[:8]}.html",
        )

    def _inline_css(self, html: str) -> str:
        """Convert CSS style blocks to inline styles.

        Extracts styles from <style> blocks and applies them as inline
        style attributes on matching elements.

        Args:
            html: HTML content with potential <style> blocks.

        Returns:
            HTML with inline styles applied.
        """
        # Extract style blocks
        style_pattern = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
        style_matches = style_pattern.findall(html)

        if not style_matches:
            return html

        # Parse CSS rules from style blocks
        css_rules = {}
        for style_content in style_matches:
            # Simple CSS parser for class and element selectors
            rule_pattern = re.compile(r"([.#]?\w+)\s*\{([^}]+)\}")
            for match in rule_pattern.finditer(style_content):
                selector = match.group(1).strip()
                properties = match.group(2).strip()
                # Normalize properties
                properties = re.sub(r"\s+", " ", properties)
                css_rules[selector] = properties

        # Remove style blocks
        html = style_pattern.sub("", html)

        # Apply inline styles to elements with classes
        for selector, properties in css_rules.items():
            if selector.startswith("."):
                class_name = selector[1:]
                # Find elements with this class and add inline style
                class_pattern = re.compile(
                    rf'(<[^>]+\bclass=["\'][^"\']*\b{re.escape(class_name)}\b[^"\']*["\'][^>]*)>',
                    re.IGNORECASE,
                )
                html = class_pattern.sub(rf'\1 style="{properties}">', html)

        return html

    def _embed_images_as_base64(self, html: str) -> str:
        """Embed external image references as base64 data URIs.

        Finds img tags with src attributes pointing to local files
        and replaces them with base64-encoded data URIs.

        Args:
            html: HTML content with potential image references.

        Returns:
            HTML with images embedded as data URIs.
        """
        # Find all img tags with src attributes
        img_pattern = re.compile(
            r'(<img[^>]+src=["\'])([^"\']+)(["\'][^>]*>)', re.IGNORECASE
        )

        def replace_image(match: re.Match) -> str:
            prefix = match.group(1)
            src = match.group(2)
            suffix = match.group(3)

            # Skip if already a data URI or external URL
            if src.startswith("data:") or src.startswith("http"):
                if src.startswith("http"):
                    # Remove external URLs for email compatibility
                    return f'{prefix}{suffix}'
                return match.group(0)

            # Try to read and embed the image file
            try:
                # Determine MIME type from extension
                extension = Path(src).suffix.lower()
                mime_types = {
                    ".png": "image/png",
                    ".jpg": "image/jpeg",
                    ".jpeg": "image/jpeg",
                    ".gif": "image/gif",
                    ".svg": "image/svg+xml",
                    ".webp": "image/webp",
                }
                mime_type = mime_types.get(extension, "image/png")

                # Read image file (if it exists in working directory)
                image_path = Path(src)
                if image_path.exists():
                    image_bytes = image_path.read_bytes()
                    base64_data = base64.b64encode(image_bytes).decode("ascii")
                    return f'{prefix}data:{mime_type};base64,{base64_data}{suffix}'
                else:
                    # Remove image if file not found
                    return f'{prefix}{suffix}'
            except (OSError, ValueError):
                # If we can't read the image, remove the src
                return f'{prefix}{suffix}'

        return img_pattern.sub(replace_image, html)

    def _ensure_html5_structure(self, html: str) -> str:
        """Ensure HTML has valid HTML5 structure.

        Adds DOCTYPE declaration and wraps content in proper html/head/body
        tags if not present.

        Args:
            html: HTML content.

        Returns:
            HTML with valid HTML5 structure.
        """
        # Check if DOCTYPE is present
        has_doctype = re.search(r"<!doctype\s+html>", html, re.IGNORECASE)
        has_html_tag = re.search(r"<html[\s>]", html, re.IGNORECASE)
        has_body_tag = re.search(r"<body[\s>]", html, re.IGNORECASE)

        if has_doctype and has_html_tag and has_body_tag:
            return html

        # Build proper HTML5 structure
        # Extract body content if body tag exists
        if has_body_tag:
            body_match = re.search(r"<body[^>]*>(.*)</body>", html, re.DOTALL | re.IGNORECASE)
            body_content = body_match.group(1) if body_match else html
        else:
            body_content = html

        # Extract head content if present
        head_match = re.search(r"<head[^>]*>(.*)</head>", html, re.DOTALL | re.IGNORECASE)
        head_content = head_match.group(1) if head_match else ""

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voucher</title>
    {head_content}
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
    {body_content}
</body>
</html>"""
