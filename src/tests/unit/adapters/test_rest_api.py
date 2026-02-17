"""Unit tests for REST API adapter.

Test Budget: 3 behaviors x 2 = 6 unit tests max
1. POST /vouchers returns 201 with valid request
2. POST /vouchers returns correct response structure
3. POST /vouchers calls use case and returns result

These tests verify the REST API adapter correctly translates HTTP
requests to use case calls and formats responses.
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
