"""Unit tests for domain value objects."""

from datetime import date

import pytest


class TestCustomerData:
    """Tests for CustomerData value object."""

    def test_creates_with_required_fields(self) -> None:
        """CustomerData accepts first_name and last_name as required fields."""
        from voucher_merger.domain.value_objects import CustomerData

        customer = CustomerData(first_name="John", last_name="Doe")

        assert customer.first_name == "John"
        assert customer.last_name == "Doe"

    def test_title_is_optional_with_none_default(self) -> None:
        """CustomerData has optional title field defaulting to None."""
        from voucher_merger.domain.value_objects import CustomerData

        customer = CustomerData(first_name="Jane", last_name="Smith")

        assert customer.title is None

    def test_accepts_title_when_provided(self) -> None:
        """CustomerData accepts title when explicitly provided."""
        from voucher_merger.domain.value_objects import CustomerData

        customer = CustomerData(first_name="Dr", last_name="House", title="Dr.")

        assert customer.title == "Dr."

    def test_is_immutable(self) -> None:
        """CustomerData is immutable (frozen)."""
        from voucher_merger.domain.value_objects import CustomerData

        customer = CustomerData(first_name="John", last_name="Doe")

        with pytest.raises((AttributeError, TypeError)):
            customer.first_name = "Jane"  # type: ignore[misc]


class TestServiceData:
    """Tests for ServiceData value object."""

    def test_creates_with_required_fields(self) -> None:
        """ServiceData accepts name and provider as required fields."""
        from voucher_merger.domain.value_objects import ServiceData

        service = ServiceData(name="Spa Treatment", provider="Wellness Center")

        assert service.name == "Spa Treatment"
        assert service.provider == "Wellness Center"

    def test_is_immutable(self) -> None:
        """ServiceData is immutable (frozen)."""
        from voucher_merger.domain.value_objects import ServiceData

        service = ServiceData(name="Massage", provider="Spa")

        with pytest.raises((AttributeError, TypeError)):
            service.name = "Other"  # type: ignore[misc]


class TestBookingRef:
    """Tests for BookingRef value object."""

    def test_creates_with_required_fields(self) -> None:
        """BookingRef accepts booking_id and service_date as required fields."""
        from voucher_merger.domain.value_objects import BookingRef

        booking = BookingRef(booking_id="BK-12345", service_date=date(2026, 3, 15))

        assert booking.booking_id == "BK-12345"
        assert booking.service_date == date(2026, 3, 15)

    def test_is_immutable(self) -> None:
        """BookingRef is immutable (frozen)."""
        from voucher_merger.domain.value_objects import BookingRef

        booking = BookingRef(booking_id="BK-001", service_date=date(2026, 1, 1))

        with pytest.raises((AttributeError, TypeError)):
            booking.booking_id = "BK-999"  # type: ignore[misc]
