"""Unit tests for GenerateVoucher use case.

Test Budget: 5 behaviors x 2 = 10 unit tests max
- Behavior 1: Successful voucher generation (orchestrates load, merge, render, store)
- Behavior 2: Template not found error
- Behavior 3: Merge logic replaces placeholder correctly
- Behavior 4: Customer placeholder merging (first_name, last_name, title, email, phone)
- Behavior 5: Missing optional customer fields render as empty
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

    @pytest.mark.parametrize(
        "placeholder,field_value,customer_field",
        [
            ("{{customer.first_name}}", "James", "first_name"),
            ("{{customer.last_name}}", "Morrison", "last_name"),
            ("{{customer.title}}", "Mr", "title"),
            ("{{customer.email}}", "j.morrison@email.com", "email"),
            ("{{customer.phone}}", "+44 7700 900123", "phone"),
        ],
    )
    def test_merges_customer_placeholders_into_template(
        self, placeholder: str, field_value: str, customer_field: str
    ) -> None:
        """Use case replaces all customer placeholders with actual data."""
        from voucher_merger.application.generate_voucher import (
            GenerateVoucher,
            GenerateVoucherRequest,
        )

        # Arrange
        template_repo = Mock()
        template_repo.find_by_id.return_value = Template(
            template_id="test-template",
            content=f"Customer: {placeholder}",
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

        # Build customer data with optional fields
        customer_kwargs = {
            "first_name": "James",
            "last_name": "Morrison",
            "title": "Mr",
            "email": "j.morrison@email.com",
            "phone": "+44 7700 900123",
        }
        customer = CustomerData(**customer_kwargs)

        request = GenerateVoucherRequest(
            template_id="test-template",
            booking=BookingRef(booking_id="B-12345", service_date=date(2026, 3, 15)),
            customer=customer,
            service=ServiceData(name="Transfer", provider="CityLink"),
        )

        # Act
        use_case.execute(request)

        # Assert - verify placeholder was replaced
        document_renderer.render_pdf.assert_called_once()
        call_args = document_renderer.render_pdf.call_args
        merged_content: MergedContent = call_args[0][0]

        assert field_value in merged_content.html
        assert placeholder not in merged_content.html

    def test_renders_missing_optional_fields_as_empty_string(self) -> None:
        """Missing optional customer fields (title, email, phone) render as empty."""
        from voucher_merger.application.generate_voucher import (
            GenerateVoucher,
            GenerateVoucherRequest,
        )

        # Arrange
        template_repo = Mock()
        template_repo.find_by_id.return_value = Template(
            template_id="test-template",
            content="Dear {{customer.title}} {{customer.last_name}}",
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

        # Customer without optional title
        customer = CustomerData(first_name="Elena", last_name="Rodriguez")

        request = GenerateVoucherRequest(
            template_id="test-template",
            booking=BookingRef(booking_id="B-12345", service_date=date(2026, 3, 15)),
            customer=customer,
            service=ServiceData(name="Transfer", provider="CityLink"),
        )

        # Act
        use_case.execute(request)

        # Assert - title placeholder replaced with empty, last_name replaced
        document_renderer.render_pdf.assert_called_once()
        call_args = document_renderer.render_pdf.call_args
        merged_content: MergedContent = call_args[0][0]

        assert "Rodriguez" in merged_content.html
        assert "{{customer.title}}" not in merged_content.html
        assert "{{customer.last_name}}" not in merged_content.html

    @pytest.mark.parametrize(
        "last_name",
        [
            "O'Brien",       # Apostrophe
            "Mueller",       # Umlaut-compatible (using ASCII)
            "von der Berg",  # Spaces and lowercase
        ],
    )
    def test_handles_special_characters_in_customer_names(self, last_name: str) -> None:
        """Customer names with special characters are merged correctly."""
        from voucher_merger.application.generate_voucher import (
            GenerateVoucher,
            GenerateVoucherRequest,
        )

        # Arrange
        template_repo = Mock()
        template_repo.find_by_id.return_value = Template(
            template_id="test-template",
            content="Customer: {{customer.last_name}}",
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

        customer = CustomerData(first_name="Patrick", last_name=last_name)

        request = GenerateVoucherRequest(
            template_id="test-template",
            booking=BookingRef(booking_id="B-12345", service_date=date(2026, 3, 15)),
            customer=customer,
            service=ServiceData(name="Transfer", provider="CityLink"),
        )

        # Act
        use_case.execute(request)

        # Assert - special characters preserved
        document_renderer.render_pdf.assert_called_once()
        call_args = document_renderer.render_pdf.call_args
        merged_content: MergedContent = call_args[0][0]

        assert last_name in merged_content.html
        assert "{{customer.last_name}}" not in merged_content.html
