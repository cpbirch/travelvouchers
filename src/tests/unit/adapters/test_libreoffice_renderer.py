"""Unit tests for LibreOfficeRenderer adapter."""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from voucher_merger.adapters.libreoffice_renderer import (
    LibreOfficeNotFoundError,
    LibreOfficeRenderer,
    RenderingError,
)
from voucher_merger.ports.document_renderer import MergedContent, RenderedDocument


class TestLibreOfficeRenderer:
    """Tests for LibreOfficeRenderer driven port adapter.

    Test Budget: 2 behaviors x 2 = 4 unit tests max
    - Behavior 1: Renders HTML to PDF via LibreOffice subprocess
    - Behavior 2: Handles LibreOffice unavailability/errors
    """

    def test_renders_html_content_to_pdf_bytes(self) -> None:
        """render_pdf returns RenderedDocument with PDF bytes from LibreOffice."""
        merged_content = MergedContent(html="<html><body>Hello World</body></html>")
        fake_pdf_bytes = b"%PDF-1.4 fake pdf content"

        def simulate_libreoffice_conversion(cmd, **kwargs):
            """Simulate LibreOffice creating a PDF file."""
            # Find the output directory and input file from command
            outdir_index = cmd.index("--outdir") + 1
            output_dir = cmd[outdir_index]
            input_path = cmd[-1]

            # Create a fake PDF output file (LibreOffice replaces .html with .pdf)
            input_name = Path(input_path).name
            output_name = input_name.replace(".html", ".pdf")
            output_path = Path(output_dir) / output_name
            output_path.write_bytes(fake_pdf_bytes)

            return MagicMock(returncode=0)

        with patch(
            "voucher_merger.adapters.libreoffice_renderer.subprocess.run"
        ) as mock_run:
            mock_run.side_effect = simulate_libreoffice_conversion

            renderer = LibreOfficeRenderer()
            result = renderer.render_pdf(merged_content)

            assert isinstance(result, RenderedDocument)
            assert result.content == fake_pdf_bytes
            assert result.filename.endswith(".pdf")
            assert "voucher_" in result.filename

    def test_raises_rendering_error_when_conversion_fails(self) -> None:
        """render_pdf raises RenderingError when LibreOffice conversion fails."""
        merged_content = MergedContent(html="<html><body>Test</body></html>")

        with patch(
            "voucher_merger.adapters.libreoffice_renderer.subprocess.run"
        ) as mock_run:
            # Simulate subprocess failure with stderr
            error = subprocess.CalledProcessError(1, "soffice")
            error.stderr = b"conversion error"
            mock_run.side_effect = error

            renderer = LibreOfficeRenderer()

            with pytest.raises(RenderingError) as exc_info:
                renderer.render_pdf(merged_content)

            assert "exit code 1" in str(exc_info.value)

    def test_raises_libreoffice_not_found_when_executable_missing(self) -> None:
        """render_pdf raises LibreOfficeNotFoundError when soffice is not found."""
        merged_content = MergedContent(html="<html><body>Test</body></html>")

        with patch(
            "voucher_merger.adapters.libreoffice_renderer.subprocess.run"
        ) as mock_run:
            # FileNotFoundError when soffice not found
            mock_run.side_effect = FileNotFoundError("soffice not found")

            renderer = LibreOfficeRenderer()

            with pytest.raises(LibreOfficeNotFoundError) as exc_info:
                renderer.render_pdf(merged_content)

            assert "LibreOffice not found" in str(exc_info.value)
