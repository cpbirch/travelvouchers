"""
Milestone 4 Acceptance Tests: Placeholder Validation
User Story US-003: Validate Template Placeholders Against Schema

This module tests placeholder validation through the domain layer, verifying that:
- Unknown placeholders generate warnings but allow generation
- Typos are detected with 'Did you mean' suggestions (Levenshtein distance)
- Optional field usage generates warnings
- Valid placeholders pass without warnings
"""

import pytest
from dataclasses import dataclass, field
from typing import Any
from pathlib import Path
import logging

from pytest_bdd import scenarios, given, when, then, parsers


# =============================================================================
# Test Context
# =============================================================================

@dataclass
class ValidationTestContext:
    """Holds state across Given-When-Then steps within a single scenario."""
    template_id: str = ""
    template_content: str = ""
    request_data: dict = field(default_factory=dict)
    customer_data: dict = field(default_factory=dict)
    service_data: dict = field(default_factory=dict)
    response: Any = None
    response_json: dict = field(default_factory=dict)
    validation_result: Any = None
    captured_logs: list = field(default_factory=list)
    templates: dict = field(default_factory=dict)


@pytest.fixture
def context() -> ValidationTestContext:
    """Fresh test context for each scenario."""
    return ValidationTestContext()


# =============================================================================
# Custom Template Repository for Testing
# =============================================================================

class InMemoryTemplateRepository:
    """In-memory template repository for validation testing."""

    def __init__(self) -> None:
        self._templates: dict[str, str] = {}

    def add_template(self, template_id: str, content: str) -> None:
        """Add a template with given content."""
        self._templates[template_id] = content

    def find_by_id(self, template_id: str):
        """Find template by ID."""
        from voucher_merger.ports.template_repository import Template
        content = self._templates.get(template_id)
        if content is None:
            return None
        return Template(template_id=template_id, content=content)


# =============================================================================
# Application Fixture with Validation Support
# =============================================================================

@pytest.fixture
def storage_base_path(tmp_path: Path) -> Path:
    """Provide a temporary base path for storage tests."""
    return tmp_path


@pytest.fixture
def template_repo(context: ValidationTestContext) -> InMemoryTemplateRepository:
    """Create in-memory template repository."""
    repo = InMemoryTemplateRepository()
    context.template_repo = repo
    return repo


@pytest.fixture
def client(context: ValidationTestContext, storage_base_path: Path, template_repo: InMemoryTemplateRepository):
    """Create TestClient for the FastAPI application with validation support."""
    from voucher_merger.main import create_app
    from voucher_merger.application.generate_voucher import GenerateVoucher
    from voucher_merger.ports.document_renderer import MergedContent, RenderedDocument, RenderedHtmlDocument
    from voucher_merger.ports.voucher_storage import StorageUrl

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
        """Mock storage for validation testing."""

        def __init__(self, base_path: Path):
            self._base_path = base_path
            self._booking_id: str = ""
            self._service_date: str = ""

        def configure(self, booking_id: str, service_date: str) -> None:
            self._booking_id = booking_id
            self._service_date = service_date

        def find_existing(self) -> None:
            return None

        def store(self, document: RenderedDocument) -> StorageUrl:
            storage_dir = self._base_path / "vouchers" / self._booking_id / self._service_date
            storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = storage_dir / "voucher.pdf"
            file_path.write_bytes(document.content)
            return StorageUrl(url=f"file://{file_path}")

        def store_html(self, document: RenderedHtmlDocument) -> StorageUrl:
            storage_dir = self._base_path / "vouchers" / self._booking_id / self._service_date
            storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = storage_dir / "voucher.html"
            file_path.write_text(document.content, encoding="utf-8")
            return StorageUrl(url=f"file://{file_path}")

    storage = MockStorage(storage_base_path)

    # Create use case with validation support
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
def airport_transfer_template_exists(context: ValidationTestContext, template_repo: InMemoryTemplateRepository):
    """Ensure the airport transfer template is available."""
    template_repo.add_template(
        "airport-transfer-v2",
        "<p>Dear {{customer.first_name}} {{customer.last_name}}, your transfer is confirmed.</p>"
    )


@given('the storage service is available')
def storage_available(context: ValidationTestContext):
    """Ensure storage is operational."""
    pass


@given(parsers.parse('the template "{template_id}" contains "{content}"'))
def template_contains_content(
    context: ValidationTestContext,
    template_id: str,
    content: str,
    template_repo: InMemoryTemplateRepository
):
    """Create a template with specific content."""
    context.template_id = template_id
    context.template_content = content
    template_repo.add_template(template_id, content)


@given(parsers.parse('the template "{template_id}" contains only known placeholders:'))
def template_with_known_placeholders(
    context: ValidationTestContext,
    template_id: str,
    datatable,
    template_repo: InMemoryTemplateRepository
):
    """Create a template with only known placeholders from table."""
    placeholders = []
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 1:
            placeholders.append(row[0])

    # Build content with all the placeholders
    content = " ".join(placeholders)
    context.template_id = template_id
    context.template_content = content
    template_repo.add_template(template_id, content)


# =============================================================================
# Step Definitions - WHEN
# =============================================================================

@when('I request a voucher for:')
def request_voucher_with_table(context: ValidationTestContext, datatable):
    """Build a voucher request from table data."""
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2:
            context.request_data[row[0]] = row[1]


@when(parsers.parse('customer "{first_name}" "{last_name}"'))
def set_customer_data(context: ValidationTestContext, first_name: str, last_name: str):
    """Set customer first and last name."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name


@when(parsers.parse('service "{name}" provided by "{provider}"'))
def set_service_and_execute(
    context: ValidationTestContext,
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

    with caplog.at_level(logging.WARNING):
        context.response = client.post("/vouchers", json=request_body)
        context.response_json = context.response.json()
        context.captured_logs = list(caplog.records)


@when(parsers.parse('the template "{template_id}" is validated'))
def validate_template(context: ValidationTestContext, template_id: str, template_repo: InMemoryTemplateRepository):
    """Validate a template against the placeholder schema."""
    from voucher_merger.domain.placeholder_validator import PlaceholderValidator
    from voucher_merger.domain.template import TemplatePlaceholderExtractor

    template = template_repo.find_by_id(template_id)
    if template is None:
        raise ValueError(f"Template not found: {template_id}")

    extractor = TemplatePlaceholderExtractor()
    extracted = extractor.extract_placeholders(template.content)

    validator = PlaceholderValidator()
    context.validation_result = validator.validate(extracted)


# =============================================================================
# Step Definitions - THEN
# =============================================================================

@then('the voucher is created successfully')
def voucher_created_successfully(context: ValidationTestContext):
    """Verify voucher creation succeeded with 201."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == 201, \
        f"Expected 201, got {context.response.status_code}: {context.response_json}"


@then(parsers.parse('a warning is logged about unknown placeholder "{placeholder}"'))
def warning_logged_for_unknown_placeholder(context: ValidationTestContext, placeholder: str):
    """Verify a warning was logged about the unknown placeholder."""
    warning_messages = [
        record.message for record in context.captured_logs
        if record.levelno >= logging.WARNING
    ]

    found = any(
        placeholder in msg and "unknown" in msg.lower()
        for msg in warning_messages
    )

    assert found, \
        f"Expected warning about unknown placeholder '{placeholder}', but got: {warning_messages}"


@then(parsers.parse('validation reports unknown placeholder "{placeholder}"'))
def validation_reports_unknown(context: ValidationTestContext, placeholder: str):
    """Verify validation reports the placeholder as unknown."""
    assert context.validation_result is not None, "No validation result"

    unknown = context.validation_result.unknown_placeholders
    assert placeholder in unknown, \
        f"Expected '{placeholder}' in unknown placeholders, got: {unknown}"


@then(parsers.parse('validation suggests "Did you mean: {suggestion}?"'))
def validation_suggests(context: ValidationTestContext, suggestion: str):
    """Verify validation suggests the correct placeholder."""
    assert context.validation_result is not None, "No validation result"

    suggestions = context.validation_result.suggestions
    found = any(
        suggestion in s
        for s in suggestions.values()
    )

    assert found, \
        f"Expected suggestion containing '{suggestion}', got: {suggestions}"


@then('validation passes with no errors')
def validation_passes(context: ValidationTestContext):
    """Verify validation passes without errors."""
    assert context.validation_result is not None, "No validation result"
    assert context.validation_result.is_valid, \
        f"Expected valid, got errors: {context.validation_result.unknown_placeholders}"
    assert len(context.validation_result.unknown_placeholders) == 0, \
        f"Expected no unknown placeholders, got: {context.validation_result.unknown_placeholders}"


@then('validation passes')
def validation_passes_with_warnings(context: ValidationTestContext):
    """Verify validation passes (may have warnings)."""
    assert context.validation_result is not None, "No validation result"
    assert context.validation_result.is_valid, \
        f"Expected valid, got errors: {context.validation_result.unknown_placeholders}"


@then(parsers.parse('validation warns "{warning}"'))
def validation_warns(context: ValidationTestContext, warning: str):
    """Verify validation includes a warning."""
    assert context.validation_result is not None, "No validation result"

    warnings = context.validation_result.warnings
    found = any(warning in w for w in warnings)

    assert found, \
        f"Expected warning containing '{warning}', got: {warnings}"


# =============================================================================
# Load Scenarios - US-003 only (explicit scenario loading to avoid conflicts)
# =============================================================================

from pytest_bdd import scenario

@scenario(
    'milestone_4_robustness.feature',
    'Template with unknown placeholder logs warning but succeeds'
)
def test_us003_unknown_placeholder():
    """US-003: Unknown placeholder logs warning but succeeds."""
    pass


@scenario(
    'milestone_4_robustness.feature',
    'Template with typo in placeholder detected'
)
def test_us003_typo_detected():
    """US-003: Template with typo in placeholder detected."""
    pass


@scenario(
    'milestone_4_robustness.feature',
    'Template validation passes for all known placeholders'
)
def test_us003_valid_placeholders():
    """US-003: Template validation passes for all known placeholders."""
    pass


@scenario(
    'milestone_4_robustness.feature',
    'Template validation warns about optional fields'
)
def test_us003_optional_fields_warning():
    """US-003: Template validation warns about optional fields."""
    pass
