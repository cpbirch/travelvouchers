"""Request validation for voucher generation.

This module provides validation utilities for voucher generation requests,
including field validation and date format validation.
"""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ValidationError:
    """A single validation error."""

    field: str
    code: str
    message: str


@dataclass
class ValidationResult:
    """Result of validating a request."""

    errors: list[ValidationError]

    @property
    def is_valid(self) -> bool:
        """Return True if no validation errors."""
        return len(self.errors) == 0


# ISO 8601 date format: YYYY-MM-DD
ISO_8601_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def is_valid_iso_date(date_string: str) -> bool:
    """Check if a string is a valid ISO 8601 date (YYYY-MM-DD).

    Args:
        date_string: The string to validate.

    Returns:
        True if the string matches ISO 8601 date format.
    """
    if not date_string:
        return False
    return bool(ISO_8601_DATE_PATTERN.match(date_string))


def validate_voucher_request(request_data: dict) -> ValidationResult:
    """Validate a voucher request and return all errors.

    This function validates all fields and returns all errors at once
    (batch error reporting) so the caller can fix them all together.

    Args:
        request_data: Dictionary of request data to validate.

    Returns:
        ValidationResult with all validation errors found.
    """
    errors: list[ValidationError] = []

    # Validate top-level required fields
    if not request_data.get("template_id"):
        errors.append(
            ValidationError(
                field="template_id",
                code="REQUIRED_FIELD_MISSING",
                message="template_id is required",
            )
        )

    if not request_data.get("booking_id"):
        errors.append(
            ValidationError(
                field="booking_id",
                code="REQUIRED_FIELD_MISSING",
                message="booking_id is required",
            )
        )

    # Validate service_date
    service_date = request_data.get("service_date")
    if not service_date:
        errors.append(
            ValidationError(
                field="service_date",
                code="REQUIRED_FIELD_MISSING",
                message="service_date is required",
            )
        )
    elif not is_valid_iso_date(service_date):
        errors.append(
            ValidationError(
                field="service_date",
                code="INVALID_DATE_FORMAT",
                message="service_date must be in ISO 8601 format (YYYY-MM-DD)",
            )
        )

    # Validate customer fields
    customer = request_data.get("customer", {})
    if not isinstance(customer, dict):
        customer = {}

    if not customer.get("first_name"):
        errors.append(
            ValidationError(
                field="customer.first_name",
                code="REQUIRED_FIELD_MISSING",
                message="customer.first_name is required",
            )
        )

    if not customer.get("last_name"):
        errors.append(
            ValidationError(
                field="customer.last_name",
                code="REQUIRED_FIELD_MISSING",
                message="customer.last_name is required",
            )
        )

    # Validate service fields
    service = request_data.get("service", {})
    if not isinstance(service, dict):
        service = {}

    if not service.get("name"):
        errors.append(
            ValidationError(
                field="service.name",
                code="REQUIRED_FIELD_MISSING",
                message="service.name is required",
            )
        )

    if not service.get("provider"):
        errors.append(
            ValidationError(
                field="service.provider",
                code="REQUIRED_FIELD_MISSING",
                message="service.provider is required",
            )
        )

    return ValidationResult(errors=errors)
