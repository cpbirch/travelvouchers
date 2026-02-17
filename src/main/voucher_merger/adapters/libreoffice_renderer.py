"""LibreOffice PDF renderer adapter."""

import subprocess
import tempfile
from pathlib import Path
from uuid import uuid4

from voucher_merger.ports.document_renderer import MergedContent, RenderedDocument


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
