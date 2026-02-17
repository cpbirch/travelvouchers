# Voucher Generation System: Requirements

## Overview

A mail-merge system that generates human-readable vouchers for holiday services by merging Word/LibreOffice templates with customer and service data.

---

## Domain Context

### What is a Voucher?
A voucher is a confirmation document that proves a customer has purchased a service as part of their holiday package. Examples:
- Airport transfer voucher
- Sightseeing tour voucher
- Hotel transfer voucher
- Activity booking voucher

### Domain Model (IATA-Aligned)
- **Offer**: A holiday package
- **OfferItem**: A component of the package (e.g., flight, transfer, tour)
- **OfferService**: The specific service being vouched (one voucher per service)

### Key Insight
A voucher is for a **single service**, not a bundle. Multiple services in a booking = multiple vouchers.

---

## Functional Requirements

### FR-1: Template Management

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-1.1 | System shall accept Word (.docx) templates | Must |
| FR-1.2 | System shall accept LibreOffice (.odt) templates | Must |
| FR-1.3 | Templates use `{{placeholder}}` syntax for variable substitution | Must |
| FR-1.4 | System shall maintain a template registry with 5-15 templates | Must |
| FR-1.5 | Templates are created externally by marketing/business users | Context |

### FR-2: Data Merging

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-2.1 | System shall merge customer data into template placeholders | Must |
| FR-2.2 | System shall merge service data into template placeholders | Must |
| FR-2.3 | System shall merge booking metadata (booking_id, service_date) | Must |
| FR-2.4 | Missing optional fields render as empty string | Must |
| FR-2.5 | Missing required fields fail validation before merge | Must |
| FR-2.6 | System shall log warnings for unresolved placeholders | Should |

### FR-3: Output Generation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-3.1 | System shall generate PDF output from merged document | Must |
| FR-3.2 | System shall generate HTML output from merged document | Must |
| FR-3.3 | PDF shall be human-readable and printable | Must |
| FR-3.4 | HTML shall include inline CSS for email compatibility | Must |
| FR-3.5 | HTML shall render without external resources | Should |

### FR-4: Storage and Retrieval

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-4.1 | System shall store generated vouchers persistently | Must |
| FR-4.2 | System shall return URLs for stored PDF and HTML | Must |
| FR-4.3 | Storage path: `/vouchers/{booking_id}/{service_date}/` | Must |
| FR-4.4 | URLs shall be accessible by internal services | Must |

### FR-5: Idempotency

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-5.1 | Duplicate requests (same booking_id + service_date) return existing voucher | Must |
| FR-5.2 | Idempotent response includes original generated_at timestamp | Must |
| FR-5.3 | No regeneration or storage write on duplicate request | Must |

### FR-6: Validation

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-6.1 | System shall validate template_id exists before processing | Must |
| FR-6.2 | System shall validate required customer fields (first_name, last_name) | Must |
| FR-6.3 | System shall validate required service fields (name, provider) | Must |
| FR-6.4 | System shall validate service_date is ISO 8601 format | Must |
| FR-6.5 | Validation errors return structured error response | Must |

---

## Non-Functional Requirements

### NFR-1: Performance

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-1.1 | Voucher generation latency P95 | < 2 seconds |
| NFR-1.2 | Generated PDF file size | < 500 KB |
| NFR-1.3 | Concurrent request handling | 10 requests/second |

### NFR-2: Reliability

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-2.1 | Success rate for valid requests | 99.9% |
| NFR-2.2 | Idempotency guarantee | 100% (same input = same output) |

### NFR-3: Maintainability

| ID | Requirement | Rationale |
|----|-------------|-----------|
| NFR-3.1 | Template changes require no code deployment | Marketing autonomy |
| NFR-3.2 | New service fields can be added without code changes | Extensibility |

### NFR-4: Security

| ID | Requirement | Rationale |
|----|-------------|-----------|
| NFR-4.1 | API accessible only to internal services | No public access |
| NFR-4.2 | Storage URLs accessible only to authorized services | Data protection |
| NFR-4.3 | No PII logging in application logs | Compliance |

---

## Data Requirements

### Customer Data Schema

```yaml
customer:
  required:
    first_name: string  # "James"
    last_name: string   # "Morrison"
  optional:
    title: string       # "Mr", "Ms", "Dr"
    email: string       # "j.morrison@email.com"
    phone: string       # "+44 7700 900123"
```

### Service Data Schema

```yaml
service:
  required:
    name: string        # "Airport Transfer - Heathrow to Central"
    provider: string    # "CityLink Transfers Ltd"
  optional:
    confirmation_code: string   # "CLT-78432-HRW"
    pickup_time: time           # "14:30"
    pickup_location: string     # "Heathrow Terminal 5"
    dropoff_location: string    # "Marriott Hotel"
    passengers: integer         # 2
    luggage_allowance: string   # "2 large bags per passenger"
    duration: string            # "3 hours"
    meeting_point: string       # "Westminster Pier"
    tour_time: time             # "10:00"
    notes: string               # "Wheelchair accessible"
```

### Booking Metadata

```yaml
booking:
  required:
    booking_id: string      # "BK-2024-78432"
    service_date: date      # "2024-03-15" (ISO 8601)
    template_id: string     # "airport-transfer-v2"
```

---

## API Contract

### Endpoint

```
POST /vouchers
Content-Type: application/json
```

### Request

```json
{
  "template_id": "airport-transfer-v2",
  "booking_id": "BK-2024-78432",
  "service_date": "2024-03-15",
  "customer": {
    "title": "Mr",
    "first_name": "James",
    "last_name": "Morrison",
    "email": "j.morrison@email.com"
  },
  "service": {
    "name": "Airport Transfer - Heathrow to Central London",
    "provider": "CityLink Transfers Ltd",
    "pickup_time": "14:30",
    "pickup_location": "Heathrow Terminal 5, Arrivals Hall",
    "dropoff_location": "Marriott Hotel, Grosvenor Square",
    "passengers": 2,
    "confirmation_code": "CLT-78432-HRW"
  }
}
```

### Success Response (201 Created / 200 OK for idempotent)

```json
{
  "voucher_id": "V-2024-78432-0315",
  "booking_id": "BK-2024-78432",
  "service_date": "2024-03-15",
  "template_id": "airport-transfer-v2",
  "generated_at": "2024-02-17T10:23:45Z",
  "urls": {
    "pdf": "https://storage.example.com/vouchers/BK-2024-78432/2024-03-15/voucher.pdf",
    "html": "https://storage.example.com/vouchers/BK-2024-78432/2024-03-15/voucher.html"
  }
}
```

### Error Response (4xx/5xx)

```json
{
  "error": "VALIDATION_FAILED",
  "message": "Request validation failed",
  "details": [
    {
      "field": "customer.last_name",
      "code": "REQUIRED_FIELD_MISSING",
      "message": "Customer last name is required"
    }
  ]
}
```

### Error Codes

| HTTP Status | Error Code | Cause |
|-------------|------------|-------|
| 400 | VALIDATION_FAILED | Missing or invalid fields |
| 404 | TEMPLATE_NOT_FOUND | Template ID does not exist |
| 500 | TEMPLATE_ERROR | Template corrupted or invalid |
| 503 | STORAGE_UNAVAILABLE | Storage service down |

---

## Constraints

1. **Template format**: Word (.docx) and LibreOffice (.odt) only
2. **Placeholder syntax**: `{{path.field}}` (Handlebars-style, no logic)
3. **Voucher uniqueness**: booking_id + service_date (idempotency key)
4. **Output formats**: PDF and HTML (both required per voucher)
5. **Internal use only**: No public API exposure
6. **Human-readable only**: No machine-readable codes required (no QR, barcodes)

---

## Out of Scope

- Template creation/editing UI (templates created externally)
- Voucher redemption tracking
- Multi-service vouchers (one service per voucher)
- Physical voucher printing management
- Email delivery (caller handles email with HTML content)
- Template versioning/history
- Voucher cancellation/invalidation
