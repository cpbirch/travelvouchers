"""Unit tests for REST API adapter.

Test Budget:
- Success behaviors: 3 behaviors x 2 = 6 unit tests max
  1. POST /vouchers returns 201 with valid request
  2. POST /vouchers returns correct response structure
  3. POST /vouchers calls use case and returns result

- Validation behaviors (step 02-05): 3 behaviors x 2 = 6 unit tests max
  1. Validate required fields are present
  2. Validate date format is ISO 8601
  3. Batch error reporting (multiple errors returned at once)

These tests verify the REST API adapter correctly translates HTTP
requests to use case calls and formats responses, including validation.
"""

import pytest
from datetime import datetime, UTC
from unittest.mock import Mock, patch

from fastapi.testclient import TestClient


class TestVoucherEndpoint:
    """Tests for POST /vouchers endpoint."""

    @pytest.fixture
    def mock_generate_voucher(self):
        """Mock GenerateVoucher use case."""
        mock = Mock()
        mock.execute.return_value = Mock(
            voucher_id="V-BK-2024-00001-20240101",
            urls=Mock(pdf_url="file:///vouchers/BK-2024-00001/2024-01-01/voucher.pdf"),
            generated_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
        )
        return mock

    @pytest.fixture
    def client(self, mock_generate_voucher):
        """Create test client with mocked use case."""
        from voucher_merger.main import create_app

        app = create_app(generate_voucher=mock_generate_voucher)
        return TestClient(app)

    def test_post_vouchers_returns_201_on_success(self, client, mock_generate_voucher):
        """POST /vouchers returns 201 Created for valid request."""
        response = client.post(
            "/vouchers",
            json={
                "template_id": "skeleton-template",
                "booking_id": "BK-2024-00001",
                "service_date": "2024-01-01",
                "customer": {"first_name": "James", "last_name": "Morrison"},
                "service": {"name": "Test Service", "provider": "Test Provider"},
            },
        )

        assert response.status_code == 201

    def test_post_vouchers_returns_correct_response_structure(
        self, client, mock_generate_voucher
    ):
        """POST /vouchers returns response with required fields."""
        response = client.post(
            "/vouchers",
            json={
                "template_id": "skeleton-template",
                "booking_id": "BK-2024-00001",
                "service_date": "2024-01-01",
                "customer": {"first_name": "James", "last_name": "Morrison"},
                "service": {"name": "Test Service", "provider": "Test Provider"},
            },
        )

        data = response.json()
        assert "voucher_id" in data
        assert "booking_id" in data
        assert "service_date" in data
        assert "template_id" in data
        assert "generated_at" in data
        assert "urls" in data
        assert "pdf" in data["urls"]

    def test_post_vouchers_calls_use_case_with_request_data(
        self, client, mock_generate_voucher
    ):
        """POST /vouchers passes request data to use case."""
        client.post(
            "/vouchers",
            json={
                "template_id": "skeleton-template",
                "booking_id": "BK-2024-00001",
                "service_date": "2024-01-01",
                "customer": {"first_name": "James", "last_name": "Morrison"},
                "service": {"name": "Test Service", "provider": "Test Provider"},
            },
        )

        mock_generate_voucher.execute.assert_called_once()
        call_args = mock_generate_voucher.execute.call_args
        request = call_args[0][0]

        assert request.template_id == "skeleton-template"
        assert request.booking.booking_id == "BK-2024-00001"
        assert request.customer.last_name == "Morrison"


class TestVoucherEndpointValidation:
    """Tests for POST /vouchers validation.

    Test Budget: 3 behaviors x 2 = 6 unit tests max
    1. Required fields validation
    2. Date format validation (ISO 8601)
    3. Batch error reporting
    """

    @pytest.fixture
    def mock_generate_voucher(self):
        """Mock GenerateVoucher use case."""
        mock = Mock()
        mock.execute.return_value = Mock(
            voucher_id="V-BK-2024-00001-20240101",
            urls=Mock(pdf_url="file:///vouchers/BK-2024-00001/2024-01-01/voucher.pdf"),
            generated_at=datetime(2024, 1, 1, 10, 0, 0, tzinfo=UTC),
        )
        return mock

    @pytest.fixture
    def client(self, mock_generate_voucher):
        """Create test client with mocked use case."""
        from voucher_merger.main import create_app

        app = create_app(generate_voucher=mock_generate_voucher)
        return TestClient(app)

    @pytest.mark.parametrize("missing_field,expected_field", [
        ("template_id", "template_id"),
        ("booking_id", "booking_id"),
        ("service_date", "service_date"),
    ])
    def test_returns_400_with_validation_error_for_missing_required_top_level_field(
        self, client, missing_field, expected_field
    ):
        """POST /vouchers returns 400 with VALIDATION_FAILED for missing required fields."""
        request_data = {
            "template_id": "airport-transfer-v2",
            "booking_id": "BK-2024-00001",
            "service_date": "2024-01-01",
            "customer": {"first_name": "James", "last_name": "Morrison"},
            "service": {"name": "Airport Transfer", "provider": "CityLink"},
        }
        del request_data[missing_field]

        response = client.post("/vouchers", json=request_data)

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_FAILED"
        error_fields = [e["field"] for e in data["errors"]]
        assert expected_field in error_fields

    @pytest.mark.parametrize("missing_customer_field,expected_field", [
        ("first_name", "customer.first_name"),
        ("last_name", "customer.last_name"),
    ])
    def test_returns_400_with_validation_error_for_missing_customer_field(
        self, client, missing_customer_field, expected_field
    ):
        """POST /vouchers returns 400 for missing customer fields."""
        customer_data = {"first_name": "James", "last_name": "Morrison"}
        del customer_data[missing_customer_field]

        response = client.post(
            "/vouchers",
            json={
                "template_id": "airport-transfer-v2",
                "booking_id": "BK-2024-00001",
                "service_date": "2024-01-01",
                "customer": customer_data,
                "service": {"name": "Airport Transfer", "provider": "CityLink"},
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_FAILED"
        error_fields = [e["field"] for e in data["errors"]]
        assert expected_field in error_fields

    @pytest.mark.parametrize("missing_service_field,expected_field", [
        ("name", "service.name"),
        ("provider", "service.provider"),
    ])
    def test_returns_400_with_validation_error_for_missing_service_field(
        self, client, missing_service_field, expected_field
    ):
        """POST /vouchers returns 400 for missing service fields."""
        service_data = {"name": "Airport Transfer", "provider": "CityLink"}
        del service_data[missing_service_field]

        response = client.post(
            "/vouchers",
            json={
                "template_id": "airport-transfer-v2",
                "booking_id": "BK-2024-00001",
                "service_date": "2024-01-01",
                "customer": {"first_name": "James", "last_name": "Morrison"},
                "service": service_data,
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_FAILED"
        error_fields = [e["field"] for e in data["errors"]]
        assert expected_field in error_fields

    @pytest.mark.parametrize("invalid_date", [
        "15-03-2024",  # DD-MM-YYYY (European format)
        "03/15/2024",  # MM/DD/YYYY (US format)
        "2024/03/15",  # Wrong separator
        "not-a-date",  # Not a date at all
    ])
    def test_returns_400_with_invalid_date_format_error(self, client, invalid_date):
        """POST /vouchers returns 400 with INVALID_DATE_FORMAT for non-ISO 8601 dates."""
        response = client.post(
            "/vouchers",
            json={
                "template_id": "airport-transfer-v2",
                "booking_id": "BK-2024-00001",
                "service_date": invalid_date,
                "customer": {"first_name": "James", "last_name": "Morrison"},
                "service": {"name": "Airport Transfer", "provider": "CityLink"},
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_FAILED"

        # Find the date validation error
        date_error = next(
            (e for e in data["errors"] if e["field"] == "service_date"),
            None
        )
        assert date_error is not None
        assert date_error["code"] == "INVALID_DATE_FORMAT"
        assert "ISO 8601" in date_error["message"]

    def test_returns_all_validation_errors_in_single_response(self, client):
        """POST /vouchers returns all validation errors at once (batch error reporting)."""
        # Request with multiple errors: missing last_name and invalid date format
        response = client.post(
            "/vouchers",
            json={
                "template_id": "airport-transfer-v2",
                "booking_id": "BK-2024-00001",
                "service_date": "15-03-2024",  # Invalid date format
                "customer": {"first_name": "James"},  # Missing last_name
                "service": {"name": "Airport Transfer", "provider": "CityLink"},
            },
        )

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_FAILED"

        # Should contain errors for both fields
        error_fields = [e["field"] for e in data["errors"]]
        assert "customer.last_name" in error_fields
        assert "service_date" in error_fields
        assert len(data["errors"]) >= 2

    def test_returns_all_required_field_errors_for_empty_request(self, client):
        """POST /vouchers returns errors for all required fields on empty request."""
        response = client.post("/vouchers", json={})

        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "VALIDATION_FAILED"

        # Should contain errors for all required fields
        error_fields = [e["field"] for e in data["errors"]]
        required_fields = [
            "template_id", "booking_id", "service_date",
            "customer.first_name", "customer.last_name",
            "service.name", "service.provider",
        ]
        for field in required_fields:
            assert field in error_fields, f"Missing error for required field: {field}"
