"""
Milestone 4 Acceptance Tests: Idempotency
User Story US-009: Idempotent Voucher Generation

This module tests idempotency functionality through the REST API, verifying that:
- Duplicate requests return the original voucher (200, not 201)
- Original generated_at timestamp is preserved
- No new files are written for duplicates
- Different booking_id or service_date creates new vouchers
"""

import json
import sys
from pathlib import Path

import pytest
from pytest_bdd import scenarios, given, when, then, parsers

from fastapi.testclient import TestClient

# Add parent directory to path for shared module access
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.contexts import VoucherTestContext
from shared.constants import AIRPORT_TRANSFER_TEMPLATE_ID


@pytest.fixture
def context() -> VoucherTestContext:
    """Fresh test context for each scenario."""
    return VoucherTestContext()


# =============================================================================
# Application Fixture with Idempotency Support
# =============================================================================

@pytest.fixture
def storage_base_path(tmp_path: Path) -> Path:
    """Provide a temporary base path for storage tests."""
    return tmp_path


@pytest.fixture
def client(context: VoucherTestContext, storage_base_path: Path):
    """Create TestClient for the FastAPI application with idempotency support.

    This fixture uses real FilesystemStorage with idempotency checking.
    """
    from voucher_merger.main import create_app
    from voucher_merger.application.generate_voucher import GenerateVoucher
    from voucher_merger.adapters.filesystem_template_repository import FilesystemTemplateRepository
    from voucher_merger.adapters.filesystem_storage import FilesystemStorage
    from voucher_merger.ports.document_renderer import MergedContent, RenderedDocument, RenderedHtmlDocument
    from voucher_merger.ports.voucher_storage import StorageUrl

    # Use filesystem template repository pointing to test fixtures
    fixtures_dir = Path(__file__).parent.parent.parent / "fixtures" / "templates"
    template_repo = FilesystemTemplateRepository(templates_dir=fixtures_dir)

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

    class IdempotentStorageFactory:
        """Factory that creates storage per request with idempotency checking."""

        def __init__(self, base_path: Path):
            self._base_path = base_path
            self._booking_id: str = ""
            self._service_date: str = ""

        def configure(self, booking_id: str, service_date: str) -> None:
            self._booking_id = booking_id
            self._service_date = service_date

        def _get_storage_dir(self) -> Path:
            return self._base_path / "vouchers" / self._booking_id / self._service_date

        def find_existing(self) -> dict | None:
            """Check if a voucher already exists for this booking/date."""
            storage_dir = self._get_storage_dir()
            metadata_path = storage_dir / "metadata.json"
            if metadata_path.exists():
                import json
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            return None

        def store(self, document: RenderedDocument) -> StorageUrl:
            storage_dir = self._get_storage_dir()
            storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = storage_dir / "voucher.pdf"
            file_path.write_bytes(document.content)
            return StorageUrl(url=f"file://{file_path}")

        def store_html(self, document: RenderedHtmlDocument) -> StorageUrl:
            storage_dir = self._get_storage_dir()
            storage_dir.mkdir(parents=True, exist_ok=True)
            file_path = storage_dir / "voucher.html"
            file_path.write_text(document.content, encoding="utf-8")
            return StorageUrl(url=f"file://{file_path}")

        def store_metadata(self, metadata: dict) -> None:
            """Store voucher metadata for idempotency checking."""
            storage_dir = self._get_storage_dir()
            storage_dir.mkdir(parents=True, exist_ok=True)
            metadata_path = storage_dir / "metadata.json"
            import json
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f)

    storage_factory = IdempotentStorageFactory(storage_base_path)

    # Store a reference to the storage factory for setting up existing vouchers
    context.storage_factory = storage_factory
    context.storage_base_path = storage_base_path

    # Create use case with idempotent storage
    use_case = GenerateVoucher(
        template_repository=template_repo,
        document_renderer=MockRenderer(),
        voucher_storage=storage_factory,
    )

    app = create_app(generate_voucher=use_case)
    return TestClient(app)


# =============================================================================
# Helper Functions
# =============================================================================

def _get_all_files(base_path: Path) -> set:
    """Get all file paths under a base directory."""
    if not base_path.exists():
        return set()
    return {str(p) for p in base_path.rglob('*') if p.is_file()}


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


@given('a voucher was previously generated for:')
def voucher_previously_generated(context: VoucherTestContext, datatable, client):
    """Set up an existing voucher for idempotency testing."""
    data = {}
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2:
            data[row[0]] = row[1]

    booking_id = data['booking_id']
    service_date = data['service_date']

    # Configure storage and create an actual voucher on disk
    context.storage_factory.configure(booking_id, service_date)

    # Create the voucher files
    storage_dir = context.storage_base_path / "vouchers" / booking_id / service_date
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Write PDF and HTML files
    (storage_dir / "voucher.pdf").write_bytes(b"%PDF-1.4\n%test content\n%%EOF")
    (storage_dir / "voucher.html").write_text("<html><body>Test</body></html>")

    # Store context for later assertions
    voucher_id = f"V-{booking_id}-{service_date.replace('-', '')}"
    context.original_voucher_id = voucher_id
    context.existing_vouchers[f"{booking_id}/{service_date}"] = {
        "voucher_id": voucher_id,
        "booking_id": booking_id,
        "service_date": service_date,
    }


@given(parsers.parse('the original voucher was created at "{timestamp}"'))
def original_voucher_timestamp(context: VoucherTestContext, timestamp: str):
    """Set the timestamp for an existing voucher."""
    context.original_generated_at = timestamp

    # Write metadata with the timestamp to the storage location
    for key, voucher in context.existing_vouchers.items():
        booking_id = voucher["booking_id"]
        service_date = voucher["service_date"]
        storage_dir = context.storage_base_path / "vouchers" / booking_id / service_date

        metadata = {
            "voucher_id": voucher["voucher_id"],
            "booking_id": booking_id,
            "service_date": service_date,
            "template_id": "airport-transfer-v2",
            "generated_at": timestamp,
            "pdf_url": f"file://{storage_dir}/voucher.pdf",
            "html_url": f"file://{storage_dir}/voucher.html",
        }

        import json
        metadata_path = storage_dir / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f)

    # Capture files before request
    context.files_before_request = _get_all_files(context.storage_base_path)


@given(parsers.parse('a voucher exists for booking "{booking_id}" date "{service_date}"'))
def voucher_exists_for_booking_date(context: VoucherTestContext, booking_id: str, service_date: str, client):
    """Set up an existing voucher with specific booking/date."""
    # Configure storage and create an actual voucher on disk
    context.storage_factory.configure(booking_id, service_date)

    storage_dir = context.storage_base_path / "vouchers" / booking_id / service_date
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Write PDF and HTML files
    (storage_dir / "voucher.pdf").write_bytes(b"%PDF-1.4\n%test content\n%%EOF")
    (storage_dir / "voucher.html").write_text("<html><body>Test</body></html>")

    voucher_id = f"V-{booking_id}-{service_date.replace('-', '')}"
    context.original_voucher_id = voucher_id
    context.existing_vouchers[f"{booking_id}/{service_date}"] = {
        "voucher_id": voucher_id,
        "booking_id": booking_id,
        "service_date": service_date,
    }

    # Write metadata
    import json
    metadata = {
        "voucher_id": voucher_id,
        "booking_id": booking_id,
        "service_date": service_date,
        "template_id": "airport-transfer-v2",
        "generated_at": "2024-02-17T10:00:00Z",
        "pdf_url": f"file://{storage_dir}/voucher.pdf",
        "html_url": f"file://{storage_dir}/voucher.html",
    }
    with open(storage_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f)


@given('a voucher was previously generated with:')
def voucher_with_full_metadata(context: VoucherTestContext, datatable, client):
    """Set up an existing voucher with full metadata."""
    data = {}
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2:
            data[row[0]] = row[1]

    booking_id = data['booking_id']
    service_date = data['service_date']
    voucher_id = data.get('voucher_id', f"V-{booking_id}-{service_date.replace('-', '')}")
    template_id = data.get('template_id', 'airport-transfer-v2')

    # Configure storage and create an actual voucher on disk
    context.storage_factory.configure(booking_id, service_date)

    storage_dir = context.storage_base_path / "vouchers" / booking_id / service_date
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Write PDF and HTML files
    (storage_dir / "voucher.pdf").write_bytes(b"%PDF-1.4\n%test content\n%%EOF")
    (storage_dir / "voucher.html").write_text("<html><body>Test</body></html>")

    context.original_voucher_id = voucher_id
    context.existing_vouchers[f"{booking_id}/{service_date}"] = data

    # Write metadata
    import json
    metadata = {
        "voucher_id": voucher_id,
        "booking_id": booking_id,
        "service_date": service_date,
        "template_id": template_id,
        "generated_at": "2024-02-17T10:00:00Z",
        "pdf_url": f"file://{storage_dir}/voucher.pdf",
        "html_url": f"file://{storage_dir}/voucher.html",
    }
    with open(storage_dir / "metadata.json", 'w') as f:
        json.dump(metadata, f)


# =============================================================================
# Step Definitions - WHEN
# =============================================================================

@when('I request a voucher for:')
def request_voucher_with_table(context: VoucherTestContext, datatable):
    """Build a voucher request from table data."""
    for row in datatable[1:]:  # Skip header row
        if len(row) >= 2:
            context.request_data[row[0]] = row[1]


@when(parsers.parse('customer "{first_name}" "{last_name}"'))
def set_customer_data(context: VoucherTestContext, first_name: str, last_name: str):
    """Set customer first and last name."""
    context.customer_data["first_name"] = first_name
    context.customer_data["last_name"] = last_name


@when(parsers.parse('service "{name}" provided by "{provider}"'))
def set_service_and_execute(
    context: VoucherTestContext,
    name: str,
    provider: str,
    client,
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

    context.response = client.post("/vouchers", json=request_body)
    context.response_json = context.response.json()

    # Capture files after request
    context.files_after_request = _get_all_files(context.storage_base_path)


@when(parsers.parse('I request a duplicate voucher for booking "{booking_id}" date "{service_date}"'))
def request_duplicate_voucher(context: VoucherTestContext, booking_id: str, service_date: str, client):
    """Request a voucher that already exists."""
    context.request_data = {
        "template_id": "airport-transfer-v2",
        "booking_id": booking_id,
        "service_date": service_date
    }
    context.customer_data = {"first_name": "Test", "last_name": "User"}
    context.service_data = {"name": "Test", "provider": "Test"}

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


# =============================================================================
# Step Definitions - THEN
# =============================================================================

@then('the voucher is created successfully')
def voucher_created_successfully(context: VoucherTestContext):
    """Verify voucher creation succeeded with 201."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == 201, \
        f"Expected 201, got {context.response.status_code}: {context.response_json}"


@then(parsers.parse('the response status is {status_code:d} {status_text}'))
def response_status_matches(context: VoucherTestContext, status_code: int, status_text: str):
    """Verify HTTP status code."""
    assert context.response is not None, "No response received"
    assert context.response.status_code == status_code, \
        f"Expected {status_code}, got {context.response.status_code}: {context.response_json}"


@then('the response contains the original voucher_id')
def response_contains_original_voucher_id(context: VoucherTestContext):
    """Verify response contains the original voucher_id."""
    assert "voucher_id" in context.response_json, \
        f"No voucher_id in response: {context.response_json}"
    assert context.response_json["voucher_id"] == context.original_voucher_id, \
        f"Expected voucher_id '{context.original_voucher_id}', got '{context.response_json['voucher_id']}'"


@then(parsers.parse('the response contains generated_at "{timestamp}"'))
def response_contains_generated_at(context: VoucherTestContext, timestamp: str):
    """Verify generated_at timestamp matches the original."""
    assert "generated_at" in context.response_json, \
        f"No generated_at in response: {context.response_json}"
    assert context.response_json["generated_at"] == timestamp, \
        f"Expected generated_at '{timestamp}', got '{context.response_json['generated_at']}'"


@then('no new files are written to storage')
def no_new_files_written(context: VoucherTestContext):
    """Verify no new files were written during the duplicate request."""
    new_files = context.files_after_request - context.files_before_request
    assert len(new_files) == 0, \
        f"New files were written: {new_files}"


@then('the voucher_id is different from the existing voucher')
def voucher_id_different(context: VoucherTestContext):
    """Verify voucher_id is different from the existing one."""
    assert "voucher_id" in context.response_json, \
        f"No voucher_id in response: {context.response_json}"
    assert context.response_json["voucher_id"] != context.original_voucher_id, \
        f"Expected different voucher_id, but got same: '{context.response_json['voucher_id']}'"


@then(parsers.parse('the response contains voucher_id "{voucher_id}"'))
def response_contains_specific_voucher_id(context: VoucherTestContext, voucher_id: str):
    """Verify specific voucher_id."""
    assert "voucher_id" in context.response_json, \
        f"No voucher_id in response: {context.response_json}"
    assert context.response_json["voucher_id"] == voucher_id, \
        f"Expected voucher_id '{voucher_id}', got '{context.response_json['voucher_id']}'"


@then(parsers.parse('the response contains template_id "{template_id}"'))
def response_contains_specific_template_id(context: VoucherTestContext, template_id: str):
    """Verify specific template_id."""
    assert "template_id" in context.response_json, \
        f"No template_id in response: {context.response_json}"
    assert context.response_json["template_id"] == template_id, \
        f"Expected template_id '{template_id}', got '{context.response_json['template_id']}'"


# =============================================================================
# Load Scenarios - US-009 only (idempotency scenarios)
# =============================================================================

from pytest_bdd import scenario

@scenario(
    'milestone_4_robustness.feature',
    'Duplicate request returns existing voucher'
)
def test_us009_duplicate_request():
    """US-009: Duplicate request returns existing voucher."""
    pass
