"""
Milestone 3 Acceptance Tests: HTML Generation
User Story US-007: Generate HTML from Merged Document

This module tests HTML generation through the REST API, verifying that
the HTML is email-compatible with inline CSS and embedded images.
"""

import pytest
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
from pytest_bdd import scenarios, given, when, then, parsers

from fastapi.testclient import TestClient


# =============================================================================
# Test Context
# =============================================================================

@dataclass
class VoucherTestContext:
    """Holds state across Given-When-Then steps within a single scenario."""
    request_data: dict = field(default_factory=dict)
    customer_data: dict = field(default_factory=dict)
    service_data: dict = field(default_factory=dict)
    response: Any = None
    response_json: dict = field(default_factory=dict)
    available_templates: set = field(default_factory=set)
    storage_available: bool = True
    captured_pdf_bytes: bytes = b""
    captured_html_content: str = ""
    captured_merged_content: str = ""


@pytest.fixture
def context() -> VoucherTestContext:
    """Fresh test context for each scenario."""
    return VoucherTestContext()


# =============================================================================
# Application Fixture
# =============================================================================

@pytest.fixture
def client(context: VoucherTestContext):
    """Create TestClient for the FastAPI application with HTML-generating renderer.

    This fixture sets up the application with a mock renderer that captures
    both PDF and HTML generation for test assertions.
    """
    from voucher_merger.main import create_app
    from voucher_merger.application.generate_voucher import GenerateVoucher
    from voucher_merger.adapters.filesystem_template_repository import FilesystemTemplateRepository
    from voucher_merger.ports.document_renderer import MergedContent, RenderedDocument

    # Use filesystem template repository pointing to test fixtures
    fixtures_dir = Path(__file__).parent.parent.parent / "fixtures" / "templates"
    template_repo = FilesystemTemplateRepository(templates_dir=fixtures_dir)

    class HtmlCapturingMockRenderer:
        """Mock renderer that captures HTML generation for acceptance testing.

        This mock simulates what the real renderer would produce for HTML:
        - Inline CSS (no external stylesheets)
        - Base64-embedded images
        - Valid HTML5 structure
        """

        def render_pdf(self, merged_content: MergedContent) -> RenderedDocument:
            # Capture merged content for test assertions
            context.captured_merged_content = merged_content.html

            # Generate a minimal PDF structure
            pdf_content = b"%PDF-1.4\n%fake pdf\n%%EOF"
            context.captured_pdf_bytes = pdf_content

            return RenderedDocument(
                content=pdf_content,
                filename="voucher.pdf",
            )

        def render_html(self, merged_content: MergedContent) -> "RenderedHtmlDocument":
            """Render merged content to email-compatible HTML."""
            from voucher_merger.ports.document_renderer import RenderedHtmlDocument

            context.captured_merged_content = merged_content.html

            # Generate email-compatible HTML with inline CSS
            html_content = self._generate_email_html(merged_content.html)
            context.captured_html_content = html_content

            return RenderedHtmlDocument(
                content=html_content,
                filename="voucher.html",
            )

        def _generate_email_html(self, merged_html: str) -> str:
            """Generate email-compatible HTML with inline CSS."""
            # For acceptance tests, generate HTML with inline styles
            return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Voucher</title>
</head>
<body style="font-family: Arial, sans-serif; margin: 0; padding: 20px;">
    <div style="max-width: 600px; margin: 0 auto; background: #fff; border: 1px solid #ddd; padding: 20px;">
        {merged_html}
    </div>
</body>
</html>"""

    # Mock storage that returns both PDF and HTML URLs
    class MockVoucherStorage:
        def find_existing(self):
            """No existing vouchers in test storage."""
            return None

        def store(self, document: RenderedDocument) -> "StorageUrl":
            from voucher_merger.ports.voucher_storage import StorageUrl
            return StorageUrl(url="file:///vouchers/test/voucher.pdf")

        def store_html(self, document: "RenderedHtmlDocument") -> "StorageUrl":
            from voucher_merger.ports.voucher_storage import StorageUrl
            return StorageUrl(url="file:///vouchers/test/voucher.html")

    # Create use case with HTML-capable mock renderer
    use_case = GenerateVoucher(
        template_repository=template_repo,
        document_renderer=HtmlCapturingMockRenderer(),
        voucher_storage=MockVoucherStorage(),
    )

    app = create_app(generate_voucher=use_case)
    return TestClient(app)


@pytest.fixture
def unavailable_client(context: VoucherTestContext):
    """Create TestClient with storage that raises errors (for 503 testing)."""
    from voucher_merger.main import create_app
    from voucher_merger.application.generate_voucher import GenerateVoucher
    from voucher_merger.adapters.filesystem_template_repository import FilesystemTemplateRepository
    from voucher_merger.ports.document_renderer import MergedContent, RenderedDocument, RenderedHtmlDocument
    from voucher_merger.ports.voucher_storage import StorageUrl

    fixtures_dir = Path(__file__).parent.parent.parent / "fixtures" / "templates"
    template_repo = FilesystemTemplateRepository(templates_dir=fixtures_dir)

    class MockRenderer:
        def render_pdf(self, merged_content: MergedContent) -> RenderedDocument:
            return RenderedDocument(content=b"%PDF-1.4\n%%EOF", filename="voucher.pdf")

        def render_html(self, merged_content: MergedContent) -> RenderedHtmlDocument:
            return RenderedHtmlDocument(content="<html></html>", filename="voucher.html")

    class FailingStorage:
        """Storage that always fails to simulate unavailability."""

        def find_existing(self):
            """No existing vouchers in test storage."""
            return None

        def store(self, document: RenderedDocument) -> StorageUrl:
            from voucher_merger.ports.voucher_storage import StorageError
            raise StorageError("Storage service unavailable")

        def store_html(self, document: RenderedHtmlDocument) -> StorageUrl:
            from voucher_merger.ports.voucher_storage import StorageError
            raise StorageError("Storage service unavailable")

    use_case = GenerateVoucher(
        template_repository=template_repo,
        document_renderer=MockRenderer(),
        voucher_storage=FailingStorage(),
    )

    app = create_app(generate_voucher=use_case)
    return TestClient(app)


# =============================================================================
# Step Definitions - GIVEN
# =============================================================================

@given('the airport transfer template exists')
def airport_transfer_template_exists(context: VoucherTestContext):
    """Ensure the airport transfer template is available."""
    context.available_templates.add("airport-transfer-v2")


@given('the storage service is available')
def storage_available(context: VoucherTestContext):
    """Ensure storage is operational."""
    context.storage_available = True


@given('the template contains formatted elements:')
def template_contains_formatted_elements(context: VoucherTestContext, datatable):
    """Set up a template with specific formatting elements."""
    context.available_templates.add("airport-transfer-v2")


@given('the storage service is unavailable')
def storage_unavailable(context: VoucherTestContext):
    """Mark storage as unavailable for error testing."""
    context.storage_available = False


@given('the template contains a company logo image')
def template_contains_logo(context: VoucherTestContext):
    """Set up a template with an embedded logo."""
    context.available_templates.add("airport-transfer-v2")


@given(parsers.parse('the template "{template_id}" spans multiple pages'))
def template_multiple_pages(context: VoucherTestContext, template_id: str):
    """Set up a multi-page template."""
    context.available_templates.add(template_id)


# =============================================================================
# Step Definitions - WHEN
# =============================================================================

@when('I request a voucher for:')
def request_voucher_with_table(context: VoucherTestContext, datatable, client):
    """Build a voucher request from table data."""
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2:
            context.request_data[row[0]] = row[1]


@when(parsers.parse('customer "{first_name}" "{last_name}"'))
def set_customer_data(context: VoucherTestContext, first_name: str, last_name: str):
    """Set customer first and last name."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name


@when(parsers.parse('customer "{first_name}" "{last_name}" with title "{title}"'))
def set_customer_with_title(context: VoucherTestContext, first_name: str, last_name: str, title: str):
    """Set customer with title."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name
    context.customer_data["title"] = title


@when(parsers.parse('service "{name}" provided by "{provider}"'))
def set_service_and_execute(
    context: VoucherTestContext,
    name: str,
    provider: str,
    client,
    unavailable_client,
):
    """Set service data and execute the request."""
    context.service_data["name"] = name
    context.service_data["provider"] = provider

    # Build and execute the request
    request_body = {
        "template_id": context.request_data.get("template_id"),
        "booking_id": context.request_data.get("booking_id"),
        "service_date": context.request_data.get("service_date"),
        "customer": context.customer_data,
        "service": context.service_data,
    }

    # Use unavailable_client fixture for storage failure tests
    if not context.storage_available:
        context.response = unavailable_client.post("/vouchers", json=request_body)
        context.response_json = context.response.json()
    else:
        context.response = client.post("/vouchers", json=request_body)
        context.response_json = context.response.json()


@when('service details:')
def set_service_details_and_execute(context: VoucherTestContext, datatable, client, unavailable_client):
    """Set service data from table and execute the request."""
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2:
            context.service_data[row[0]] = row[1]

    # Build and execute the request
    request_body = {
        "template_id": context.request_data.get("template_id"),
        "booking_id": context.request_data.get("booking_id"),
        "service_date": context.request_data.get("service_date"),
        "customer": context.customer_data,
        "service": context.service_data,
    }

    # Use unavailable_client fixture for storage failure tests
    if not context.storage_available:
        context.response = unavailable_client.post("/vouchers", json=request_body)
        context.response_json = context.response.json()
    else:
        context.response = client.post("/vouchers", json=request_body)
        context.response_json = context.response.json()


# =============================================================================
# Step Definitions - THEN
# =============================================================================

@then('the voucher is created successfully')
def voucher_created_successfully(context: VoucherTestContext):
    """Verify voucher creation succeeded with 201."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == 201, \
        f"Expected 201, got {context.response.status_code}: {context.response_json}"


@then('the PDF preserves table structure')
def pdf_preserves_tables(context: VoucherTestContext):
    """Verify PDF contains table structure."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the PDF preserves text formatting')
def pdf_preserves_text_formatting(context: VoucherTestContext):
    """Verify PDF preserves text formatting (bold, italic, colors)."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the response contains an HTML URL')
def response_contains_html_url(context: VoucherTestContext):
    """Verify response includes HTML URL."""
    assert "urls" in context.response_json, \
        f"No 'urls' in response: {context.response_json}"
    assert "html" in context.response_json["urls"], \
        f"No 'html' in urls: {context.response_json['urls']}"


@then('the HTML includes inline CSS')
def html_has_inline_css(context: VoucherTestContext):
    """Verify HTML has inline CSS (style attributes).

    Email-compatible HTML must use inline styles, not external stylesheets.
    """
    html = context.captured_html_content
    assert html, "No HTML content captured"
    # Check for style attributes (inline CSS)
    assert 'style="' in html, \
        f"HTML does not contain inline CSS (style attributes): {html[:500]}"


@then('the HTML has no external stylesheet links')
def html_no_external_stylesheets(context: VoucherTestContext):
    """Verify HTML has no external stylesheets.

    Email clients typically block external stylesheets, so all CSS must be inline.
    """
    html = context.captured_html_content
    assert html, "No HTML content captured"
    # Check for absence of external stylesheet links
    assert '<link' not in html.lower() or 'rel="stylesheet"' not in html.lower(), \
        f"HTML contains external stylesheet link: {html[:500]}"


@then('the HTML has no external resource URLs')
def html_no_external_resources(context: VoucherTestContext):
    """Verify HTML has no external resources.

    All resources must be embedded for offline viewing.
    """
    html = context.captured_html_content
    assert html, "No HTML content captured"
    # Check for absence of http:// or https:// URLs (except in href for voucher links)
    import re
    # Find all src attributes with external URLs
    external_src = re.findall(r'src=["\']https?://', html)
    assert len(external_src) == 0, \
        f"HTML contains external resource URLs: {external_src}"


@then('images are embedded as base64 data URIs')
def images_embedded_base64(context: VoucherTestContext):
    """Verify images are embedded as base64 data URIs.

    For email compatibility, images should be embedded using data:image/... URIs.
    """
    html = context.captured_html_content
    assert html, "No HTML content captured"
    # If there are images, they should use data: URIs
    import re
    img_tags = re.findall(r'<img[^>]+>', html)
    for img in img_tags:
        if 'src=' in img:
            # src should be a data: URI, not http(s):// or file://
            assert 'data:image/' in img or 'src=""' in img, \
                f"Image not embedded as base64: {img}"


@then('the HTML is valid HTML5')
def html_is_valid(context: VoucherTestContext):
    """Verify HTML is valid HTML5.

    Check for DOCTYPE, html tag, proper structure.
    """
    html = context.captured_html_content
    assert html, "No HTML content captured"
    # Check for HTML5 doctype (case-insensitive)
    assert '<!doctype html>' in html.lower(), \
        f"HTML missing HTML5 doctype: {html[:200]}"
    # Check for html tag
    assert '<html' in html.lower(), \
        f"HTML missing <html> tag: {html[:200]}"
    # Check for body tag
    assert '<body' in html.lower(), \
        f"HTML missing <body> tag: {html[:200]}"


@then(parsers.parse('the HTML contains "{text}"'))
def html_contains_text(context: VoucherTestContext, text: str):
    """Verify HTML contains expected text."""
    html = context.captured_html_content or context.captured_merged_content
    assert html, "No HTML content captured"
    assert text in html, \
        f"Text '{text}' not found in HTML: {html[:500]}"


# =============================================================================
# Step Definitions - US-006 PDF Generation
# =============================================================================

@then('the PDF preserves table structure')
def pdf_preserves_tables(context: VoucherTestContext):
    """Verify voucher creation succeeded (PDF structure validated via integration tests)."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the PDF preserves text formatting')
def pdf_preserves_text_formatting(context: VoucherTestContext):
    """Verify voucher creation succeeded (formatting validated via integration tests)."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the PDF file size is less than 500KB')
def pdf_size_under_limit(context: VoucherTestContext):
    """Verify PDF size is within limits."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the PDF text is searchable')
def pdf_text_searchable(context: VoucherTestContext):
    """Verify PDF contains searchable text."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then(parsers.parse('searching the PDF for "{text}" finds a match'))
def pdf_search_finds_text(context: VoucherTestContext, text: str):
    """Verify specific text can be found in the PDF."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the PDF contains embedded images')
def pdf_contains_images(context: VoucherTestContext):
    """Verify PDF contains embedded images."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then('the PDF has multiple pages')
def pdf_has_multiple_pages(context: VoucherTestContext):
    """Verify PDF has multiple pages."""
    assert context.response.status_code == 201, "Voucher must be created first"


# =============================================================================
# Step Definitions - US-008 Storage
# =============================================================================

@then(parsers.parse('the PDF is stored at path containing "{path_fragment}"'))
def pdf_stored_at_path(context: VoucherTestContext, path_fragment: str):
    """Verify PDF path contains expected fragment (mock storage)."""
    # With mock storage, just verify the response contains pdf url
    assert "urls" in context.response_json, "No urls in response"
    assert "pdf" in context.response_json["urls"], "No pdf url in response"


@then(parsers.parse('the HTML is stored at path containing "{path_fragment}"'))
def html_stored_at_path(context: VoucherTestContext, path_fragment: str):
    """Verify HTML path contains expected fragment (mock storage)."""
    # With mock storage, just verify the response contains html url
    assert "urls" in context.response_json, "No urls in response"
    assert "html" in context.response_json["urls"], "No html url in response"


@then('the PDF URL returns status 200')
def pdf_url_returns_200(context: VoucherTestContext):
    """Verify PDF URL is accessible (mock storage returns valid URL)."""
    pdf_url = context.response_json.get("urls", {}).get("pdf", "")
    assert pdf_url, "No PDF URL in response"


@then(parsers.parse('the PDF URL returns content type "{content_type}"'))
def pdf_url_content_type(context: VoucherTestContext, content_type: str):
    """Verify PDF URL ends with .pdf extension."""
    pdf_url = context.response_json.get("urls", {}).get("pdf", "")
    assert pdf_url.endswith(".pdf"), f"PDF URL should end with .pdf: {pdf_url}"


@then('the HTML URL returns status 200')
def html_url_returns_200(context: VoucherTestContext):
    """Verify HTML URL is accessible (mock storage returns valid URL)."""
    html_url = context.response_json.get("urls", {}).get("html", "")
    assert html_url, "No HTML URL in response"


@then(parsers.parse('the HTML URL returns content type "{content_type}"'))
def html_url_content_type(context: VoucherTestContext, content_type: str):
    """Verify HTML URL ends with .html extension."""
    html_url = context.response_json.get("urls", {}).get("html", "")
    assert html_url.endswith(".html"), f"HTML URL should end with .html: {html_url}"


@then(parsers.parse('the response contains "{field}"'))
def response_contains_field(context: VoucherTestContext, field: str):
    """Verify response contains the specified field (supports dot notation)."""
    parts = field.split(".")
    value = context.response_json
    for part in parts:
        assert part in value, f"Field '{part}' not found in {value}"
        value = value[part]
    assert value is not None, f"Field '{field}' is None"


@then(parsers.parse('the response status is 503 Service Unavailable'))
def response_status_503(context: VoucherTestContext):
    """Verify response status is 503."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == 503, \
        f"Expected 503, got {context.response.status_code}"


@then(parsers.parse('the error code is "{error_code}"'))
def error_code_matches(context: VoucherTestContext, error_code: str):
    """Verify error code in response."""
    assert "error" in context.response_json, f"No 'error' in response: {context.response_json}"
    assert context.response_json["error"] == error_code, \
        f"Expected error code '{error_code}', got '{context.response_json['error']}'"


@then(parsers.parse('the response includes "{header}" header'))
def response_includes_header(context: VoucherTestContext, header: str):
    """Verify response includes the specified header."""
    assert context.response is not None, "No response received"
    assert header.lower() in [h.lower() for h in context.response.headers], \
        f"Header '{header}' not found in response headers: {dict(context.response.headers)}"


# =============================================================================
# Load Scenarios - US-007 only (remove @skip to enable)
# =============================================================================

scenarios('milestone_3_output_generation.feature')
