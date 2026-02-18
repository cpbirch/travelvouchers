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
        email: Optional email address.
        phone: Optional phone number.
    """

    first_name: str
    last_name: str
    title: str | None = None
    email: str | None = None
    phone: str | None = None


@dataclass(frozen=True)
class ServiceData:
    """Service information for voucher generation.

    Attributes:
        name: Name of the service (required).
        provider: Service provider name (required).
        pickup_time: Optional pickup time for transfers.
        pickup_location: Optional pickup location for transfers.
        dropoff_location: Optional dropoff location for transfers.
        passengers: Optional number of passengers.
        confirmation_code: Optional confirmation/booking code.
        meeting_point: Optional meeting point for tours.
        tour_time: Optional tour start time.
        duration: Optional duration of service.
        notes: Optional special notes or requirements.
    """

    name: str
    provider: str
    pickup_time: str | None = None
    pickup_location: str | None = None
    dropoff_location: str | None = None
    passengers: str | None = None
    confirmation_code: str | None = None
    meeting_point: str | None = None
    tour_time: str | None = None
    duration: str | None = None
    notes: str | None = None


@dataclass(frozen=True)
class BookingRef:
    """Booking reference for voucher generation.

    Attributes:
        booking_id: Unique booking identifier (required).
        service_date: Date of the service (required).
    """

    booking_id: str
    service_date: date
