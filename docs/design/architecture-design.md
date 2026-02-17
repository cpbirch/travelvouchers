# Architecture Design: Voucher Generation System (Template Merger)

## System Context

### Business Capability
Generate human-readable vouchers (PDF + HTML) by merging Word/LibreOffice templates with customer and service data. Internal API consumed by holiday booking services.

### Key Quality Attributes
| Attribute | Target | Rationale |
|-----------|--------|-----------|
| Latency | P95 < 2s | Customer-facing booking flow |
| Throughput | 10 req/s | Peak booking periods |
| Reliability | 99.9% success | Business-critical documents |
| Idempotency | 100% | Safe retries in distributed system |

---

## C4 Model Diagrams

### Level 1: System Context

```
+-------------------+          POST /vouchers          +-------------------------+
|                   |  -------------------------------->|                         |
|  Booking Service  |                                   |  Voucher Merger System  |
|  (Internal)       |  <--------------------------------|                         |
|                   |    { pdf_url, html_url }          |                         |
+-------------------+                                   +-------------------------+
                                                                    |
                                                                    | stores
                                                                    v
                                                        +-------------------------+
                                                        |                         |
                                                        |  File Storage           |
                                                        |  (S3 / Filesystem)      |
                                                        |                         |
                                                        +-------------------------+

                    +-------------------------+
                    |                         |
                    |  Template Registry      |
                    |  (File-based)           |          reads
                    |  .docx / .odt files     |  <-----------------------+
                    |                         |                          |
                    +-------------------------+                          |
                                                                         |
                                                        +----------------+
```

**Actors:**
- **Booking Service**: Internal service that triggers voucher generation after booking confirmation
- **Voucher Merger System**: This system - generates vouchers from templates
- **File Storage**: Persists generated PDF and HTML vouchers
- **Template Registry**: Directory containing marketing-created templates

---

### Level 2: Container Diagram

```
+-----------------------------------------------------------------------------+
|                         Voucher Merger System                                |
|                                                                             |
|  +------------------+     +------------------+     +------------------+      |
|  |                  |     |                  |     |                  |      |
|  |  REST API        |---->|  Application     |---->|  Domain          |      |
|  |  (Primary        |     |  (Use Cases)     |     |  (Voucher        |      |
|  |   Adapter)       |     |                  |     |   Generation)    |      |
|  |                  |     |  - Generate      |     |                  |      |
|  |  POST /vouchers  |     |    Voucher       |     |  - Voucher       |      |
|  |  GET /health     |     |  - Check         |     |  - Template      |      |
|  |                  |     |    Existing      |     |  - MergeContext  |      |
|  +------------------+     +------------------+     +------------------+      |
|                                   |                        |                 |
|                                   | uses ports             | uses ports      |
|                                   v                        v                 |
|  +------------------+     +------------------+     +------------------+      |
|  |                  |     |                  |     |                  |      |
|  |  Template        |     |  Document        |     |  Voucher         |      |
|  |  Repository      |     |  Renderer        |     |  Storage         |      |
|  |  (Port)          |     |  (Port)          |     |  (Port)          |      |
|  |                  |     |                  |     |                  |      |
|  +--------+---------+     +--------+---------+     +--------+---------+      |
|           |                        |                        |                |
+-----------|------------------------|------------------------|----------------+
            |                        |                        |
            v                        v                        v
  +------------------+     +------------------+     +------------------+
  |                  |     |                  |     |                  |
  |  Filesystem      |     |  LibreOffice     |     |  Filesystem      |
  |  Template        |     |  Renderer        |     |  Storage         |
  |  Adapter         |     |  Adapter         |     |  Adapter         |
  |                  |     |  (headless)      |     |                  |
  +------------------+     +------------------+     +------------------+
            |                        |                        |
            v                        v                        v
      /templates/              LibreOffice              /vouchers/
      directory                 process               directory or S3
```

---

## Hexagonal Architecture

### Architecture Layers

```
+------------------------------------------------------------------+
|                        PRIMARY ADAPTERS                           |
|  (Driving - How the outside world talks to us)                   |
|                                                                  |
|  +------------------+                                            |
|  | REST API Adapter |  HTTP request -> Application Use Case      |
|  +------------------+                                            |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                      APPLICATION LAYER                            |
|  (Use Cases - Orchestration)                                     |
|                                                                  |
|  +------------------------+  +------------------------+          |
|  | GenerateVoucherUseCase |  | CheckExistingUseCase   |          |
|  +------------------------+  +------------------------+          |
|                                                                  |
|  Coordinates: validation, idempotency check, template loading,   |
|               merging, rendering, storage                        |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                        DOMAIN LAYER                               |
|  (Business Logic - Pure, no dependencies)                        |
|                                                                  |
|  Entities:           Value Objects:       Domain Services:       |
|  +--------+         +---------------+    +------------------+    |
|  | Voucher|         | VoucherId     |    | TemplateMerger   |    |
|  +--------+         | BookingRef    |    | (placeholder     |    |
|                     | CustomerData  |    |  substitution)   |    |
|  Aggregates:        | ServiceData   |    +------------------+    |
|  +----------+       | StorageUrls   |                            |
|  | Template |       +---------------+                            |
|  +----------+                                                    |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                         PORTS                                     |
|  (Interfaces - Contracts with external world)                    |
|                                                                  |
|  Secondary (Driven) Ports:                                       |
|  +--------------------+  +--------------------+                  |
|  | TemplateRepository |  | VoucherStorage     |                  |
|  | - find_by_id()     |  | - store()          |                  |
|  | - exists()         |  | - exists()         |                  |
|  +--------------------+  | - get_urls()       |                  |
|                          +--------------------+                  |
|  +--------------------+                                          |
|  | DocumentRenderer   |                                          |
|  | - render_pdf()     |                                          |
|  | - render_html()    |                                          |
|  +--------------------+                                          |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|                     SECONDARY ADAPTERS                            |
|  (Driven - How we talk to the outside world)                     |
|                                                                  |
|  +-------------------------+  +-------------------------+        |
|  | FilesystemTemplateRepo  |  | FilesystemVoucherStorage|        |
|  | - reads /templates/     |  | - writes /vouchers/     |        |
|  +-------------------------+  +-------------------------+        |
|                                                                  |
|  +-------------------------+  +-------------------------+        |
|  | LibreOfficeRenderer     |  | S3VoucherStorage        |        |
|  | - docx/odt -> PDF/HTML  |  | (future adapter)        |        |
|  +-------------------------+  +-------------------------+        |
+------------------------------------------------------------------+
```

---

## Component Interactions

### Request Flow: Generate Voucher (Happy Path)

```
Booking      REST        Generate        Template      Document      Voucher
Service      Adapter     VoucherUseCase  Repository    Renderer      Storage
   |            |              |              |             |            |
   |--POST----->|              |              |             |            |
   |            |--execute()-->|              |             |            |
   |            |              |--exists?---->|             |            |
   |            |              |<--voucher----|             |            | (idempotent check)
   |            |              |              |             |            |
   |            |              |--find()----->|             |            |
   |            |              |<--template---|             |            |
   |            |              |              |             |            |
   |            |              |--[merge in domain]-------->|            |
   |            |              |              |             |            |
   |            |              |--render_pdf()------------->|            |
   |            |              |<--pdf_bytes----------------|            |
   |            |              |              |             |            |
   |            |              |--render_html()------------>|            |
   |            |              |<--html_string--------------|            |
   |            |              |              |             |            |
   |            |              |--store()-------------------------------->|
   |            |              |<--urls------------------------------------
   |            |              |              |             |            |
   |            |<--response---|              |             |            |
   |<--201------|              |              |             |            |
```

### Request Flow: Duplicate Request (Idempotent)

```
Booking      REST        Generate        Voucher
Service      Adapter     VoucherUseCase  Storage
   |            |              |             |
   |--POST----->|              |             |
   |            |--execute()-->|             |
   |            |              |--exists?--->|
   |            |              |<--true------|
   |            |              |--get_urls-->|
   |            |              |<--urls------|
   |            |<--response---|             |
   |<--200------|              |             |
```

---

## Domain Model

### Aggregate: Voucher

```
+------------------------------------------------------------------+
|                          Voucher (Aggregate Root)                 |
+------------------------------------------------------------------+
| - voucher_id: VoucherId                                          |
| - booking_ref: BookingRef                                        |
| - template_id: TemplateId                                        |
| - generated_at: DateTime                                         |
| - storage_urls: StorageUrls                                      |
+------------------------------------------------------------------+
| + idempotency_key() -> string  (booking_id + service_date)       |
+------------------------------------------------------------------+

+---------------------------+    +---------------------------+
|      BookingRef           |    |      StorageUrls          |
+---------------------------+    +---------------------------+
| - booking_id: string      |    | - pdf_url: URL            |
| - service_date: Date      |    | - html_url: URL           |
+---------------------------+    +---------------------------+

+---------------------------+    +---------------------------+
|      CustomerData         |    |      ServiceData          |
+---------------------------+    +---------------------------+
| - first_name: string      |    | - name: string            |
| - last_name: string       |    | - provider: string        |
| - title?: string          |    | - pickup_time?: string    |
| - email?: string          |    | - pickup_location?: string|
| - phone?: string          |    | - dropoff_location?: string|
+---------------------------+    | - confirmation_code?: str |
                                 | - passengers?: int        |
                                 | - meeting_point?: string  |
                                 | - tour_time?: string      |
                                 | - notes?: string          |
                                 +---------------------------+
```

### Entity: Template

```
+------------------------------------------------------------------+
|                          Template                                 |
+------------------------------------------------------------------+
| - template_id: TemplateId                                        |
| - format: TemplateFormat (DOCX | ODT)                            |
| - content: bytes                                                 |
| - placeholders: List[string]                                     |
+------------------------------------------------------------------+
| + merge(context: MergeContext) -> MergedDocument                 |
+------------------------------------------------------------------+

+---------------------------+
|      MergeContext         |
+---------------------------+
| - customer: CustomerData  |
| - service: ServiceData    |
| - booking: BookingRef     |
+---------------------------+
| + to_placeholder_map()    |
+---------------------------+
```

---

## Port Definitions

### Primary Port: VoucherAPI

```
Interface: VoucherAPI (Driving Port)

generate_voucher(request: VoucherRequest) -> VoucherResponse
  - Accepts: template_id, booking_id, service_date, customer, service
  - Returns: voucher_id, urls, generated_at
  - Errors: ValidationError, TemplateNotFoundError, StorageError
```

### Secondary Port: TemplateRepository

```
Interface: TemplateRepository (Driven Port)

find_by_id(template_id: string) -> Template | None
  - Returns parsed template with identified placeholders
  - Returns None if template not found

exists(template_id: string) -> bool
  - Fast existence check without parsing
```

### Secondary Port: DocumentRenderer

```
Interface: DocumentRenderer (Driven Port)

render_pdf(merged_document: MergedDocument) -> bytes
  - Converts merged document to PDF binary
  - Preserves formatting, fonts, images

render_html(merged_document: MergedDocument) -> string
  - Converts merged document to HTML string
  - Inline CSS, base64 embedded images
```

### Secondary Port: VoucherStorage

```
Interface: VoucherStorage (Driven Port)

store(voucher_id: string, pdf: bytes, html: string, path: StoragePath) -> StorageUrls
  - Stores both files at path
  - Returns accessible URLs

exists(path: StoragePath) -> bool
  - Checks if voucher already exists (idempotency)

get_metadata(path: StoragePath) -> VoucherMetadata | None
  - Returns existing voucher metadata if exists
```

---

## Dependency Rules

### Allowed Dependencies

```
REST Adapter      -> Application (Use Cases)
Application       -> Domain, Ports
Domain            -> (nothing - pure)
Ports             -> Domain value objects only
Secondary Adapters -> Ports (implements), External libraries
```

### Forbidden Dependencies

- Domain MUST NOT depend on Application, Adapters, or Ports
- Ports MUST NOT depend on Adapters
- Primary Adapters MUST NOT depend on Secondary Adapters
- Application MUST NOT depend on Adapters (only Ports)

---

## Error Handling Strategy

### Error Categories

| Category | HTTP Status | Error Code | Retry |
|----------|-------------|------------|-------|
| Validation | 400 | VALIDATION_FAILED | No |
| Not Found | 404 | TEMPLATE_NOT_FOUND | No |
| Template Corrupt | 500 | TEMPLATE_ERROR | No |
| Storage Down | 503 | STORAGE_UNAVAILABLE | Yes |
| Render Failure | 500 | RENDER_ERROR | No |

### Error Response Structure (RFC 7807 inspired)

```json
{
  "error": "VALIDATION_FAILED",
  "message": "Request validation failed",
  "correlation_id": "uuid",
  "details": [
    {"field": "customer.last_name", "code": "REQUIRED_FIELD_MISSING"}
  ]
}
```

---

## Deployment Architecture

### Single Deployable Unit (Monolith)

```
+------------------------------------------------------------------+
|                    Container / VM / Process                       |
|                                                                  |
|  +------------------+  +------------------+  +------------------+  |
|  |   HTTP Server    |  |   Application    |  |   LibreOffice    |  |
|  |   (uvicorn/      |  |   Code           |  |   (headless)     |  |
|  |    gunicorn)     |  |                  |  |                  |  |
|  +------------------+  +------------------+  +------------------+  |
|                                                                  |
+------------------------------------------------------------------+
         |                                            |
         v                                            v
  +------------------+                      +------------------+
  |  /templates/     |                      |  /vouchers/      |
  |  (mounted vol)   |                      |  (mounted vol    |
  |                  |                      |   or S3)         |
  +------------------+                      +------------------+
```

### Configuration

| Config | Walking Skeleton | Production |
|--------|-----------------|------------|
| Template storage | Local /templates | Mounted volume |
| Voucher storage | Local /vouchers | S3 or mounted volume |
| PDF renderer | LibreOffice headless | LibreOffice headless |
| Concurrency | 1 worker | 4+ workers |

---

## Quality Attribute Strategies

### Performance (P95 < 2s)
- Cache parsed templates in memory (LRU)
- Connection pooling for storage
- Async I/O for storage operations
- LibreOffice process pool (avoid cold starts)

### Reliability (99.9%)
- Health check endpoint
- Graceful degradation on storage errors
- Correlation IDs for debugging
- Structured logging

### Idempotency (100%)
- Check storage path existence before processing
- Atomic write operations
- Return cached metadata for duplicates

### Security
- Internal-only API (no public exposure)
- No PII in logs (customer data masked)
- Storage URLs internal-accessible only

---

## Walking Skeleton Scope

For US-001 (Walking Skeleton), implement minimal versions:

| Component | Skeleton Implementation |
|-----------|------------------------|
| REST Adapter | Single endpoint POST /vouchers |
| Use Case | GenerateVoucher (no idempotency check) |
| Template Repo | Hardcoded single template |
| Renderer | LibreOffice headless (PDF only) |
| Storage | Local filesystem |
| Domain | Minimal Voucher, CustomerData, ServiceData |

**Deferring to later stories:**
- HTML generation (US-007)
- Template loading from registry (US-002)
- Idempotency check (US-009)
- Full validation (US-010)

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-17 | Morgan (Solution Architect) | Initial design |
