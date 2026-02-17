"""
Acceptance Test Configuration and Fixtures

This module provides the test infrastructure for acceptance tests.
It configures the FastAPI TestClient and manages test fixtures.

Architecture Note:
- Tests invoke through the REST API (driving port) only
- Real internal services (domain, use cases) are exercised
- External adapters (storage, LibreOffice) are mocked for speed and reliability
"""

import pytest
from typing import Generator, Any
from dataclasses import dataclass, field
from datetime import datetime
from unittest.mock import MagicMock, patch
import json


# =============================================================================
# Test Context - Shared state across steps in a scenario
# =============================================================================

@dataclass
class VoucherTestContext:
    """
    Holds state across Given-When-Then steps within a single scenario.

    This is reset for each scenario to ensure test isolation.
    """
    # Request building
    request_data: dict = field(default_factory=dict)
    customer_data: dict = field(default_factory=dict)
    service_data: dict = field(default_factory=dict)

    # Response capturing
    response: Any = None
    response_json: dict = field(default_factory=dict)

    # Fixtures state
    existing_vouchers: dict = field(default_factory=dict)
    available_templates: set = field(default_factory=set)
    storage_available: bool = True

    # For assertions
    pdf_content: bytes = b""
    html_content: str = ""
    files_written: list = field(default_factory=list)
    warnings_logged: list = field(default_factory=list)


@pytest.fixture
def context() -> VoucherTestContext:
    """Fresh test context for each scenario."""
    return VoucherTestContext()


# =============================================================================
# Mock Adapters - External dependencies mocked for speed
# =============================================================================

@dataclass
class MockTemplate:
    """In-memory template for testing."""
    template_id: str
    format: str  # 'docx' or 'odt'
    content: bytes
    placeholders: list


@dataclass
class MockStoredVoucher:
    """Represents a voucher stored by mock storage."""
    voucher_id: str
    booking_id: str
    service_date: str
    template_id: str
    generated_at: str
    pdf_content: bytes
    html_content: str


class MockTemplateRepository:
    """
    Mock implementation of TemplateRepository port.

    In production, this reads from filesystem. In tests, we use
    pre-configured templates in memory for speed and control.
    """

    def __init__(self):
        self.templates: dict[str, MockTemplate] = {}
        self._setup_default_templates()

    def _setup_default_templates(self):
        """Pre-populate with test templates."""
        self.templates["skeleton-template"] = MockTemplate(
            template_id="skeleton-template",
            format="docx",
            content=b"Skeleton template: {{customer.last_name}}",
            placeholders=["customer.last_name"]
        )
        self.templates["airport-transfer-v2"] = MockTemplate(
            template_id="airport-transfer-v2",
            format="docx",
            content=b"Airport Transfer Voucher for {{customer.title}} {{customer.last_name}}",
            placeholders=[
                "customer.title", "customer.first_name", "customer.last_name",
                "service.name", "service.provider", "service.pickup_time",
                "service.pickup_location", "service.dropoff_location",
                "service.confirmation_code"
            ]
        )
        self.templates["sightseeing-tour-v1"] = MockTemplate(
            template_id="sightseeing-tour-v1",
            format="odt",
            content=b"Sightseeing Tour for {{customer.first_name}} {{customer.last_name}}",
            placeholders=[
                "customer.first_name", "customer.last_name",
                "service.name", "service.provider", "service.meeting_point",
                "service.tour_time", "service.duration"
            ]
        )

    def add_template(self, template: MockTemplate):
        """Add a test template."""
        self.templates[template.template_id] = template

    def find_by_id(self, template_id: str) -> MockTemplate | None:
        """Load template by ID."""
        return self.templates.get(template_id)

    def exists(self, template_id: str) -> bool:
        """Check if template exists."""
        return template_id in self.templates


class MockVoucherStorage:
    """
    Mock implementation of VoucherStorage port.

    In production, this writes to filesystem/S3. In tests, we store
    in memory and can verify what was written.
    """

    def __init__(self):
        self.stored_vouchers: dict[str, MockStoredVoucher] = {}
        self.is_available: bool = True
        self.files_written: list[str] = []

    def store(
        self,
        voucher_id: str,
        booking_id: str,
        service_date: str,
        template_id: str,
        pdf_content: bytes,
        html_content: str
    ) -> dict:
        """Store voucher and return URLs."""
        if not self.is_available:
            raise StorageUnavailableError("Storage service is unavailable")

        path = f"{booking_id}/{service_date}"
        self.stored_vouchers[path] = MockStoredVoucher(
            voucher_id=voucher_id,
            booking_id=booking_id,
            service_date=service_date,
            template_id=template_id,
            generated_at=datetime.utcnow().isoformat() + "Z",
            pdf_content=pdf_content,
            html_content=html_content
        )
        self.files_written.append(f"{path}/voucher.pdf")
        self.files_written.append(f"{path}/voucher.html")

        base_url = "http://test-storage.example.com/vouchers"
        return {
            "pdf": f"{base_url}/{path}/voucher.pdf",
            "html": f"{base_url}/{path}/voucher.html"
        }

    def exists(self, booking_id: str, service_date: str) -> bool:
        """Check if voucher already exists (for idempotency)."""
        path = f"{booking_id}/{service_date}"
        return path in self.stored_vouchers

    def get_existing(self, booking_id: str, service_date: str) -> MockStoredVoucher | None:
        """Get existing voucher metadata."""
        path = f"{booking_id}/{service_date}"
        return self.stored_vouchers.get(path)

    def set_unavailable(self):
        """Simulate storage failure."""
        self.is_available = False

    def set_available(self):
        """Restore storage availability."""
        self.is_available = True


class MockDocumentRenderer:
    """
    Mock implementation of DocumentRenderer port.

    In production, this uses LibreOffice. In tests, we return
    simple content that includes the merged data for verification.
    """

    def render_pdf(self, template_content: bytes, merge_data: dict) -> bytes:
        """Generate mock PDF with merged content."""
        # Create a fake PDF that contains the merged data as searchable text
        content_str = template_content.decode('utf-8', errors='replace')
        for key, value in self._flatten_dict(merge_data).items():
            placeholder = "{{" + key + "}}"
            content_str = content_str.replace(placeholder, str(value) if value else "")

        # Fake PDF header + content
        return b"%PDF-1.4\n" + content_str.encode('utf-8')

    def render_html(self, template_content: bytes, merge_data: dict) -> str:
        """Generate mock HTML with merged content."""
        content_str = template_content.decode('utf-8', errors='replace')
        for key, value in self._flatten_dict(merge_data).items():
            placeholder = "{{" + key + "}}"
            content_str = content_str.replace(placeholder, str(value) if value else "")

        return f"""<!DOCTYPE html>
<html>
<head><style>body {{ font-family: Arial; }}</style></head>
<body>{content_str}</body>
</html>"""

    def _flatten_dict(self, d: dict, parent_key: str = "") -> dict:
        """Flatten nested dict to dot-notation keys."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)


class StorageUnavailableError(Exception):
    """Raised when storage service is unavailable."""
    pass


# =============================================================================
# Fixtures for Mock Services
# =============================================================================

@pytest.fixture
def mock_template_repo() -> MockTemplateRepository:
    """Provide mock template repository."""
    return MockTemplateRepository()


@pytest.fixture
def mock_storage() -> MockVoucherStorage:
    """Provide mock voucher storage."""
    return MockVoucherStorage()


@pytest.fixture
def mock_renderer() -> MockDocumentRenderer:
    """Provide mock document renderer."""
    return MockDocumentRenderer()


# =============================================================================
# FastAPI TestClient Setup
# =============================================================================

@pytest.fixture
def app():
    """
    Create the FastAPI application with mocked adapters.

    This fixture is used when the application code exists.
    For now, it returns None as a placeholder.
    """
    # TODO: Import and configure the actual FastAPI app when implemented
    # from voucher_merger.main import create_app
    # from voucher_merger.config import Settings
    #
    # app = create_app(
    #     template_repository=mock_template_repo,
    #     voucher_storage=mock_storage,
    #     document_renderer=mock_renderer
    # )
    # return app
    return None


@pytest.fixture
def client(app):
    """
    Create a test client for the FastAPI application.

    This is the primary way tests interact with the system -
    through the REST API (driving port), not internal methods.
    """
    if app is None:
        # Return a mock client for initial test scaffolding
        return MockTestClient()

    from fastapi.testclient import TestClient
    return TestClient(app)


class MockTestClient:
    """
    Placeholder test client for scaffolding tests before implementation.

    This allows us to write and validate test scenarios before the
    production code exists. Replace with FastAPI TestClient when ready.
    """

    def post(self, url: str, json: dict = None) -> "MockResponse":
        """Simulate POST request - returns 501 Not Implemented."""
        return MockResponse(
            status_code=501,
            json_data={
                "error": "NOT_IMPLEMENTED",
                "message": "Application not yet implemented"
            }
        )

    def get(self, url: str) -> "MockResponse":
        """Simulate GET request - returns 501 Not Implemented."""
        return MockResponse(
            status_code=501,
            json_data={
                "error": "NOT_IMPLEMENTED",
                "message": "Application not yet implemented"
            }
        )


class MockResponse:
    """Mock HTTP response for test scaffolding."""

    def __init__(self, status_code: int, json_data: dict = None, headers: dict = None):
        self.status_code = status_code
        self._json = json_data or {}
        self.headers = headers or {}
        self.content = json.dumps(self._json).encode('utf-8')

    def json(self) -> dict:
        return self._json


# =============================================================================
# Pytest-BDD Configuration
# =============================================================================

def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    """Enhanced error reporting for BDD step failures."""
    print(f"\nStep failed: {step}")
    print(f"Scenario: {scenario.name}")
    print(f"Feature: {feature.name}")
