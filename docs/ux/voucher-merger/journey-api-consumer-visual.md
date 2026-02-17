# API Consumer Journey: Voucher Generation

## Journey Overview

**Persona**: Internal Service (e.g., Booking Service, Fulfillment Service)
**Goal**: Generate a human-readable voucher confirming a customer's booked service
**Emotional Arc**: Uncertain ("Will integration work?") -> Confident ("Reliable, predictable API")

---

## Journey Flow (ASCII)

```
+------------------+     +-------------------+     +------------------+
|  BOOKING SERVICE |     |  VOUCHER-MERGER   |     |  STORAGE SERVICE |
|  (API Consumer)  |     |  (This System)    |     |  (Blob/File)     |
+--------+---------+     +---------+---------+     +--------+---------+
         |                         |                        |
         |  POST /vouchers         |                        |
         |  {                      |                        |
         |    template_id,         |                        |
         |    customer: {...},     |                        |
         |    service: {...}       |                        |
         |  }                      |                        |
         +------------------------>|                        |
         |                         |                        |
         |               +---------+---------+              |
         |               | 1. Validate Input |              |
         |               |    - template exists?            |
         |               |    - required fields?            |
         |               +---------+---------+              |
         |                         |                        |
         |               +---------+---------+              |
         |               | 2. Load Template  |              |
         |               |    (Word/ODT file)|              |
         |               +---------+---------+              |
         |                         |                        |
         |               +---------+---------+              |
         |               | 3. Merge Data     |              |
         |               |    {{customer.*}} |              |
         |               |    {{service.*}}  |              |
         |               +---------+---------+              |
         |                         |                        |
         |               +---------+---------+              |
         |               | 4. Render Outputs |              |
         |               |    - PDF          |              |
         |               |    - HTML         |              |
         |               +---------+---------+              |
         |                         |                        |
         |                         |  Store voucher files   |
         |                         +----------------------->|
         |                         |                        |
         |                         |<-----------------------+
         |                         |  storage_urls          |
         |                         |                        |
         |  201 Created            |                        |
         |  {                      |                        |
         |    voucher_id,          |                        |
         |    pdf_url,             |                        |
         |    html_url             |                        |
         |  }                      |                        |
         |<------------------------+                        |
         |                         |                        |
```

---

## Step-by-Step Journey

### Step 1: Request Voucher Generation

**What the consumer sends:**
```json
POST /vouchers
Content-Type: application/json

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
    "luggage_allowance": "2 large bags per passenger",
    "confirmation_code": "CLT-78432-HRW"
  }
}
```

**Emotional state**: Hopeful but cautious ("I hope the integration works")
**Key concern**: "What if the template doesn't exist? What if I'm missing required fields?"

---

### Step 2: Validation (System Internal)

**System validates:**
- `template_id` exists in template registry
- `booking_id` + `service_date` uniqueness (idempotency)
- Required customer fields present: `first_name`, `last_name`
- Required service fields present: `name`, `provider`

**On validation failure:**
```json
HTTP 400 Bad Request
{
  "error": "VALIDATION_FAILED",
  "details": [
    {
      "field": "customer.last_name",
      "code": "REQUIRED_FIELD_MISSING",
      "message": "Customer last name is required"
    }
  ]
}
```

**Emotional impact**: Clear error messages build trust. Vague errors erode confidence.

---

### Step 3: Template Loading and Merge

**Template source**: Word (.docx) or LibreOffice (.odt) document
**Placeholder syntax**: `{{customer.first_name}}`, `{{service.pickup_time}}`

**Example template snippet (conceptual):**
```
+----------------------------------------------------------+
|                   [COMPANY LOGO]                         |
|                                                          |
|  TRANSFER VOUCHER                                        |
|  ================                                        |
|                                                          |
|  Dear {{customer.title}} {{customer.last_name}},         |
|                                                          |
|  Your transfer is confirmed:                             |
|                                                          |
|  Service:    {{service.name}}                            |
|  Date:       {{service_date}}                            |
|  Pickup:     {{service.pickup_time}}                     |
|  From:       {{service.pickup_location}}                 |
|  To:         {{service.dropoff_location}}                |
|                                                          |
|  Provider:   {{service.provider}}                        |
|  Reference:  {{service.confirmation_code}}               |
|                                                          |
|  Booking ID: {{booking_id}}                              |
+----------------------------------------------------------+
```

**Merge rules:**
- Missing optional fields: render as empty string
- Missing required fields: fail with clear error (caught in validation)
- Date formatting: ISO 8601 input, localized output based on template locale

---

### Step 4: Render and Store

**Outputs generated:**
1. **PDF**: For printing, email attachment
2. **HTML**: For email body, web display

**Storage pattern:**
```
/vouchers/{booking_id}/{service_date}/
  voucher.pdf
  voucher.html
```

**Idempotency**: Same `booking_id` + `service_date` returns existing voucher (no regeneration)

---

### Step 5: Response

**Success response:**
```json
HTTP 201 Created
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

**Emotional state**: Confident ("It worked exactly as documented")

---

## Error Scenarios

| Scenario | HTTP Status | Error Code | Consumer Action |
|----------|-------------|------------|-----------------|
| Template not found | 404 | TEMPLATE_NOT_FOUND | Check template_id spelling |
| Missing required field | 400 | VALIDATION_FAILED | Add missing field to request |
| Template parse error | 500 | TEMPLATE_ERROR | Contact template maintainer |
| Storage failure | 503 | STORAGE_UNAVAILABLE | Retry with backoff |
| Duplicate (idempotent) | 200 | (none - returns existing) | Use returned URLs |

---

## Integration Checkpoints

1. **Template Registry**: Consumer must know valid template IDs
2. **Schema Contract**: Customer and Service schemas must be documented
3. **Storage Access**: Consumer needs read access to storage URLs
4. **Idempotency**: Consumer should handle 200 (existing) same as 201 (new)

---

## TUI Mockup: CLI Tool for Testing (Optional Future)

```
$ voucher-cli generate \
    --template airport-transfer-v2 \
    --booking BK-2024-78432 \
    --date 2024-03-15 \
    --customer '{"first_name":"James","last_name":"Morrison"}' \
    --service '{"name":"Airport Transfer","provider":"CityLink"}'

Validating input... OK
Loading template... OK
Merging data... OK
Rendering PDF... OK
Rendering HTML... OK
Storing voucher... OK

Voucher generated:
  ID:   V-2024-78432-0315
  PDF:  https://storage.example.com/vouchers/.../voucher.pdf
  HTML: https://storage.example.com/vouchers/.../voucher.html
```
