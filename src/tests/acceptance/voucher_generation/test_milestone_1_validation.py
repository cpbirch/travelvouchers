"""
Milestone 1 Acceptance Tests: Request Validation

This module runs the milestone 1 validation acceptance tests through the REST API.
It validates request field validation with batch error reporting.
"""

import pytest
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Optional
from pytest_bdd import scenarios, given, when, then, parsers

from fastapi.testclient import TestClient


# =============================================================================
# Test Context
# =============================================================================

@dataclass
class ValidationTestContext:
    """Holds state across Given-When-Then steps within a single scenario."""
    request_data: dict = field(default_factory=dict)
    customer_data: dict = field(default_factory=dict)
    service_data: dict = field(default_factory=dict)
    response: Any = None
    response_json: dict = field(default_factory=dict)
    available_templates: set = field(default_factory=set)
    storage_available: bool = True
    # Flags for intentional missing fields
    skip_template_id: bool = False
    skip_booking_id: bool = False
    skip_customer_first_name: bool = False
    skip_customer_last_name: bool = False
    skip_service_name: bool = False
    skip_service_provider: bool = False


@pytest.fixture
def context() -> ValidationTestContext:
    """Fresh test context for each scenario."""
    return ValidationTestContext()


# =============================================================================
# Application Fixture
# =============================================================================

@pytest.fixture
def client(context: ValidationTestContext):
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

    # Mock storage (avoids filesystem dependency)
    class MockVoucherStorage:
        def store(self, document: RenderedDocument) -> StorageUrl:
            return StorageUrl(url="file:///vouchers/test/voucher.pdf")

    # Create use case with mocked adapters
    use_case = GenerateVoucher(
        template_repository=template_repo,
        document_renderer=MockDocumentRenderer(),
        voucher_storage=MockVoucherStorage(),
    )

    app = create_app(generate_voucher=use_case)
    return TestClient(app)


# =============================================================================
# Given Steps
# =============================================================================

@given('the airport transfer template exists')
def airport_transfer_template_exists(context: ValidationTestContext):
    """Ensure the airport transfer template is available."""
    context.available_templates.add("airport-transfer-v2")


@given('the storage service is available')
def storage_available(context: ValidationTestContext):
    """Ensure storage is operational."""
    context.storage_available = True


# =============================================================================
# When Steps
# =============================================================================

@when('I request a voucher with multiple validation errors:')
def request_with_multiple_errors(context: ValidationTestContext, datatable, client):
    """Build a voucher request with multiple intentional errors."""
    # Build request with specific errors based on table
    context.request_data = {
        "template_id": "airport-transfer-v2",
        "booking_id": "BK-2024-TEST",
        "service_date": "2024-03-15",  # Will be overwritten if needed
    }
    context.customer_data = {
        "first_name": "James",
        "last_name": "Morrison",
    }
    context.service_data = {
        "name": "Airport Transfer",
        "provider": "CityLink Transfers",
    }

    # Parse table for intentional errors
    for row in datatable[1:]:  # Skip header
        if len(row) >= 2:
            field_name = row[0]
            issue = row[1]

            if field_name == "customer.last_name" and issue == "missing":
                context.skip_customer_last_name = True
            elif field_name == "customer.first_name" and issue == "missing":
                context.skip_customer_first_name = True
            elif field_name == "service_date" and issue == "invalid format":
                context.request_data["service_date"] = "15-03-2024"
            elif field_name == "template_id" and issue == "missing":
                context.skip_template_id = True
            elif field_name == "booking_id" and issue == "missing":
                context.skip_booking_id = True

    # Build final customer data
    customer = {}
    if not context.skip_customer_first_name:
        customer["first_name"] = context.customer_data["first_name"]
    if not context.skip_customer_last_name:
        customer["last_name"] = context.customer_data["last_name"]

    # Build final service data
    service = {}
    if not context.skip_service_name:
        service["name"] = context.service_data["name"]
    if not context.skip_service_provider:
        service["provider"] = context.service_data["provider"]

    # Build request body
    request_body = {
        "customer": customer if customer else {},
        "service": service if service else {},
    }

    if not context.skip_template_id:
        request_body["template_id"] = context.request_data["template_id"]
    if not context.skip_booking_id:
        request_body["booking_id"] = context.request_data["booking_id"]
    if "service_date" in context.request_data:
        request_body["service_date"] = context.request_data["service_date"]

    context.response = client.post("/vouchers", json=request_body)
    context.response_json = context.response.json()


@when('I request a voucher for:')
def request_voucher_with_table(context: ValidationTestContext, datatable, client):
    """Build a voucher request from table data."""
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2:
            context.request_data[row[0]] = row[1]


@when(parsers.parse('customer "{first_name}" "{last_name}"'))
def set_customer_data(context: ValidationTestContext, first_name: str, last_name: str):
    """Set customer first and last name."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name


@when(parsers.parse('customer "{first_name}" without last name'))
def set_customer_without_last_name(context: ValidationTestContext, first_name: str):
    """Set customer with missing last name."""
    context.customer_data["first_name"] = first_name
    context.skip_customer_last_name = True


@when(parsers.parse('customer without first name "{last_name}"'))
def set_customer_without_first_name(context: ValidationTestContext, last_name: str):
    """Set customer with missing first name."""
    context.customer_data["last_name"] = last_name
    context.skip_customer_first_name = True


@when(parsers.parse('service "{name}" provided by "{provider}"'))
def set_service_and_execute(context: ValidationTestContext, name: str, provider: str, client):
    """Set service data and execute the request."""
    if not context.skip_service_name:
        context.service_data["name"] = name
    if not context.skip_service_provider:
        context.service_data["provider"] = provider

    # Build customer data
    customer = {}
    if not context.skip_customer_first_name and "first_name" in context.customer_data:
        customer["first_name"] = context.customer_data["first_name"]
    if not context.skip_customer_last_name and "last_name" in context.customer_data:
        customer["last_name"] = context.customer_data["last_name"]

    # Build service data
    service = {}
    if not context.skip_service_name and "name" in context.service_data:
        service["name"] = context.service_data["name"]
    if not context.skip_service_provider and "provider" in context.service_data:
        service["provider"] = context.service_data["provider"]

    # Build request body
    request_body = {
        "customer": customer,
        "service": service,
    }

    if not context.skip_template_id and "template_id" in context.request_data:
        request_body["template_id"] = context.request_data["template_id"]
    if not context.skip_booking_id and "booking_id" in context.request_data:
        request_body["booking_id"] = context.request_data["booking_id"]
    if "service_date" in context.request_data:
        request_body["service_date"] = context.request_data["service_date"]

    context.response = client.post("/vouchers", json=request_body)
    context.response_json = context.response.json()


@when(parsers.parse('service without name provided by "{provider}"'))
def set_service_without_name_and_execute(context: ValidationTestContext, provider: str, client):
    """Set service with missing name and execute the request."""
    context.skip_service_name = True
    context.service_data["provider"] = provider

    # Build customer data
    customer = {}
    if not context.skip_customer_first_name and "first_name" in context.customer_data:
        customer["first_name"] = context.customer_data["first_name"]
    if not context.skip_customer_last_name and "last_name" in context.customer_data:
        customer["last_name"] = context.customer_data["last_name"]

    # Build service data (no name)
    service = {"provider": provider}

    # Build request body
    request_body = {
        "customer": customer,
        "service": service,
    }

    if not context.skip_template_id and "template_id" in context.request_data:
        request_body["template_id"] = context.request_data["template_id"]
    if not context.skip_booking_id and "booking_id" in context.request_data:
        request_body["booking_id"] = context.request_data["booking_id"]
    if "service_date" in context.request_data:
        request_body["service_date"] = context.request_data["service_date"]

    context.response = client.post("/vouchers", json=request_body)
    context.response_json = context.response.json()


@when(parsers.parse('service "{name}" without provider'))
def set_service_without_provider_and_execute(context: ValidationTestContext, name: str, client):
    """Set service with missing provider and execute the request."""
    context.service_data["name"] = name
    context.skip_service_provider = True

    # Build customer data
    customer = {}
    if not context.skip_customer_first_name and "first_name" in context.customer_data:
        customer["first_name"] = context.customer_data["first_name"]
    if not context.skip_customer_last_name and "last_name" in context.customer_data:
        customer["last_name"] = context.customer_data["last_name"]

    # Build service data (no provider)
    service = {"name": name}

    # Build request body
    request_body = {
        "customer": customer,
        "service": service,
    }

    if not context.skip_template_id and "template_id" in context.request_data:
        request_body["template_id"] = context.request_data["template_id"]
    if not context.skip_booking_id and "booking_id" in context.request_data:
        request_body["booking_id"] = context.request_data["booking_id"]
    if "service_date" in context.request_data:
        request_body["service_date"] = context.request_data["service_date"]

    context.response = client.post("/vouchers", json=request_body)
    context.response_json = context.response.json()


@when('I request a voucher without template_id for:')
def request_without_template_id(context: ValidationTestContext, datatable, client):
    """Build a voucher request without template_id."""
    context.skip_template_id = True
    for row in datatable[1:]:
        if len(row) >= 2:
            context.request_data[row[0]] = row[1]


@when('I request a voucher without booking_id for:')
def request_without_booking_id(context: ValidationTestContext, datatable, client):
    """Build a voucher request without booking_id."""
    context.skip_booking_id = True
    for row in datatable[1:]:
        if len(row) >= 2:
            context.request_data[row[0]] = row[1]


@when('I send an empty voucher request')
def send_empty_request(context: ValidationTestContext, client):
    """Send a completely empty request body."""
    context.response = client.post("/vouchers", json={})
    context.response_json = context.response.json()


# =============================================================================
# Then Steps
# =============================================================================

@then(parsers.parse('the response status is {status_code:d} {status_text}'))
def response_status_matches(context: ValidationTestContext, status_code: int, status_text: str):
    """Verify HTTP status code."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == status_code, \
        f"Expected {status_code}, got {context.response.status_code}: {context.response_json}"


@then(parsers.parse('the error response contains {count:d} validation errors'))
def error_response_contains_count(context: ValidationTestContext, count: int):
    """Verify the number of validation errors in response."""
    errors = context.response_json.get("details", [])
    assert len(errors) == count, \
        f"Expected {count} validation errors, got {len(errors)}: {errors}"


@then(parsers.parse('error for "{field}" has code "{code}"'))
def error_for_field_has_code(context: ValidationTestContext, field: str, code: str):
    """Verify a specific field has a specific error code."""
    errors = context.response_json.get("details", [])
    matching_error = None
    for error in errors:
        if error.get("field") == field:
            matching_error = error
            break

    assert matching_error is not None, \
        f"No error found for field '{field}'. Errors: {errors}"
    assert matching_error.get("code") == code, \
        f"Expected code '{code}' for field '{field}', got '{matching_error.get('code')}'"


@then(parsers.parse('the error code is "{error_code}"'))
def error_code_matches(context: ValidationTestContext, error_code: str):
    """Verify the top-level error code."""
    assert context.response_json.get("error") == error_code, \
        f"Expected error code '{error_code}', got '{context.response_json.get('error')}'"


@then(parsers.parse('the error details include field "{field}"'))
def error_details_include_field(context: ValidationTestContext, field: str):
    """Verify that a specific field is mentioned in validation errors."""
    errors = context.response_json.get("details", [])
    field_found = any(error.get("field") == field for error in errors)
    assert field_found, \
        f"Field '{field}' not found in validation errors: {errors}"


@then(parsers.parse('the error message mentions "{text}"'))
def error_message_mentions(context: ValidationTestContext, text: str):
    """Verify the error message contains specific text."""
    message = context.response_json.get("message", "")
    # Also check in individual error messages
    errors = context.response_json.get("details", [])
    error_messages = [e.get("message", "") for e in errors]
    all_messages = message + " " + " ".join(error_messages)

    assert text.lower() in all_messages.lower(), \
        f"Expected '{text}' in error messages. Got: {all_messages}"


@then('the error response contains validation errors for required fields')
def error_response_contains_required_fields(context: ValidationTestContext):
    """Verify that all required fields are mentioned in validation errors."""
    errors = context.response_json.get("details", [])
    required_fields = ["template_id", "booking_id", "service_date",
                       "customer.first_name", "customer.last_name",
                       "service.name", "service.provider"]

    error_fields = [e.get("field") for e in errors]

    for req_field in required_fields:
        assert req_field in error_fields, \
            f"Required field '{req_field}' not in validation errors: {error_fields}"


# =============================================================================
# Load Scenarios
# =============================================================================

scenarios('milestone_1_validation.feature')
