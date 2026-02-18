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

    def test_preserves_formatted_html_content_in_conversion(self) -> None:
        """render_pdf writes formatted HTML (tables, bold, colors) to temp file for LibreOffice.

        Step 03-01: Verify that HTML with formatting elements (tables, bold text,
        inline styles for colors) is correctly passed through to LibreOffice.
        """
        formatted_html = """<!DOCTYPE html>
<html>
<head><style>
    .provider { font-weight: bold; color: #003366; }
    table { border-collapse: collapse; }
    td { border: 1px solid #ccc; padding: 8px; }
</style></head>
<body>
    <table>
        <tr><td>Pickup</td><td>Heathrow Terminal 5</td></tr>
        <tr><td>Provider</td><td class="provider">CityLink Transfers Ltd</td></tr>
    </table>
</body>
</html>"""
        merged_content = MergedContent(html=formatted_html)
        fake_pdf_bytes = b"%PDF-1.4 fake pdf with formatting"
        captured_html_content = []

        def simulate_libreoffice_preserving_format(cmd, **kwargs):
            """Simulate LibreOffice conversion, capturing input HTML."""
            outdir_index = cmd.index("--outdir") + 1
            output_dir = cmd[outdir_index]
            input_path = cmd[-1]

            # Capture what was written to the input file
            html_content = Path(input_path).read_text(encoding="utf-8")
            captured_html_content.append(html_content)

            # Create fake PDF output
            input_name = Path(input_path).name
            output_name = input_name.replace(".html", ".pdf")
            output_path = Path(output_dir) / output_name
            output_path.write_bytes(fake_pdf_bytes)

            return MagicMock(returncode=0)

        with patch(
            "voucher_merger.adapters.libreoffice_renderer.subprocess.run"
        ) as mock_run:
            mock_run.side_effect = simulate_libreoffice_preserving_format

            renderer = LibreOfficeRenderer()
            result = renderer.render_pdf(merged_content)

            # Verify PDF was produced
            assert result.content == fake_pdf_bytes

            # Verify the formatted HTML was preserved in the input file
            assert len(captured_html_content) == 1
            written_html = captured_html_content[0]

            # Table structure preserved
            assert "<table>" in written_html
            assert "<tr>" in written_html
            assert "<td>" in written_html

            # Bold styling preserved
            assert "font-weight: bold" in written_html

            # Color styling preserved
            assert "#003366" in written_html

            # Content preserved
            assert "CityLink Transfers Ltd" in written_html
            assert "Heathrow Terminal 5" in written_html


class TestLibreOfficeRendererHtmlGeneration:
    """Tests for LibreOfficeRenderer HTML generation.

    Test Budget: 2 behaviors x 2 = 4 unit tests max
    - Behavior 1: Generates email-compatible HTML with inline CSS
    - Behavior 2: Embeds images as base64 data URIs
    """

    def test_renders_html_with_inline_css(self) -> None:
        """render_html returns RenderedHtmlDocument with inline CSS.

        Step 03-02: HTML generation must use inline styles for email compatibility.
        External stylesheets are blocked by most email clients.
        """
        from voucher_merger.ports.document_renderer import RenderedHtmlDocument

        # HTML with external stylesheet references
        merged_content = MergedContent(
            html="""<html>
<head>
<style>
    .provider { font-weight: bold; color: #003366; }
    table { border-collapse: collapse; }
</style>
</head>
<body>
    <div class="provider">CityLink Transfers Ltd</div>
    <table><tr><td>Service Details</td></tr></table>
</body>
</html>"""
        )

        renderer = LibreOfficeRenderer()
        result = renderer.render_html(merged_content)

        # Verify result type
        assert isinstance(result, RenderedHtmlDocument)
        assert result.filename.endswith(".html")

        # Verify inline CSS (style attributes present)
        html_content = result.content
        assert 'style="' in html_content, "HTML should contain inline style attributes"

        # Verify no external stylesheet links
        assert '<link' not in html_content.lower() or 'stylesheet' not in html_content.lower(), \
            "HTML should not contain external stylesheet links"

        # Verify valid HTML5 structure
        assert '<!DOCTYPE html>' in html_content or '<!doctype html>' in html_content.lower()

    def test_embeds_images_as_base64_data_uris(self) -> None:
        """render_html embeds images as base64 data URIs.

        Step 03-02: Images must be embedded for offline viewing and email compatibility.
        External image URLs are typically blocked by email clients.
        """
        from voucher_merger.ports.document_renderer import RenderedHtmlDocument

        # HTML with an external image reference
        merged_content = MergedContent(
            html="""<html>
<body>
    <img src="images/logo.png" alt="Company Logo">
    <p>Welcome to our service</p>
</body>
</html>"""
        )

        renderer = LibreOfficeRenderer()
        result = renderer.render_html(merged_content)

        assert isinstance(result, RenderedHtmlDocument)

        html_content = result.content

        # Verify no external image URLs remain
        import re
        external_img_urls = re.findall(r'src=["\']https?://', html_content)
        file_img_urls = re.findall(r'src=["\']images/', html_content)
        assert len(external_img_urls) == 0, "Should not contain external image URLs"
        assert len(file_img_urls) == 0, "Should not contain file path image URLs"

        # If images exist, they should use data: URIs or be removed
        img_tags = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html_content)
        for src in img_tags:
            assert src.startswith('data:image/') or src == '', \
                f"Image src should be base64 data URI, got: {src}"
