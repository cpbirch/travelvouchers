"""
Milestone 4 Acceptance Tests: Structured Error Responses
User Story US-011: Return Structured Error Responses

This module tests structured error response functionality through the REST API, verifying that:
- All errors include: error (code), message, correlation_id, details
- Validation errors include field-level details array
- 503 errors include retry_after field and Retry-After header
- Correlation ID is logged with all errors
"""

import pytest
import logging
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any
from pytest_bdd import given, when, then, parsers, scenario


# =============================================================================
# Test Context
# =============================================================================

@dataclass
class ErrorTestContext:
    """Holds state across Given-When-Then steps within a single scenario."""
    request_data: dict = field(default_factory=dict)
    customer_data: dict = field(default_factory=dict)
    service_data: dict = field(default_factory=dict)
    response: Any = None
    response_json: dict = field(default_factory=dict)
    storage_available: bool = True
    template_corrupted: bool = False
    captured_logs: list = field(default_factory=list)


@pytest.fixture
def context() -> ErrorTestContext:
    """Fresh test context for each scenario."""
    return ErrorTestContext()


# =============================================================================
# Application Fixture with Error Handling Support
# =============================================================================

@pytest.fixture
def storage_base_path(tmp_path: Path) -> Path:
    """Provide a temporary base path for storage tests."""
    return tmp_path


class InMemoryTemplateRepository:
    """In-memory template repository for error testing."""

    def __init__(self) -> None:
        self._templates: dict[str, str] = {}
        self._corrupted: set[str] = set()

    def add_template(self, template_id: str, content: str) -> None:
        """Add a template with given content."""
        self._templates[template_id] = content

    def mark_corrupted(self, template_id: str) -> None:
        """Mark a template as corrupted."""
        self._corrupted.add(template_id)

    def find_by_id(self, template_id: str):
        """Find template by ID."""
        from voucher_merger.ports.template_repository import Template

        if template_id in self._corrupted:
            raise ValueError(f"Template '{template_id}' is corrupted")

        content = self._templates.get(template_id)
        if content is None:
            return None
        return Template(template_id=template_id, content=content)


@pytest.fixture
def template_repo(context: ErrorTestContext) -> InMemoryTemplateRepository:
    """Create in-memory template repository."""
    repo = InMemoryTemplateRepository()
    # Add standard templates
    repo.add_template(
        "airport-transfer-v2",
        "<p>Dear {{customer.first_name}} {{customer.last_name}}, your transfer is confirmed.</p>"
    )
    context.template_repo = repo
    return repo


@pytest.fixture
def client(context: ErrorTestContext, storage_base_path: Path, template_repo: InMemoryTemplateRepository):
    """Create TestClient for the FastAPI application with error handling support."""
    from voucher_merger.main import create_app
    from voucher_merger.application.generate_voucher import GenerateVoucher
    from voucher_merger.ports.document_renderer import MergedContent, RenderedDocument, RenderedHtmlDocument
    from voucher_merger.ports.voucher_storage import StorageUrl, StorageError

    class MockRenderer:
        """Mock renderer that produces valid PDF and HTML content."""

        def render_pdf(self, merged_content: MergedContent) -> RenderedDocument:
            pdf_content = b"%PDF-1.4\n%test pdf content\n%%EOF"
            return RenderedDocument(
                content=pdf_content,
                filename="voucher.pdf",
            )

        def render_html(self, merged_content: MergedContent) -> RenderedHtmlDocument:
            html_content = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><title>Voucher</title></head>
<body style="font-family: Arial;">{merged_content.html}</body>
</html>"""
            return RenderedHtmlDocument(
                content=html_content,
                filename="voucher.html",
            )

    class MockStorage:
        """Mock storage for error testing."""

        def __init__(self, base_path: Path, context: ErrorTestContext):
            self._base_path = base_path
            self._context = context
            self._booking_id: str = ""
            self._service_date: str = ""

        def configure(self, booking_id: str, service_date: str) -> None:
            self._booking_id = booking_id
            self._service_date = service_date

        def find_existing(self) -> None:
            if not self._context.storage_available:
                raise StorageError("Storage service is temporarily unavailable")
            return None

        def store(self, document: RenderedDocument) -> StorageUrl:
            if not self._context.storage_available:
                raise StorageError("Storage service is temporarily unavailable")
            storage_dir = self._base_path / "vouchers" / self._booking_id / self._service_date
            storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = storage_dir / "voucher.pdf"
            file_path.write_bytes(document.content)
            return StorageUrl(url=f"file://{file_path}")

        def store_html(self, document: RenderedHtmlDocument) -> StorageUrl:
            if not self._context.storage_available:
                raise StorageError("Storage service is temporarily unavailable")
            storage_dir = self._base_path / "vouchers" / self._booking_id / self._service_date
            storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = storage_dir / "voucher.html"
            file_path.write_text(document.content, encoding="utf-8")
            return StorageUrl(url=f"file://{file_path}")

    storage = MockStorage(storage_base_path, context)

    # Create use case with error handling support
    use_case = GenerateVoucher(
        template_repository=template_repo,
        document_renderer=MockRenderer(),
        voucher_storage=storage,
    )

    app = create_app(generate_voucher=use_case)

    from fastapi.testclient import TestClient
    return TestClient(app)


# =============================================================================
# Step Definitions - GIVEN
# =============================================================================

@given('the airport transfer template exists')
def airport_transfer_template_exists(context: ErrorTestContext, template_repo: InMemoryTemplateRepository):
    """Ensure the airport transfer template is available."""
    # Template is already added in fixture
    pass


@given('the storage service is available')
def storage_available(context: ErrorTestContext):
    """Ensure storage is operational."""
    context.storage_available = True


@given('the storage service is temporarily unavailable')
def storage_temporarily_unavailable(context: ErrorTestContext):
    """Simulate temporary storage failure."""
    context.storage_available = False


@given(parsers.parse('the template "{template_id}" exists but is corrupted'))
def template_is_corrupted(context: ErrorTestContext, template_id: str, template_repo: InMemoryTemplateRepository):
    """Set up a corrupted template for error testing."""
    template_repo.add_template(template_id, "<p>Test content</p>")
    template_repo.mark_corrupted(template_id)
    context.template_corrupted = True


# =============================================================================
# Step Definitions - WHEN
# =============================================================================

@when('I request a voucher for:')
def request_voucher_with_table(context: ErrorTestContext, datatable):
    """Build a voucher request from table data."""
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2:
            context.request_data[row[0]] = row[1]


@when(parsers.parse('customer "{first_name}" "{last_name}"'))
def set_customer_data(context: ErrorTestContext, first_name: str, last_name: str):
    """Set customer first and last name."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name


@when(parsers.parse('service "{name}" provided by "{provider}"'))
def set_service_and_execute(
    context: ErrorTestContext,
    name: str,
    provider: str,
    client,
    caplog,
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

    with caplog.at_level(logging.DEBUG):
        context.response = client.post("/vouchers", json=request_body)
        context.response_json = context.response.json()
        context.captured_logs = list(caplog.records)


@when('I request a voucher with missing customer last_name')
def request_missing_last_name(context: ErrorTestContext, client, caplog):
    """Request with missing customer.last_name."""
    request_body = {
        "template_id": "airport-transfer-v2",
        "booking_id": "BK-2024-99999",
        "service_date": "2024-03-01",
        "customer": {"first_name": "Test"},
        "service": {"name": "Test", "provider": "Test"},
    }

    with caplog.at_level(logging.DEBUG):
        context.response = client.post("/vouchers", json=request_body)
        context.response_json = context.response.json()
        context.captured_logs = list(caplog.records)


@when(parsers.parse('I request a voucher with template_id "{template_id}"'))
def request_with_template_id(context: ErrorTestContext, template_id: str, client, caplog):
    """Request with specific template_id."""
    request_body = {
        "template_id": template_id,
        "booking_id": "BK-2024-99999",
        "service_date": "2024-03-01",
        "customer": {"first_name": "Test", "last_name": "User"},
        "service": {"name": "Test", "provider": "Test"},
    }

    with caplog.at_level(logging.DEBUG):
        context.response = client.post("/vouchers", json=request_body)
        context.response_json = context.response.json()
        context.captured_logs = list(caplog.records)


@when(parsers.parse('I request a voucher with service_date "{service_date}"'))
def request_with_service_date(context: ErrorTestContext, service_date: str, client, caplog):
    """Request with specific service_date."""
    request_body = {
        "template_id": "airport-transfer-v2",
        "booking_id": "BK-2024-99999",
        "service_date": service_date,
        "customer": {"first_name": "Test", "last_name": "User"},
        "service": {"name": "Test", "provider": "Test"},
    }

    with caplog.at_level(logging.DEBUG):
        context.response = client.post("/vouchers", json=request_body)
        context.response_json = context.response.json()
        context.captured_logs = list(caplog.records)


@when('I request a voucher with invalid data')
def request_with_invalid_data(context: ErrorTestContext, client, caplog):
    """Request with some invalid data (missing required fields)."""
    request_body = {
        "template_id": "airport-transfer-v2",
        "booking_id": "BK-2024-99999",
        "service_date": "invalid",
        "customer": {"first_name": "Test"},  # Missing last_name
        "service": {"name": "Test"},  # Missing provider
    }

    with caplog.at_level(logging.DEBUG):
        context.response = client.post("/vouchers", json=request_body)
        context.response_json = context.response.json()
        context.captured_logs = list(caplog.records)


# =============================================================================
# Step Definitions - THEN
# =============================================================================

@then(parsers.parse('the response status is {status_code:d} {status_text}'))
def response_status_matches(context: ErrorTestContext, status_code: int, status_text: str):
    """Verify HTTP status code."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == status_code, \
        f"Expected {status_code}, got {context.response.status_code}: {context.response_json}"


@then('the error response contains:')
def error_response_contains_fields(context: ErrorTestContext, datatable):
    """Verify error response contains expected fields with correct types."""
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2:
            field_name = row[0]
            expected_type = row[1]

            assert field_name in context.response_json, \
                f"Field '{field_name}' not in error response: {context.response_json}"

            value = context.response_json[field_name]

            if expected_type == "string":
                assert isinstance(value, str), \
                    f"Field '{field_name}' should be string, got {type(value).__name__}"
            elif expected_type == "array":
                assert isinstance(value, list), \
                    f"Field '{field_name}' should be array, got {type(value).__name__}"
            elif expected_type == "TEMPLATE_NOT_FOUND":
                assert value == "TEMPLATE_NOT_FOUND", \
                    f"Field '{field_name}' should be 'TEMPLATE_NOT_FOUND', got '{value}'"


@then('the error response contains a correlation_id')
def error_has_correlation_id(context: ErrorTestContext):
    """Verify error has correlation_id."""
    assert "correlation_id" in context.response_json, \
        f"No correlation_id in error response: {context.response_json}"
    assert isinstance(context.response_json["correlation_id"], str), \
        "correlation_id should be a string"
    assert len(context.response_json["correlation_id"]) > 0, \
        "correlation_id should not be empty"


@then(parsers.parse('the error response contains "{field}" as integer'))
def error_contains_integer_field(context: ErrorTestContext, field: str):
    """Verify field is an integer."""
    assert field in context.response_json, \
        f"Field '{field}' not in error response: {context.response_json}"
    assert isinstance(context.response_json[field], int), \
        f"Field '{field}' should be integer, got {type(context.response_json[field]).__name__}"


@then(parsers.parse('the response header "{header}" is present'))
def header_is_present(context: ErrorTestContext, header: str):
    """Verify header is present."""
    assert header in context.response.headers, \
        f"Header '{header}' not in response headers: {dict(context.response.headers)}"


@then('the correlation_id is logged with the error')
def correlation_id_logged(context: ErrorTestContext):
    """Verify correlation_id was logged."""
    correlation_id = context.response_json.get("correlation_id")
    assert correlation_id is not None, "No correlation_id in response"

    # Check if correlation_id appears in any log record
    log_messages = [record.message for record in context.captured_logs]
    found = any(correlation_id in msg for msg in log_messages)

    assert found, \
        f"Correlation ID '{correlation_id}' not found in logs: {log_messages}"


@then(parsers.parse('the error code is "{error_code}"'))
def error_code_matches(context: ErrorTestContext, error_code: str):
    """Verify error code."""
    assert context.response_json.get("error") == error_code, \
        f"Expected error '{error_code}', got '{context.response_json.get('error')}'"


@then('the error message is human-readable')
def error_message_readable(context: ErrorTestContext):
    """Verify error message is human-readable."""
    message = context.response_json.get("message", "")
    assert len(message) > 10, f"Error message too short to be helpful: '{message}'"
    # Should contain words, not just codes
    assert any(c.isalpha() for c in message), "Error message should contain words"


@then('the error message explains what was wrong')
def error_message_explains(context: ErrorTestContext):
    """Verify error message explains the problem."""
    message = context.response_json.get("message", "")
    assert len(message) > 0, "Error message is empty"
    # Should be descriptive
    assert " " in message, "Error message should be a phrase, not a single word"


# =============================================================================
# Load Scenarios - US-011 only (structured error scenarios)
# =============================================================================

@scenario(
    'milestone_4_robustness.feature',
    'Validation error has consistent structure'
)
def test_us011_validation_error_structure():
    """US-011: Validation error has consistent structure."""
    pass


@scenario(
    'milestone_4_robustness.feature',
    'Template not found error has consistent structure'
)
def test_us011_template_not_found_structure():
    """US-011: Template not found error has consistent structure."""
    pass


@scenario(
    'milestone_4_robustness.feature',
    'Storage error includes retry guidance'
)
def test_us011_storage_error_retry():
    """US-011: Storage error includes retry guidance."""
    pass


@scenario(
    'milestone_4_robustness.feature',
    'All error responses include correlation ID'
)
def test_us011_correlation_id():
    """US-011: All error responses include correlation ID."""
    pass


@scenario(
    'milestone_4_robustness.feature',
    'Corrupted template returns 500 with error details'
)
def test_us011_corrupted_template():
    """US-011: Corrupted template returns 500 with error details."""
    pass


@scenario(
    'milestone_4_robustness.feature',
    'Error message is human-readable'
)
def test_us011_human_readable_error():
    """US-011: Error message is human-readable."""
    pass
