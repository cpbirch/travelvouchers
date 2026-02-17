"""Domain value objects for voucher generation."""

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class CustomerData:
    """Customer information for voucher generation.

    Attributes:
        first_name: Customer's first name (required).
        last_name: Customer's last name (required).
        title: Optional title (e.g., "Mr.", "Dr.").
    """

    first_name: str
    last_name: str
    title: str | None = None


@dataclass(frozen=True)
class ServiceData:
    """Service information for voucher generation.

    Attributes:
        name: Name of the service (required).
        provider: Service provider name (required).
    """

    name: str
    provider: str


@dataclass(frozen=True)
class BookingRef:
    """Booking reference for voucher generation.

    Attributes:
        booking_id: Unique booking identifier (required).
        service_date: Date of the service (required).
    """

    booking_id: str
    service_date: date
