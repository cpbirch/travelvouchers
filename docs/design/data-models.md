# Data Models: Voucher Generation System

## Overview

This document defines domain entities, value objects, and DTOs for the voucher generation system.

---

## Domain Layer

### Value Objects

Value objects are immutable, compared by value, and have no identity.

#### VoucherId

```python
@dataclass(frozen=True)
class VoucherId:
    """Unique identifier for a voucher."""
    value: str

    def __post_init__(self):
        # Format: V-{booking_id_suffix}-{MMDD}
        # Example: V-2024-78432-0315
        if not self.value:
            raise ValueError("VoucherId cannot be empty")

    @classmethod
    def generate(cls, booking_id: str, service_date: date) -> "VoucherId":
        """Generate voucher ID from booking reference."""
        suffix = booking_id.replace("BK-", "")
        date_part = service_date.strftime("%m%d")
        return cls(f"V-{suffix}-{date_part}")
```

#### BookingRef

```python
@dataclass(frozen=True)
class BookingRef:
    """Reference to the originating booking."""
    booking_id: str
    service_date: date

    def __post_init__(self):
        if not self.booking_id.startswith("BK-"):
            raise ValueError("booking_id must start with 'BK-'")

    def idempotency_key(self) -> str:
        """Generate idempotency key for duplicate detection."""
        return f"{self.booking_id}:{self.service_date.isoformat()}"

    def storage_path(self) -> str:
        """Generate storage path component."""
        return f"{self.booking_id}/{self.service_date.isoformat()}"
```

#### TemplateId

```python
@dataclass(frozen=True)
class TemplateId:
    """Identifier for a template."""
    value: str

    def __post_init__(self):
        if not self.value or not self.value.replace("-", "").replace("_", "").isalnum():
            raise ValueError("TemplateId must be alphanumeric with hyphens/underscores")
```

#### StoragePath

```python
@dataclass(frozen=True)
class StoragePath:
    """Path where voucher files are stored."""
    booking_id: str
    service_date: date

    def to_string(self) -> str:
        return f"{self.booking_id}/{self.service_date.isoformat()}"

    def pdf_filename(self) -> str:
        return "voucher.pdf"

    def html_filename(self) -> str:
        return "voucher.html"

    def metadata_filename(self) -> str:
        return "metadata.json"
```

#### StorageUrls

```python
@dataclass(frozen=True)
class StorageUrls:
    """URLs to access stored voucher files."""
    pdf_url: str
    html_url: str
```

#### CustomerData

```python
@dataclass(frozen=True)
class CustomerData:
    """Customer information for voucher personalization."""
    first_name: str
    last_name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    def __post_init__(self):
        if not self.first_name:
            raise ValueError("first_name is required")
        if not self.last_name:
            raise ValueError("last_name is required")

    def to_placeholder_map(self) -> dict[str, str]:
        """Convert to placeholder key-value map."""
        return {
            "customer.first_name": self.first_name,
            "customer.last_name": self.last_name,
            "customer.title": self.title or "",
            "customer.email": self.email or "",
            "customer.phone": self.phone or "",
        }
```

#### ServiceData

```python
@dataclass(frozen=True)
class ServiceData:
    """Service information for voucher content."""
    name: str
    provider: str
    pickup_time: Optional[str] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    confirmation_code: Optional[str] = None
    passengers: Optional[int] = None
    luggage_allowance: Optional[str] = None
    duration: Optional[str] = None
    meeting_point: Optional[str] = None
    tour_time: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self):
        if not self.name:
            raise ValueError("name is required")
        if not self.provider:
            raise ValueError("provider is required")

    def to_placeholder_map(self) -> dict[str, str]:
        """Convert to placeholder key-value map."""
        return {
            "service.name": self.name,
            "service.provider": self.provider,
            "service.pickup_time": self.pickup_time or "",
            "service.pickup_location": self.pickup_location or "",
            "service.dropoff_location": self.dropoff_location or "",
            "service.confirmation_code": self.confirmation_code or "",
            "service.passengers": str(self.passengers) if self.passengers else "",
            "service.luggage_allowance": self.luggage_allowance or "",
            "service.duration": self.duration or "",
            "service.meeting_point": self.meeting_point or "",
            "service.tour_time": self.tour_time or "",
            "service.notes": self.notes or "",
        }
```

---

### Entities

Entities have identity and mutable state (though often designed as immutable in practice).

#### Template

```python
@dataclass
class Template:
    """A voucher template loaded from storage."""
    template_id: TemplateId
    format: TemplateFormat  # DOCX or ODT
    content: bytes          # Raw file content
    placeholders: list[str] # Extracted placeholder names

    def merge(self, context: MergeContext) -> MergedDocument:
        """
        Create merged document by substituting placeholders.

        This is a domain operation - actual file manipulation
        delegated to infrastructure.
        """
        return MergedDocument(
            template=self,
            context=context,
            content=self._substitute_placeholders(context)
        )

    def _substitute_placeholders(self, context: MergeContext) -> bytes:
        """Substitute placeholders in template content."""
        # Implementation detail - actual substitution
        # handled by adapter working with this object
        raise NotImplementedError("Implemented by infrastructure")
```

#### MergedDocument

```python
@dataclass
class MergedDocument:
    """A template with all placeholders substituted."""
    template: Template
    context: MergeContext
    content: bytes  # Modified document content

    @property
    def format(self) -> TemplateFormat:
        return self.template.format
```

---

### Aggregates

#### Voucher (Aggregate Root)

```python
@dataclass
class Voucher:
    """
    Generated voucher aggregate.

    Invariants:
    - voucher_id is derived from booking_ref
    - generated_at is set at creation time
    - storage_urls are set after storage
    """
    voucher_id: VoucherId
    booking_ref: BookingRef
    template_id: TemplateId
    generated_at: datetime
    storage_urls: Optional[StorageUrls] = None

    @classmethod
    def create(
        cls,
        booking_ref: BookingRef,
        template_id: TemplateId
    ) -> "Voucher":
        """Factory method to create a new voucher."""
        return cls(
            voucher_id=VoucherId.generate(
                booking_ref.booking_id,
                booking_ref.service_date
            ),
            booking_ref=booking_ref,
            template_id=template_id,
            generated_at=datetime.utcnow()
        )

    def with_storage_urls(self, urls: StorageUrls) -> "Voucher":
        """Return new voucher instance with storage URLs set."""
        return Voucher(
            voucher_id=self.voucher_id,
            booking_ref=self.booking_ref,
            template_id=self.template_id,
            generated_at=self.generated_at,
            storage_urls=urls
        )

    @property
    def idempotency_key(self) -> str:
        """Key for duplicate detection."""
        return self.booking_ref.idempotency_key()
```

---

### Domain Services

#### MergeContext

```python
@dataclass(frozen=True)
class MergeContext:
    """Context for template merging."""
    customer: CustomerData
    service: ServiceData
    booking_ref: BookingRef

    def to_placeholder_map(self) -> dict[str, str]:
        """
        Flatten all data to placeholder key-value map.

        Keys match template placeholders: {{customer.last_name}} -> "customer.last_name"
        """
        placeholders = {}
        placeholders.update(self.customer.to_placeholder_map())
        placeholders.update(self.service.to_placeholder_map())
        placeholders["booking.booking_id"] = self.booking_ref.booking_id
        placeholders["booking.service_date"] = self.booking_ref.service_date.isoformat()
        return placeholders
```

---

## Application Layer

### VoucherMetadata

```python
@dataclass
class VoucherMetadata:
    """Metadata stored alongside voucher files for retrieval."""
    voucher_id: str
    booking_id: str
    service_date: str
    template_id: str
    generated_at: str
    pdf_url: str
    html_url: str

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_voucher(cls, voucher: Voucher) -> "VoucherMetadata":
        return cls(
            voucher_id=voucher.voucher_id.value,
            booking_id=voucher.booking_ref.booking_id,
            service_date=voucher.booking_ref.service_date.isoformat(),
            template_id=voucher.template_id.value,
            generated_at=voucher.generated_at.isoformat() + "Z",
            pdf_url=voucher.storage_urls.pdf_url if voucher.storage_urls else "",
            html_url=voucher.storage_urls.html_url if voucher.storage_urls else ""
        )
```

---

## Adapter Layer (DTOs)

### Request Models (Pydantic)

```python
from pydantic import BaseModel, Field
from datetime import date

class CustomerRequest(BaseModel):
    """Customer data from API request."""
    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None

    def to_domain(self) -> CustomerData:
        return CustomerData(
            first_name=self.first_name,
            last_name=self.last_name,
            title=self.title,
            email=self.email,
            phone=self.phone
        )


class ServiceRequest(BaseModel):
    """Service data from API request."""
    name: str = Field(..., min_length=1)
    provider: str = Field(..., min_length=1)
    pickup_time: Optional[str] = None
    pickup_location: Optional[str] = None
    dropoff_location: Optional[str] = None
    confirmation_code: Optional[str] = None
    passengers: Optional[int] = None
    luggage_allowance: Optional[str] = None
    duration: Optional[str] = None
    meeting_point: Optional[str] = None
    tour_time: Optional[str] = None
    notes: Optional[str] = None

    def to_domain(self) -> ServiceData:
        return ServiceData(
            name=self.name,
            provider=self.provider,
            pickup_time=self.pickup_time,
            pickup_location=self.pickup_location,
            dropoff_location=self.dropoff_location,
            confirmation_code=self.confirmation_code,
            passengers=self.passengers,
            luggage_allowance=self.luggage_allowance,
            duration=self.duration,
            meeting_point=self.meeting_point,
            tour_time=self.tour_time,
            notes=self.notes
        )


class VoucherRequest(BaseModel):
    """API request to generate a voucher."""
    template_id: str = Field(..., min_length=1)
    booking_id: str = Field(..., pattern=r"^BK-\d{4}-\d{5}$")
    service_date: date
    customer: CustomerRequest
    service: ServiceRequest
```

### Response Models (Pydantic)

```python
class UrlsResponse(BaseModel):
    """URLs in API response."""
    pdf: str
    html: str


class VoucherResponse(BaseModel):
    """API response for voucher generation."""
    voucher_id: str
    booking_id: str
    service_date: str
    template_id: str
    generated_at: str
    urls: UrlsResponse

    @classmethod
    def from_voucher(cls, voucher: Voucher) -> "VoucherResponse":
        return cls(
            voucher_id=voucher.voucher_id.value,
            booking_id=voucher.booking_ref.booking_id,
            service_date=voucher.booking_ref.service_date.isoformat(),
            template_id=voucher.template_id.value,
            generated_at=voucher.generated_at.isoformat() + "Z",
            urls=UrlsResponse(
                pdf=voucher.storage_urls.pdf_url,
                html=voucher.storage_urls.html_url
            )
        )
```

### Error Models (Pydantic)

```python
class ErrorDetail(BaseModel):
    """Individual validation error."""
    field: str
    code: str
    message: str


class ErrorResponse(BaseModel):
    """Structured error response."""
    error: str
    message: str
    correlation_id: str
    details: list[ErrorDetail] = []
    retry_after: Optional[int] = None
```

---

## Enumerations

```python
from enum import Enum

class TemplateFormat(str, Enum):
    """Supported template file formats."""
    DOCX = "docx"
    ODT = "odt"


class ErrorCode(str, Enum):
    """Machine-readable error codes."""
    VALIDATION_FAILED = "VALIDATION_FAILED"
    TEMPLATE_NOT_FOUND = "TEMPLATE_NOT_FOUND"
    TEMPLATE_ERROR = "TEMPLATE_ERROR"
    RENDER_ERROR = "RENDER_ERROR"
    STORAGE_UNAVAILABLE = "STORAGE_UNAVAILABLE"
    REQUIRED_FIELD_MISSING = "REQUIRED_FIELD_MISSING"
    INVALID_DATE_FORMAT = "INVALID_DATE_FORMAT"
    INVALID_FORMAT = "INVALID_FORMAT"
```

---

## Data Flow

### Request to Domain

```
VoucherRequest (Pydantic)
    |
    v
VoucherRequest.customer.to_domain() -> CustomerData (Value Object)
VoucherRequest.service.to_domain()  -> ServiceData (Value Object)
BookingRef(booking_id, service_date) -> BookingRef (Value Object)
    |
    v
MergeContext(customer, service, booking_ref)
    |
    v
Template.merge(context) -> MergedDocument
    |
    v
Voucher.create(booking_ref, template_id) -> Voucher (Aggregate)
```

### Domain to Response

```
Voucher (Aggregate)
    |
    v
VoucherResponse.from_voucher(voucher) -> VoucherResponse (Pydantic)
    |
    v
JSON Response
```

---

## Schema Validation

### Known Placeholders

```python
CUSTOMER_PLACEHOLDERS = {
    "customer.first_name": {"required": True},
    "customer.last_name": {"required": True},
    "customer.title": {"required": False},
    "customer.email": {"required": False},
    "customer.phone": {"required": False},
}

SERVICE_PLACEHOLDERS = {
    "service.name": {"required": True},
    "service.provider": {"required": True},
    "service.pickup_time": {"required": False},
    "service.pickup_location": {"required": False},
    "service.dropoff_location": {"required": False},
    "service.confirmation_code": {"required": False},
    "service.passengers": {"required": False},
    "service.luggage_allowance": {"required": False},
    "service.duration": {"required": False},
    "service.meeting_point": {"required": False},
    "service.tour_time": {"required": False},
    "service.notes": {"required": False},
}

BOOKING_PLACEHOLDERS = {
    "booking.booking_id": {"required": True},
    "booking.service_date": {"required": True},
}

ALL_PLACEHOLDERS = {
    **CUSTOMER_PLACEHOLDERS,
    **SERVICE_PLACEHOLDERS,
    **BOOKING_PLACEHOLDERS,
}
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-17 | Morgan (Solution Architect) | Initial data models |
