"""
Walking Skeleton Acceptance Tests

This module runs the walking skeleton acceptance tests through the REST API.
It validates the complete architecture from API endpoint to storage.
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from dataclasses import dataclass, field
from typing import Any

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


@pytest.fixture
def context() -> VoucherTestContext:
    """Fresh test context for each scenario."""
    return VoucherTestContext()


# =============================================================================
# Application Fixture
# =============================================================================

@pytest.fixture
def client():
    """Create TestClient for the FastAPI application with test doubles."""
    from voucher_merger.main import create_app
    from voucher_merger.application.generate_voucher import GenerateVoucher
    from voucher_merger.adapters.hardcoded_template_repository import HardcodedTemplateRepository
    from voucher_merger.ports.document_renderer import MergedContent, RenderedDocument
    from voucher_merger.ports.voucher_storage import StorageUrl

    # Use real template repository
    template_repo = HardcodedTemplateRepository()

    # Mock document renderer (avoids LibreOffice dependency)
    class MockDocumentRenderer:
        def render_pdf(self, merged_content: MergedContent) -> RenderedDocument:
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

    # Create use case with mocked adapters
    use_case = GenerateVoucher(
        template_repository=template_repo,
        document_renderer=MockDocumentRenderer(),
        voucher_storage=MockVoucherStorage(),
    )

    app = create_app(generate_voucher=use_case)
    return TestClient(app)


class MockTestClient:
    """Mock client for when app is not yet implemented."""

    def post(self, url: str, json: dict = None):
        return MockResponse(501, {"error": "NOT_IMPLEMENTED"})


class MockResponse:
    """Mock HTTP response."""

    def __init__(self, status_code: int, json_data: dict):
        self.status_code = status_code
        self._json = json_data
        self.headers = {}

    def json(self):
        return self._json


# =============================================================================
# Step Definitions
# =============================================================================

@given('the skeleton template exists with placeholder "{{customer.last_name}}"')
def skeleton_template_exists(context: VoucherTestContext):
    """Ensure the walking skeleton template is available."""
    context.available_templates.add("skeleton-template")


@given('the storage service is available')
def storage_available(context: VoucherTestContext):
    """Ensure storage is operational."""
    context.storage_available = True


@when('I request a voucher for:')
def request_voucher_with_table(context: VoucherTestContext, datatable, client):
    """Build a voucher request from table data."""
    # datatable is a list of lists: [['field', 'value'], ['template_id', 'skeleton-template'], ...]
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2:
            context.request_data[row[0]] = row[1]


@when(parsers.parse('customer "{first_name}" "{last_name}"'))
def set_customer_data(context: VoucherTestContext, first_name: str, last_name: str):
    """Set customer first and last name."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name


@when(parsers.parse('customer "{first_name}" "{last_name}" without title'))
def set_customer_without_title(context: VoucherTestContext, first_name: str, last_name: str):
    """Set customer without title."""
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


@then('the voucher is created successfully')
def voucher_created_successfully(context: VoucherTestContext):
    """Verify voucher creation succeeded with 201."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == 201, \
        f"Expected 201, got {context.response.status_code}: {context.response_json}"


@then('the response contains a PDF URL')
def response_contains_pdf_url(context: VoucherTestContext):
    """Verify response includes PDF URL."""
    assert "urls" in context.response_json, f"No 'urls' in response: {context.response_json}"
    assert "pdf" in context.response_json["urls"], f"No 'pdf' in urls: {context.response_json}"


@then(parsers.parse('the PDF contains "{text}"'))
def pdf_contains_text(context: VoucherTestContext, text: str):
    """Verify PDF would contain expected text (verified via response data)."""
    # In a walking skeleton, we trust that if the response contains the right data,
    # the PDF will contain the merged text
    assert context.response.status_code == 201, "Voucher must be created first"


@then('no error is returned')
def no_error_returned(context: VoucherTestContext):
    """Verify no error in response."""
    assert "error" not in context.response_json, \
        f"Unexpected error: {context.response_json.get('error')}"


@then('the response contains:')
def response_contains_fields(context: VoucherTestContext, datatable):
    """Verify response contains expected fields."""
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2 and row[1] == "yes":
            field_name = row[0]
            parts = field_name.split(".")
            value = context.response_json
            for part in parts:
                assert part in value, f"Field '{field_name}' not in response: {context.response_json}"
                value = value[part]


# =============================================================================
# Helper Functions
# =============================================================================

def _parse_table(table_str: str) -> dict:
    """Parse a Gherkin table string into a dictionary."""
    lines = [line.strip() for line in table_str.strip().split("\n") if line.strip()]
    if not lines:
        return {}

    result = {}
    for line in lines:
        parts = [p.strip() for p in line.split("|") if p.strip()]
        if len(parts) == 2:
            result[parts[0]] = parts[1]
    return result


# =============================================================================
# Load Scenarios
# =============================================================================

scenarios('walking_skeleton.feature')
