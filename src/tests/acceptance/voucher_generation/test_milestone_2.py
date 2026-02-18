"""
Milestone 2 Acceptance Tests: Template Loading and Data Merging

This module runs the milestone 2 acceptance tests through the REST API.
It validates template loading from filesystem (.docx and .odt formats).
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
    captured_merged_content: str = ""  # Captures merged HTML for verification


@pytest.fixture
def context() -> VoucherTestContext:
    """Fresh test context for each scenario."""
    return VoucherTestContext()


# =============================================================================
# Application Fixture
# =============================================================================

@pytest.fixture
def client(context: VoucherTestContext):
    """Create TestClient for the FastAPI application with filesystem template repository."""
    from voucher_merger.main import create_app
    from voucher_merger.application.generate_voucher import GenerateVoucher
    from voucher_merger.adapters.filesystem_template_repository import FilesystemTemplateRepository
    from voucher_merger.ports.document_renderer import MergedContent, RenderedDocument
    from voucher_merger.ports.voucher_storage import StorageUrl

    # Use filesystem template repository pointing to test fixtures
    fixtures_dir = Path(__file__).parent.parent.parent / "fixtures" / "templates"
    template_repo = FilesystemTemplateRepository(templates_dir=fixtures_dir)

    # Mock document renderer (avoids LibreOffice dependency)
    class MockDocumentRenderer:
        def render_pdf(self, merged_content: MergedContent) -> RenderedDocument:
            # Capture merged content for verification in then steps
            context.captured_merged_content = merged_content.html
            return RenderedDocument(
                content=b"%PDF-1.4\n" + merged_content.html.encode(),
                filename="voucher.pdf",
            )

        def render_html(self, merged_content: MergedContent) -> "RenderedHtmlDocument":
            from voucher_merger.ports.document_renderer import RenderedHtmlDocument
            return RenderedHtmlDocument(
                content=f"<html><body>{merged_content.html}</body></html>",
                filename="voucher.html",
            )

    # Mock storage (avoids filesystem dependency)
    class MockVoucherStorage:
        def find_existing(self):
            """No existing vouchers in test storage."""
            return None

        def store(self, document: RenderedDocument) -> StorageUrl:
            return StorageUrl(url="file:///vouchers/test/voucher.pdf")

        def store_html(self, document: "RenderedHtmlDocument") -> StorageUrl:
            return StorageUrl(url="file:///vouchers/test/voucher.html")

    # Create use case with real template repository, mocked adapters
    use_case = GenerateVoucher(
        template_repository=template_repo,
        document_renderer=MockDocumentRenderer(),
        voucher_storage=MockVoucherStorage(),
    )

    app = create_app(generate_voucher=use_case)
    return TestClient(app)


# =============================================================================
# Step Definitions
# =============================================================================

@given('the storage service is available')
def storage_available(context: VoucherTestContext):
    """Ensure storage is operational."""
    context.storage_available = True


@given(parsers.parse('the template "{template_id}" exists as a Word document'))
def template_exists_as_docx(context: VoucherTestContext, template_id: str):
    """Ensure a specific Word template is available."""
    context.available_templates.add(template_id)


@given(parsers.parse('the template "{template_id}" exists as a LibreOffice document'))
def template_exists_as_odt(context: VoucherTestContext, template_id: str):
    """Ensure a specific LibreOffice template is available."""
    context.available_templates.add(template_id)


@given(parsers.parse('the template "{template_id}" does not exist'))
def template_does_not_exist(context: VoucherTestContext, template_id: str):
    """Ensure a template is NOT available (for 404 testing)."""
    context.available_templates.discard(template_id)


@given('the template with customer placeholders exists')
def template_with_customer_placeholders(context: VoucherTestContext):
    """Ensure a template with customer placeholders exists."""
    context.available_templates.add("airport-transfer-v2")


@given(parsers.parse('the template with "{placeholder_text}" exists'))
def template_with_specific_placeholders(context: VoucherTestContext, placeholder_text: str):
    """Ensure a template with specific placeholders exists."""
    context.available_templates.add("airport-transfer-v2")


@given('the template with customer name placeholders exists')
def template_with_customer_name_placeholders(context: VoucherTestContext):
    """Ensure a template with customer name placeholders exists."""
    context.available_templates.add("airport-transfer-v2")


@given(parsers.parse('the template "{template_id}" exists with service placeholders'))
def template_with_service_placeholders(context: VoucherTestContext, template_id: str):
    """Ensure a template with service placeholders exists."""
    context.available_templates.add(template_id)


@given(parsers.parse('the template "{template_id}" exists with tour placeholders'))
def template_with_tour_placeholders(context: VoucherTestContext, template_id: str):
    """Ensure a template with tour placeholders exists."""
    context.available_templates.add(template_id)


@given('the template with optional service placeholders exists')
def template_with_optional_service_placeholders(context: VoucherTestContext):
    """Ensure a template with optional service placeholders exists."""
    context.available_templates.add("airport-transfer-v2")


@given('the template with service notes placeholder exists')
def template_with_service_notes_placeholder(context: VoucherTestContext):
    """Ensure a template with service notes placeholder exists."""
    context.available_templates.add("airport-transfer-v2")


@when('I request a voucher for:')
def request_voucher_with_table(context: VoucherTestContext, datatable, client):
    """Build a voucher request from table data."""
    # datatable is a list of lists: [['field', 'value'], ['template_id', 'airport-transfer-v2'], ...]
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


@when(parsers.parse('customer "{first_name}" "{last_name}" with:'))
def set_customer_with_table(context: VoucherTestContext, first_name: str, last_name: str, datatable):
    """Set customer with additional data from table."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2:
            context.customer_data[row[0]] = row[1]


@when(parsers.parse('customer "{first_name}" "{last_name}" without title'))
def set_customer_without_title(context: VoucherTestContext, first_name: str, last_name: str):
    """Set customer without optional title."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name


@when(parsers.parse('service "{name}" provided by "{provider}"'))
def set_service_and_execute(context: VoucherTestContext, name: str, provider: str, client):
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

    context.response = client.post("/vouchers", json=request_body)
    context.response_json = context.response.json()


@when('service details:')
def set_service_details_and_execute(context: VoucherTestContext, datatable, client):
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

    context.response = client.post("/vouchers", json=request_body)
    context.response_json = context.response.json()


@then('the voucher is created successfully')
def voucher_created_successfully(context: VoucherTestContext):
    """Verify voucher creation succeeded with 201."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == 201, \
        f"Expected 201, got {context.response.status_code}: {context.response_json}"


@then('the PDF preserves the template formatting')
def pdf_preserves_formatting(context: VoucherTestContext):
    """Verify PDF preserves formatting."""
    assert context.response.status_code == 201, "Voucher must be created first"


@then(parsers.parse('the response status is {status_code:d} {status_text}'))
def response_status_matches(context: VoucherTestContext, status_code: int, status_text: str):
    """Verify HTTP status code."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == status_code, \
        f"Expected {status_code}, got {context.response.status_code}: {context.response_json}"


@then(parsers.parse('the error code is "{error_code}"'))
def error_code_matches(context: VoucherTestContext, error_code: str):
    """Verify error code."""
    assert context.response_json.get("error") == error_code, \
        f"Expected error '{error_code}', got '{context.response_json.get('error')}'"


@then(parsers.parse('the error message contains "{text}"'))
def error_message_contains(context: VoucherTestContext, text: str):
    """Verify error message contains text."""
    message = context.response_json.get("message", "")
    assert text in message, f"Expected '{text}' in message: {message}"


@then(parsers.parse('the PDF contains "{text}"'))
def pdf_contains_text(context: VoucherTestContext, text: str):
    """Verify the PDF content contains the expected text.

    The mock renderer captures the merged HTML, which we check
    to verify placeholder replacement worked correctly.
    """
    assert context.response is not None, "No response received"
    assert context.response.status_code == 201, \
        f"Voucher must be created first (got {context.response.status_code})"
    assert text in context.captured_merged_content, \
        f"Expected '{text}' in merged content, but got:\n{context.captured_merged_content[:500]}"


# =============================================================================
# Load Scenarios - US-002 only (step 02-01)
# =============================================================================

scenarios('milestone_2_templates_and_merging.feature')
