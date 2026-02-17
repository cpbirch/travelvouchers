# Shared Artifacts Registry: Voucher Generation

This registry tracks all data artifacts that flow across journey steps.
Every `{{variable}}` in templates must trace back to a source in this registry.

---

## Artifact Categories

### 1. Request Artifacts (Consumer-Provided)

| Artifact | Type | Source | Consumers | Required | Description |
|----------|------|--------|-----------|----------|-------------|
| `template_id` | string | API Consumer | Validation, Template Loader | Yes | Identifier for the template to use |
| `booking_id` | string | API Consumer | Validation, Merge, Storage, Response | Yes | Unique booking reference |
| `service_date` | date (ISO 8601) | API Consumer | Validation, Merge, Storage, Response | Yes | Date the service is booked for |
| `customer` | CustomerData | API Consumer | Validation, Merge | Yes | Customer details object |
| `service` | ServiceData | API Consumer | Validation, Merge | Yes | Service details object |

### 2. Customer Data Fields

| Field | Type | Required | Template Placeholder | Example |
|-------|------|----------|---------------------|---------|
| `customer.title` | string | No | `{{customer.title}}` | "Mr", "Ms", "Dr" |
| `customer.first_name` | string | Yes | `{{customer.first_name}}` | "James" |
| `customer.last_name` | string | Yes | `{{customer.last_name}}` | "Morrison" |
| `customer.email` | string | No | `{{customer.email}}` | "j.morrison@email.com" |
| `customer.phone` | string | No | `{{customer.phone}}` | "+44 7700 900123" |

### 3. Service Data Fields (IATA-Aligned)

| Field | Type | Required | Template Placeholder | Example |
|-------|------|----------|---------------------|---------|
| `service.name` | string | Yes | `{{service.name}}` | "Airport Transfer - Heathrow to Central" |
| `service.provider` | string | Yes | `{{service.provider}}` | "CityLink Transfers Ltd" |
| `service.confirmation_code` | string | No | `{{service.confirmation_code}}` | "CLT-78432-HRW" |
| `service.pickup_time` | time | No | `{{service.pickup_time}}` | "14:30" |
| `service.pickup_location` | string | No | `{{service.pickup_location}}` | "Heathrow Terminal 5" |
| `service.dropoff_location` | string | No | `{{service.dropoff_location}}` | "Marriott Hotel" |
| `service.passengers` | integer | No | `{{service.passengers}}` | 2 |
| `service.luggage_allowance` | string | No | `{{service.luggage_allowance}}` | "2 large bags per passenger" |
| `service.duration` | string | No | `{{service.duration}}` | "3 hours" |
| `service.meeting_point` | string | No | `{{service.meeting_point}}` | "Westminster Pier" |
| `service.tour_time` | time | No | `{{service.tour_time}}` | "10:00" |
| `service.notes` | string | No | `{{service.notes}}` | "Wheelchair accessible" |

### 4. System-Generated Artifacts

| Artifact | Type | Source | Consumers | Description |
|----------|------|--------|-----------|-------------|
| `voucher_id` | string | Voucher Service | Response, Storage | Generated unique ID: `V-{year}-{booking_suffix}-{date_suffix}` |
| `generated_at` | datetime | Voucher Service | Response, Storage | ISO 8601 timestamp of generation |
| `pdf_binary` | binary | Renderer | Storage | Generated PDF file content |
| `html_string` | string | Renderer | Storage | Generated HTML content |
| `pdf_url` | URL | Storage | Response | Public URL to fetch PDF |
| `html_url` | URL | Storage | Response | Public URL to fetch HTML |

---

## Data Flow Diagram

```
+----------------+     +----------------+     +----------------+
|  API Request   |     |   Template     |     |   Storage      |
+----------------+     +----------------+     +----------------+
        |                     |                      ^
        v                     v                      |
+-------+---------------------+-------+              |
|           MERGE ENGINE              |              |
|                                     |              |
|  template_id -----> Load template   |              |
|                          |          |              |
|  customer.* ----+        v          |              |
|                 +--> Replace        |              |
|  service.* -----+    placeholders   |              |
|                          |          |              |
|  booking_id ----+        v          |              |
|                 +--> Merged doc     |              |
|  service_date --+        |          |              |
|                          v          |              |
|                    +-----------+    |              |
|                    | Render    |    |              |
|                    | PDF + HTML|----+--------------+
|                    +-----------+    |
+-------------------------------------+
```

---

## Template Placeholder Rules

### Syntax
- Format: `{{path.to.field}}`
- Nesting: Up to 2 levels (`{{customer.first_name}}`, not `{{customer.address.city}}`)
- Case: Exact match required (case-sensitive)

### Resolution Order
1. Check `customer.*` namespace
2. Check `service.*` namespace
3. Check root fields (`booking_id`, `service_date`)
4. If not found: render as empty string + log warning

### Required vs Optional
- Required fields: Validation fails if missing (400 error before merge)
- Optional fields: Merge proceeds, placeholder renders as empty string

---

## Integration Contracts

### Input Schema (JSON)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["template_id", "booking_id", "service_date", "customer", "service"],
  "properties": {
    "template_id": {
      "type": "string",
      "pattern": "^[a-z0-9-]+$",
      "description": "Template identifier (lowercase, alphanumeric, hyphens)"
    },
    "booking_id": {
      "type": "string",
      "pattern": "^BK-[0-9]{4}-[0-9]+$",
      "description": "Booking reference in format BK-YYYY-NNNNN"
    },
    "service_date": {
      "type": "string",
      "format": "date",
      "description": "ISO 8601 date (YYYY-MM-DD)"
    },
    "customer": {
      "type": "object",
      "required": ["first_name", "last_name"],
      "properties": {
        "title": { "type": "string" },
        "first_name": { "type": "string" },
        "last_name": { "type": "string" },
        "email": { "type": "string", "format": "email" },
        "phone": { "type": "string" }
      }
    },
    "service": {
      "type": "object",
      "required": ["name", "provider"],
      "properties": {
        "name": { "type": "string" },
        "provider": { "type": "string" },
        "confirmation_code": { "type": "string" },
        "pickup_time": { "type": "string" },
        "pickup_location": { "type": "string" },
        "dropoff_location": { "type": "string" },
        "passengers": { "type": "integer" },
        "luggage_allowance": { "type": "string" },
        "duration": { "type": "string" },
        "meeting_point": { "type": "string" },
        "tour_time": { "type": "string" },
        "notes": { "type": "string" }
      }
    }
  }
}
```

### Output Schema (JSON)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["voucher_id", "booking_id", "service_date", "template_id", "generated_at", "urls"],
  "properties": {
    "voucher_id": {
      "type": "string",
      "pattern": "^V-[0-9]{4}-[0-9]+-[0-9]{4}$"
    },
    "booking_id": { "type": "string" },
    "service_date": { "type": "string", "format": "date" },
    "template_id": { "type": "string" },
    "generated_at": { "type": "string", "format": "date-time" },
    "urls": {
      "type": "object",
      "required": ["pdf", "html"],
      "properties": {
        "pdf": { "type": "string", "format": "uri" },
        "html": { "type": "string", "format": "uri" }
      }
    }
  }
}
```

---

## Validation Checkpoints

| Checkpoint | When | What | Action on Failure |
|------------|------|------|-------------------|
| Template exists | Before merge | `template_id` in registry | 404 TEMPLATE_NOT_FOUND |
| Required customer fields | Before merge | `first_name`, `last_name` present | 400 VALIDATION_FAILED |
| Required service fields | Before merge | `name`, `provider` present | 400 VALIDATION_FAILED |
| Date format | Before merge | `service_date` is ISO 8601 | 400 INVALID_DATE_FORMAT |
| Idempotency check | Before merge | `booking_id` + `service_date` unique | 200 return existing |
| Placeholder resolution | During merge | All placeholders mapped | Warning log, empty string |
| Storage write | After render | Files stored successfully | 503 STORAGE_UNAVAILABLE |
