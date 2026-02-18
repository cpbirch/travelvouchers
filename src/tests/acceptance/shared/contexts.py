"""Shared test context classes for BDD steps.

L3 Responsibilities: Extract duplicated test context dataclasses
from individual test files into a shared module.

Test contexts hold state across Given-When-Then steps within scenarios.
"""

from dataclasses import dataclass, field
from typing import Any


@dataclass
class VoucherTestContext:
    """Standard test context for voucher generation scenarios.

    This class is used by most acceptance test modules to share state
    across BDD steps within a single scenario. Reset for each scenario.
    """

    # Request building
    request_data: dict = field(default_factory=dict)
    customer_data: dict = field(default_factory=dict)
    service_data: dict = field(default_factory=dict)

    # Response capturing
    response: Any = None
    response_json: dict = field(default_factory=dict)

    # Template state
    available_templates: set = field(default_factory=set)

    # Storage state
    storage_available: bool = True
    existing_vouchers: dict = field(default_factory=dict)

    # Captured content for assertions
    captured_pdf_bytes: bytes = b""
    captured_html_content: str = ""
    captured_merged_content: str = ""

    # For idempotency testing
    original_voucher_id: str = ""
    original_generated_at: str = ""
    files_before_request: set = field(default_factory=set)
    files_after_request: set = field(default_factory=set)

    # For file path tracking
    stored_pdf_path: str = ""
    stored_html_path: str = ""
    pdf_content: bytes = b""
    html_content: str = ""


@dataclass
class ValidationTestContext:
    """Test context for validation-specific scenarios.

    Extends basic context with flags for intentional missing fields
    to test validation error handling.
    """

    # Request building
    request_data: dict = field(default_factory=dict)
    customer_data: dict = field(default_factory=dict)
    service_data: dict = field(default_factory=dict)

    # Response capturing
    response: Any = None
    response_json: dict = field(default_factory=dict)

    # Template state
    available_templates: set = field(default_factory=set)
    storage_available: bool = True

    # Flags for intentional missing fields
    skip_template_id: bool = False
    skip_booking_id: bool = False
    skip_customer_first_name: bool = False
    skip_customer_last_name: bool = False
    skip_service_name: bool = False
    skip_service_provider: bool = False


@dataclass
class ErrorTestContext:
    """Test context for structured error response testing.

    Includes fields for capturing logs and testing correlation IDs.
    """

    # Request building
    request_data: dict = field(default_factory=dict)
    customer_data: dict = field(default_factory=dict)
    service_data: dict = field(default_factory=dict)

    # Response capturing
    response: Any = None
    response_json: dict = field(default_factory=dict)

    # Error state
    storage_available: bool = True
    template_corrupted: bool = False

    # Log capturing
    captured_logs: list = field(default_factory=list)
