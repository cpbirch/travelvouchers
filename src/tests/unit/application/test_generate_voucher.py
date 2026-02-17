"""Unit tests for GenerateVoucher use case.

Test Budget: 3 behaviors x 2 = 6 unit tests max
- Behavior 1: Successful voucher generation (orchestrates load, merge, render, store)
- Behavior 2: Template not found error
- Behavior 3: Merge logic replaces placeholder correctly
"""

from datetime import date, datetime
from unittest.mock import Mock

import pytest
from voucher_merger.domain.value_objects import BookingRef, CustomerData, ServiceData
from voucher_merger.ports.document_renderer import MergedContent, RenderedDocument
from voucher_merger.ports.template_repository import Template
from voucher_merger.ports.voucher_storage import StorageUrl


class TestGenerateVoucher:
    """Tests for GenerateVoucher use case via driving port."""

    def test_generates_voucher_and_returns_response_with_required_fields(self) -> None:
        """Use case orchestrates ports and returns VoucherResponse."""
        from voucher_merger.application.generate_voucher import (
            GenerateVoucher,
            GenerateVoucherRequest,
            VoucherResponse,
        )

        # Arrange - mock driven ports at boundary
        template_repo = Mock()
        template_repo.find_by_id.return_value = Template(
            template_id="skeleton-template",
            content="Dear {{customer.last_name}}, Your voucher is confirmed.",
        )

        document_renderer = Mock()
        document_renderer.render_pdf.return_value = RenderedDocument(
            content=b"%PDF-1.4 test", filename="voucher.pdf"
        )

        voucher_storage = Mock()
        voucher_storage.store.return_value = StorageUrl(
            url="file:///vouchers/voucher.pdf"
        )

        use_case = GenerateVoucher(
            template_repository=template_repo,
            document_renderer=document_renderer,
            voucher_storage=voucher_storage,
        )

        request = GenerateVoucherRequest(
            template_id="skeleton-template",
            booking=BookingRef(booking_id="B-12345", service_date=date(2026, 3, 15)),
            customer=CustomerData(first_name="John", last_name="Doe"),
            service=ServiceData(name="Spa Treatment", provider="Wellness Resort"),
        )

        # Act
        result = use_case.execute(request)

        # Assert - verify response structure
        assert isinstance(result, VoucherResponse)
        assert result.voucher_id is not None
        assert "B-12345" in result.voucher_id  # Contains booking_id
        assert result.urls is not None
        assert result.urls.pdf_url == "file:///vouchers/voucher.pdf"
        assert result.generated_at is not None
        assert isinstance(result.generated_at, datetime)

    def test_raises_error_when_template_not_found(self) -> None:
        """Use case raises TemplateNotFoundError when repository returns None."""
        from voucher_merger.application.generate_voucher import (
            GenerateVoucher,
            GenerateVoucherRequest,
            TemplateNotFoundError,
        )

        # Arrange - template not found
        template_repo = Mock()
        template_repo.find_by_id.return_value = None

        document_renderer = Mock()
        voucher_storage = Mock()

        use_case = GenerateVoucher(
            template_repository=template_repo,
            document_renderer=document_renderer,
            voucher_storage=voucher_storage,
        )

        request = GenerateVoucherRequest(
            template_id="non-existent-template",
            booking=BookingRef(booking_id="B-12345", service_date=date(2026, 3, 15)),
            customer=CustomerData(first_name="John", last_name="Doe"),
            service=ServiceData(name="Spa Treatment", provider="Wellness Resort"),
        )

        # Act & Assert
        with pytest.raises(TemplateNotFoundError) as exc_info:
            use_case.execute(request)

        assert "non-existent-template" in str(exc_info.value)

    def test_merges_customer_last_name_into_template_placeholder(self) -> None:
        """Use case replaces customer.last_name placeholder with actual name."""
        from voucher_merger.application.generate_voucher import (
            GenerateVoucher,
            GenerateVoucherRequest,
        )

        # Arrange
        template_repo = Mock()
        template_repo.find_by_id.return_value = Template(
            template_id="skeleton-template",
            content="Dear {{customer.last_name}}, Your voucher is confirmed.",
        )

        document_renderer = Mock()
        document_renderer.render_pdf.return_value = RenderedDocument(
            content=b"%PDF-1.4 test", filename="voucher.pdf"
        )

        voucher_storage = Mock()
        voucher_storage.store.return_value = StorageUrl(
            url="file:///vouchers/voucher.pdf"
        )

        use_case = GenerateVoucher(
            template_repository=template_repo,
            document_renderer=document_renderer,
            voucher_storage=voucher_storage,
        )

        request = GenerateVoucherRequest(
            template_id="skeleton-template",
            booking=BookingRef(booking_id="B-12345", service_date=date(2026, 3, 15)),
            customer=CustomerData(first_name="Jane", last_name="Smith"),
            service=ServiceData(name="Massage", provider="Spa Center"),
        )

        # Act
        use_case.execute(request)

        # Assert - verify rendered content has merged data
        document_renderer.render_pdf.assert_called_once()
        call_args = document_renderer.render_pdf.call_args
        merged_content: MergedContent = call_args[0][0]

        assert "Smith" in merged_content.html
        assert "{{customer.last_name}}" not in merged_content.html
