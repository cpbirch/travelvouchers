# User Stories: Voucher Generation System

## Story Map Overview

```
EPIC: Voucher Generation from Templates
|
+-- Feature 0: Walking Skeleton (US-001)
|
+-- Feature 1: Template Processing
|   +-- US-002: Load and Parse Template
|   +-- US-003: Validate Template Placeholders
|
+-- Feature 2: Data Merging
|   +-- US-004: Merge Customer Data
|   +-- US-005: Merge Service Data
|
+-- Feature 3: Output Generation
|   +-- US-006: Generate PDF Output
|   +-- US-007: Generate HTML Output
|
+-- Feature 4: Storage and Retrieval
|   +-- US-008: Store and Return Voucher URLs
|   +-- US-009: Idempotent Voucher Generation
|
+-- Feature 5: Validation and Errors
|   +-- US-010: Validate Request Data
|   +-- US-011: Return Structured Errors
```

---

## Feature 0: Walking Skeleton

### US-001: Minimal End-to-End Voucher Generation

**Problem (The Pain)**
The development team needs to validate that the architectural approach works before building full features. Without a walking skeleton, they risk building components that don't integrate.

**Who (The User)**
- Internal development team
- Context: Greenfield project with unproven architecture
- Motivation: Reduce integration risk early

**Solution (What We Build)**
A minimal end-to-end flow that:
1. Accepts a hardcoded template with one placeholder
2. Merges one data field
3. Produces a basic PDF
4. Returns a URL

**Domain Examples**

### Example 1: Simplest Happy Path
Maria Santos, a developer, calls the API with:
- Template: "skeleton-template" (hardcoded, contains `{{customer.last_name}}`)
- Customer: `{"first_name": "James", "last_name": "Morrison"}`
- Service: `{"name": "Test Service", "provider": "Test Provider"}`

The system returns a PDF URL. The PDF contains "Morrison".

### Example 2: Verify Integration Points
Carlos Rivera, lead developer, checks that:
- Template loading works (file system read)
- Placeholder replacement works (string substitution)
- PDF generation works (document conversion)
- Storage works (file write + URL return)

### Example 3: Missing Optional Field
Maria calls the API without `customer.title`. The system succeeds (title is optional), proving optional field handling works.

**UAT Scenarios (BDD)**

```gherkin
@walking-skeleton
Scenario: Generate minimal voucher end-to-end
  Given the skeleton template exists with placeholder "{{customer.last_name}}"
  And the storage service is available
  When I request a voucher with:
    | field        | value              |
    | template_id  | skeleton-template  |
    | booking_id   | BK-TEST-001        |
    | service_date | 2024-01-01         |
  And customer last_name is "Morrison"
  And service name is "Test Service" with provider "Test Provider"
  Then the response status is 201 Created
  And the response contains a pdf_url
  And the PDF at that URL contains "Morrison"

Scenario: Walking skeleton handles missing optional fields
  Given the skeleton template exists
  When I request a voucher without customer.title
  Then the response status is 201 Created
  And no error is returned
```

**Acceptance Criteria**
- [ ] API endpoint POST /vouchers accepts request and returns 201
- [ ] PDF is generated and stored
- [ ] PDF URL in response is accessible
- [ ] PDF contains merged customer.last_name value
- [ ] Missing optional fields do not cause errors

**Technical Notes**
- Hardcode template for walking skeleton (no template registry yet)
- Use simplest possible PDF generation (plain text acceptable)
- Storage can be local file system initially
- No HTML output required for skeleton

**Dependencies**
- None (first story)

**Effort Estimate**: 1-2 days

---

## Feature 1: Template Processing

### US-002: Load and Parse Word/LibreOffice Templates

**Problem (The Pain)**
The booking service team needs to use professionally designed templates created by marketing in Word/LibreOffice. Currently, there's no way to use these templates programmatically.

**Who (The User)**
- Booking Service (internal API consumer)
- Context: Integrating with marketing-created templates
- Motivation: Use branded, professional voucher designs

**Solution (What We Build)**
Template loading that:
1. Reads .docx and .odt files from template registry
2. Parses document structure preserving formatting
3. Identifies all `{{placeholder}}` tokens

**Domain Examples**

### Example 1: Load Airport Transfer Template
The booking service requests template "airport-transfer-v2". The system loads `/templates/airport-transfer-v2.docx`, a Word document created by Sarah Chen in Marketing. The document contains CityLink branding, formatted tables, and 12 placeholders.

### Example 2: Load LibreOffice Template
The booking service requests template "sightseeing-tour-v1". The system loads `/templates/sightseeing-tour-v1.odt`, created in LibreOffice by the Barcelona office. Same placeholder syntax works.

### Example 3: Template Not Found
The booking service requests template "old-template-2019". The system returns 404 because this template was removed from the registry.

**UAT Scenarios (BDD)**

```gherkin
Scenario: Load Word template successfully
  Given the template "airport-transfer-v2" exists as a .docx file
  When the system loads template "airport-transfer-v2"
  Then the template is parsed successfully
  And all placeholders are identified

Scenario: Load LibreOffice template successfully
  Given the template "sightseeing-tour-v1" exists as a .odt file
  When the system loads template "sightseeing-tour-v1"
  Then the template is parsed successfully

Scenario: Template not found returns 404
  Given the template "non-existent" does not exist
  When a voucher is requested with template_id "non-existent"
  Then the response status is 404 Not Found
  And the error code is "TEMPLATE_NOT_FOUND"
```

**Acceptance Criteria**
- [ ] System loads .docx files from template directory
- [ ] System loads .odt files from template directory
- [ ] Template formatting (fonts, tables, images) is preserved
- [ ] All `{{placeholder}}` tokens are identified
- [ ] Missing template returns 404 with TEMPLATE_NOT_FOUND error

**Technical Notes**
- Template directory location configurable
- Consider caching parsed templates for performance
- Placeholder regex: `\{\{[a-z_.]+\}\}`

**Dependencies**
- US-001 (Walking Skeleton) completed

**Effort Estimate**: 2-3 days

---

### US-003: Validate Template Placeholders Against Schema

**Problem (The Pain)**
When marketing creates templates with typos in placeholder names (e.g., `{{custmer.name}}`), the error isn't discovered until a customer receives a voucher with blank fields.

**Who (The User)**
- Marketing team (template creators)
- Context: Creating and updating voucher templates
- Motivation: Catch placeholder errors before production use

**Solution (What We Build)**
Template validation that:
1. Checks all placeholders against known schema
2. Reports unknown placeholders
3. Warns about optional fields that may be empty

**Domain Examples**

### Example 1: Valid Template
Sarah Chen uploads "airport-transfer-v3.docx". The validator confirms all 12 placeholders match the schema: `{{customer.title}}`, `{{customer.first_name}}`, etc.

### Example 2: Typo in Placeholder
Sarah uploads a template with `{{customer.lst_name}}`. The validator reports: "Unknown placeholder: customer.lst_name. Did you mean: customer.last_name?"

### Example 3: Warning for Optional Fields
Template uses `{{customer.phone}}`. Validator warns: "customer.phone is optional and may be empty for some vouchers."

**UAT Scenarios (BDD)**

```gherkin
Scenario: All placeholders valid
  Given a template with placeholders "{{customer.first_name}}", "{{service.name}}"
  When the template is validated
  Then validation passes with no errors

Scenario: Unknown placeholder detected
  Given a template with placeholder "{{customer.lst_name}}"
  When the template is validated
  Then validation fails with error "Unknown placeholder: customer.lst_name"
  And the error suggests "Did you mean: customer.last_name?"

Scenario: Optional field warning
  Given a template with placeholder "{{customer.phone}}"
  When the template is validated
  Then validation passes with warning "customer.phone is optional and may be empty"
```

**Acceptance Criteria**
- [ ] All placeholders validated against known schema
- [ ] Unknown placeholders reported with suggestions
- [ ] Optional field usage generates warnings
- [ ] Validation can run independently of voucher generation

**Technical Notes**
- Levenshtein distance for "did you mean" suggestions
- Validation endpoint: POST /templates/validate (future)

**Dependencies**
- US-002 (Load Templates) completed

**Effort Estimate**: 1-2 days

---

## Feature 2: Data Merging

### US-004: Merge Customer Data into Template

**Problem (The Pain)**
The booking service has customer data in JSON format, but templates expect formatted text. Manual copy-paste is error-prone and doesn't scale.

**Who (The User)**
- Booking Service
- Context: Has customer JSON, needs personalized voucher
- Motivation: Automated, error-free personalization

**Solution (What We Build)**
Customer data merging that:
1. Maps customer JSON fields to `{{customer.*}}` placeholders
2. Handles missing optional fields gracefully
3. Validates required fields are present

**Domain Examples**

### Example 1: Full Customer Data
James Morrison's booking includes: title "Mr", first_name "James", last_name "Morrison", email "j.morrison@email.com", phone "+44 7700 900123". All fields merge into template.

### Example 2: Minimal Customer Data
Elena Rodriguez's booking includes only first_name "Elena" and last_name "Rodriguez". Template renders "Elena Rodriguez" without title prefix.

### Example 3: Missing Required Field
A request arrives without last_name. System rejects with 400: "customer.last_name is required".

**UAT Scenarios (BDD)**

```gherkin
Scenario: Merge complete customer data
  Given a template with "Dear {{customer.title}} {{customer.last_name}}"
  And customer data:
    | field      | value    |
    | title      | Mr       |
    | first_name | James    |
    | last_name  | Morrison |
  When the data is merged
  Then the output contains "Dear Mr Morrison"

Scenario: Merge with missing optional title
  Given a template with "Dear {{customer.title}} {{customer.last_name}}"
  And customer data without title:
    | field      | value     |
    | first_name | Elena     |
    | last_name  | Rodriguez |
  When the data is merged
  Then the output contains "Dear  Rodriguez"

Scenario: Reject missing required field
  Given customer data without last_name
  When a voucher is requested
  Then the response status is 400 Bad Request
  And the error indicates "customer.last_name" is required
```

**Acceptance Criteria**
- [ ] All `{{customer.*}}` placeholders replaced with values
- [ ] Missing optional fields render as empty string
- [ ] Missing required fields (first_name, last_name) return 400
- [ ] Special characters in names handled correctly (O'Brien, Muller)

**Technical Notes**
- HTML-encode values when rendering to HTML output
- Consider locale-aware name formatting (future)

**Dependencies**
- US-002 (Load Templates) completed

**Effort Estimate**: 1-2 days

---

### US-005: Merge Service Data into Template

**Problem (The Pain)**
Each service type (transfer, tour, activity) has different data fields. The booking service needs a flexible way to merge any service type into templates.

**Who (The User)**
- Booking Service
- Context: Multiple service types with varying fields
- Motivation: Single API for all service vouchers

**Solution (What We Build)**
Service data merging that:
1. Maps service JSON fields to `{{service.*}}` placeholders
2. Handles service-type-specific optional fields
3. Validates required fields (name, provider)

**Domain Examples**

### Example 1: Airport Transfer Service
Service includes: name "Airport Transfer - Heathrow to Central", provider "CityLink Transfers Ltd", pickup_time "14:30", pickup_location "Terminal 5", dropoff_location "Marriott Hotel", passengers 2, confirmation_code "CLT-78432-HRW".

### Example 2: Sightseeing Tour Service
Service includes: name "London Eye and Thames Cruise", provider "City Sightseeing London", tour_time "10:00", meeting_point "Westminster Pier", duration "3 hours", confirmation_code "CSL-92156-LON". No pickup/dropoff fields.

### Example 3: Missing Provider
Service data lacks provider field. System rejects with 400: "service.provider is required".

**UAT Scenarios (BDD)**

```gherkin
Scenario: Merge transfer service data
  Given a template with "Pickup: {{service.pickup_time}} at {{service.pickup_location}}"
  And service data:
    | field           | value                  |
    | name            | Airport Transfer       |
    | provider        | CityLink Transfers     |
    | pickup_time     | 14:30                  |
    | pickup_location | Heathrow Terminal 5    |
  When the data is merged
  Then the output contains "Pickup: 14:30 at Heathrow Terminal 5"

Scenario: Merge tour service data
  Given a template with "Meet at {{service.meeting_point}} at {{service.tour_time}}"
  And service data:
    | field         | value            |
    | name          | London Eye Tour  |
    | provider      | City Sightseeing |
    | meeting_point | Westminster Pier |
    | tour_time     | 10:00            |
  When the data is merged
  Then the output contains "Meet at Westminster Pier at 10:00"

Scenario: Reject missing provider
  Given service data without provider
  When a voucher is requested
  Then the response status is 400 Bad Request
  And the error indicates "service.provider" is required
```

**Acceptance Criteria**
- [ ] All `{{service.*}}` placeholders replaced with values
- [ ] Missing optional service fields render as empty string
- [ ] Missing required fields (name, provider) return 400
- [ ] Different service types use same merge logic

**Technical Notes**
- Service schema is extensible (new fields don't require code changes)
- Consider time formatting (12h vs 24h) based on template locale

**Dependencies**
- US-002 (Load Templates) completed

**Effort Estimate**: 1-2 days

---

## Feature 3: Output Generation

### US-006: Generate PDF from Merged Document

**Problem (The Pain)**
Customers need printable vouchers for services that require physical presentation (hotel check-in, tour check-in). Digital-only formats are insufficient.

**Who (The User)**
- Holiday customer (end recipient)
- Context: Needs to print voucher or show on device
- Motivation: Have proof of booking at service location

**Solution (What We Build)**
PDF generation that:
1. Converts merged Word/LibreOffice document to PDF
2. Preserves formatting, fonts, and images
3. Produces file under 500KB

**Domain Examples**

### Example 1: Transfer Voucher PDF
James Morrison's airport transfer voucher is generated as PDF. The document shows CityLink branding, his name, pickup details, and is 127KB. He prints it at home.

### Example 2: Tour Voucher with Images
Elena Rodriguez's sightseeing tour voucher includes a small map image. PDF preserves the image at reasonable quality, total size 342KB.

### Example 3: Text-Heavy Voucher
A detailed activity voucher with terms and conditions spans 2 pages. PDF renders both pages correctly.

**UAT Scenarios (BDD)**

```gherkin
Scenario: Generate PDF with preserved formatting
  Given a merged document with formatted tables and bold text
  When PDF is generated
  Then the PDF preserves table structure
  And the PDF preserves bold formatting
  And the PDF file size is less than 500KB

Scenario: Generate PDF with images
  Given a merged document with a logo image
  When PDF is generated
  Then the PDF contains the image
  And the image is legible

Scenario: Generate multi-page PDF
  Given a merged document spanning 2 pages
  When PDF is generated
  Then the PDF has 2 pages
  And page breaks are in correct positions
```

**Acceptance Criteria**
- [ ] PDF generated from merged document
- [ ] Formatting preserved (fonts, tables, colors)
- [ ] Images preserved at reasonable quality
- [ ] File size under 500KB for typical vouchers
- [ ] PDF contains searchable text (not image-only)

**Technical Notes**
- LibreOffice headless or equivalent for conversion
- Consider PDF/A format for long-term readability

**Dependencies**
- US-004 (Merge Customer Data) completed
- US-005 (Merge Service Data) completed

**Effort Estimate**: 2-3 days

---

### US-007: Generate HTML from Merged Document

**Problem (The Pain)**
Customers often view vouchers on mobile devices or in email. PDFs are awkward on mobile. An HTML version provides better readability.

**Who (The User)**
- Holiday customer (end recipient)
- Context: Viewing voucher on phone or in email
- Motivation: Easy mobile viewing without PDF download

**Solution (What We Build)**
HTML generation that:
1. Converts merged document to HTML
2. Includes inline CSS for email compatibility
3. Renders without external resources

**Domain Examples**

### Example 1: Email-Ready HTML
The booking system emails James Morrison his transfer voucher. The HTML renders correctly in Gmail, Outlook, and Apple Mail with all styling intact.

### Example 2: Mobile-Friendly HTML
Elena Rodriguez opens her voucher link on her iPhone. The HTML adapts to screen width and is easily readable.

### Example 3: Offline-Capable HTML
A customer opens the HTML voucher URL while in airplane mode (previously cached). All images are inline base64, so it renders completely.

**UAT Scenarios (BDD)**

```gherkin
Scenario: Generate email-compatible HTML
  Given a merged document with styled content
  When HTML is generated
  Then the HTML includes inline CSS (no external stylesheets)
  And the HTML renders correctly in major email clients

Scenario: Generate HTML without external dependencies
  Given a merged document with images
  When HTML is generated
  Then images are embedded as base64 data URIs
  And no external URLs are referenced

Scenario: HTML validates as HTML5
  Given a generated HTML voucher
  When validated against HTML5 spec
  Then no validation errors are reported
```

**Acceptance Criteria**
- [ ] HTML generated from merged document
- [ ] CSS is inline (no external stylesheets)
- [ ] Images embedded as base64 data URIs
- [ ] Valid HTML5 document structure
- [ ] Renders correctly without network access

**Technical Notes**
- Use table-based layout for email client compatibility
- Inline all styles using style attribute
- Base64 images may increase file size significantly

**Dependencies**
- US-004 (Merge Customer Data) completed
- US-005 (Merge Service Data) completed

**Effort Estimate**: 2-3 days

---

## Feature 4: Storage and Retrieval

### US-008: Store Vouchers and Return Access URLs

**Problem (The Pain)**
Generated vouchers need to be accessible later (customer re-downloads, support retrieval). In-memory generation is insufficient.

**Who (The User)**
- Booking Service (needs URLs to share)
- Customer (needs to re-access voucher)
- Support team (needs to retrieve for troubleshooting)

**Solution (What We Build)**
Storage that:
1. Stores PDF and HTML in persistent storage
2. Generates accessible URLs
3. Organizes by booking_id and service_date

**Domain Examples**

### Example 1: Store and Return URLs
James Morrison's voucher is stored at:
- PDF: `/vouchers/BK-2024-78432/2024-03-15/voucher.pdf`
- HTML: `/vouchers/BK-2024-78432/2024-03-15/voucher.html`

The API returns full URLs that the booking system emails to James.

### Example 2: Support Retrieval
A support agent needs to see what voucher was sent for booking BK-2024-78432. They can construct the URL from booking_id and service_date.

### Example 3: Storage Failure Handling
Storage service is temporarily unavailable. The API returns 503 with Retry-After header. Booking service retries.

**UAT Scenarios (BDD)**

```gherkin
Scenario: Store voucher and return URLs
  Given a generated PDF and HTML voucher
  When the voucher is stored
  Then PDF is stored at /vouchers/{booking_id}/{service_date}/voucher.pdf
  And HTML is stored at /vouchers/{booking_id}/{service_date}/voucher.html
  And the response contains accessible pdf_url and html_url

Scenario: URLs are accessible
  Given a stored voucher with URLs
  When the pdf_url is accessed
  Then the PDF content is returned
  When the html_url is accessed
  Then the HTML content is returned

Scenario: Storage failure returns 503
  Given the storage service is unavailable
  When a voucher generation is attempted
  Then the response status is 503 Service Unavailable
  And the response includes Retry-After header
```

**Acceptance Criteria**
- [ ] PDF stored at predictable path
- [ ] HTML stored at predictable path
- [ ] URLs returned in API response
- [ ] URLs are accessible by authorized services
- [ ] Storage failure returns 503 with Retry-After

**Technical Notes**
- Storage backend configurable (S3, Azure Blob, local filesystem)
- Consider signed URLs for security (time-limited access)

**Dependencies**
- US-006 (Generate PDF) completed
- US-007 (Generate HTML) completed

**Effort Estimate**: 1-2 days

---

### US-009: Idempotent Voucher Generation

**Problem (The Pain)**
The booking service may accidentally call the voucher API twice for the same booking (retry logic, duplicate events). Without idempotency, this creates duplicate storage and confusing multiple URLs.

**Who (The User)**
- Booking Service
- Context: Distributed system with retry logic
- Motivation: Safe retries without side effects

**Solution (What We Build)**
Idempotency that:
1. Uses booking_id + service_date as idempotency key
2. Returns existing voucher on duplicate request
3. Does not regenerate or re-store

**Domain Examples**

### Example 1: Duplicate Request Returns Existing
Booking service calls API for BK-2024-78432 / 2024-03-15 at 10:23:45. Due to network timeout, it retries at 10:23:52. Second call returns the voucher generated at 10:23:45 with status 200.

### Example 2: Same Booking, Different Date
Booking BK-2024-78432 has a transfer on 2024-03-15 and another on 2024-03-16. Each date gets its own voucher (different idempotency keys).

### Example 3: Different Booking, Same Date
Bookings BK-2024-78432 and BK-2024-78433 both have transfers on 2024-03-15. Each booking gets its own voucher.

**UAT Scenarios (BDD)**

```gherkin
Scenario: Duplicate request returns existing voucher
  Given a voucher was generated for booking "BK-2024-78432" date "2024-03-15" at "10:23:45"
  When a voucher is requested for the same booking and date
  Then the response status is 200 OK
  And the response contains the original voucher_id
  And generated_at is "10:23:45" (original timestamp)
  And no new files are written to storage

Scenario: Same booking different dates creates separate vouchers
  Given a voucher exists for booking "BK-2024-78432" date "2024-03-15"
  When a voucher is requested for booking "BK-2024-78432" date "2024-03-16"
  Then the response status is 201 Created
  And a new voucher_id is returned
```

**Acceptance Criteria**
- [ ] Idempotency key is booking_id + service_date
- [ ] Duplicate request returns 200 (not 201)
- [ ] Original generated_at timestamp preserved
- [ ] No storage write on duplicate
- [ ] Different dates = different vouchers

**Technical Notes**
- Store idempotency index (booking_id + date -> voucher_id)
- Consider database vs storage metadata for index

**Dependencies**
- US-008 (Store Vouchers) completed

**Effort Estimate**: 1 day

---

## Feature 5: Validation and Errors

### US-010: Validate Request Data Before Processing

**Problem (The Pain)**
If validation happens late in the process (e.g., during merge), the booking service gets confusing errors. Early validation with clear messages speeds up integration.

**Who (The User)**
- Booking Service developer
- Context: Integrating with voucher API
- Motivation: Clear, actionable error messages

**Solution (What We Build)**
Input validation that:
1. Validates all fields before any processing
2. Returns all validation errors at once (not one at a time)
3. Provides field-level error codes

**Domain Examples**

### Example 1: Multiple Validation Errors
Request has invalid date format AND missing customer.last_name. Response includes both errors so developer can fix both at once.

### Example 2: Invalid Date Format
service_date is "15-03-2024" (DD-MM-YYYY). Error says: "service_date must be ISO 8601 format (YYYY-MM-DD)".

### Example 3: Invalid Booking ID Format
booking_id is "78432" (missing prefix). Error says: "booking_id must match pattern BK-YYYY-NNNNN".

**UAT Scenarios (BDD)**

```gherkin
Scenario: Return all validation errors at once
  Given a request with:
    | issue               | field              |
    | missing             | customer.last_name |
    | invalid format      | service_date       |
  When the request is validated
  Then the response includes both errors
  And each error has field and code

Scenario: Validate date format
  Given service_date is "15-03-2024"
  When the request is validated
  Then error code is "INVALID_DATE_FORMAT"
  And error message mentions "ISO 8601"

Scenario: Validate booking_id format
  Given booking_id is "78432"
  When the request is validated
  Then error code is "INVALID_FORMAT"
  And error message mentions "BK-YYYY-NNNNN"
```

**Acceptance Criteria**
- [ ] All validation runs before processing starts
- [ ] Multiple errors returned in single response
- [ ] Each error includes field path and error code
- [ ] Error messages are actionable (include expected format)

**Technical Notes**
- Use JSON Schema validation as baseline
- Add custom validators for business rules

**Dependencies**
- US-001 (Walking Skeleton) completed

**Effort Estimate**: 1 day

---

### US-011: Return Structured Error Responses

**Problem (The Pain)**
Unstructured error messages ("Something went wrong") force developers to guess what failed. Structured errors enable programmatic handling.

**Who (The User)**
- Booking Service developer
- Context: Building error handling for integration
- Motivation: Programmatic error handling

**Solution (What We Build)**
Structured errors that:
1. Include error code, message, and details
2. Use consistent schema across all error types
3. Include correlation ID for support

**Domain Examples**

### Example 1: Validation Error Structure
```json
{
  "error": "VALIDATION_FAILED",
  "message": "Request validation failed",
  "correlation_id": "abc-123-def",
  "details": [
    {"field": "customer.last_name", "code": "REQUIRED_FIELD_MISSING", "message": "Customer last name is required"}
  ]
}
```

### Example 2: Template Error Structure
```json
{
  "error": "TEMPLATE_NOT_FOUND",
  "message": "Template 'old-template' not found",
  "correlation_id": "xyz-456-ghi",
  "details": []
}
```

### Example 3: Storage Error with Retry
```json
{
  "error": "STORAGE_UNAVAILABLE",
  "message": "Storage service temporarily unavailable",
  "correlation_id": "mno-789-pqr",
  "retry_after": 30
}
```

**UAT Scenarios (BDD)**

```gherkin
Scenario: Validation error includes details array
  Given a validation failure occurs
  When the error response is returned
  Then the response includes "error" code
  And the response includes "message"
  And the response includes "correlation_id"
  And the response includes "details" array

Scenario: Storage error includes retry_after
  Given a storage failure occurs
  When the error response is returned
  Then the response includes "retry_after" in seconds
  And HTTP header "Retry-After" is set
```

**Acceptance Criteria**
- [ ] All errors use consistent JSON structure
- [ ] Error code is machine-readable (enum)
- [ ] Message is human-readable
- [ ] Correlation ID present for tracing
- [ ] 503 errors include retry_after

**Technical Notes**
- Log correlation ID with all error logs
- Consider RFC 7807 (Problem Details for HTTP APIs)

**Dependencies**
- US-010 (Validate Request Data) completed

**Effort Estimate**: 1 day

---

## Story Dependency Graph

```
US-001 (Walking Skeleton)
   |
   +---> US-002 (Load Templates)
   |        |
   |        +---> US-003 (Validate Placeholders)
   |        |
   |        +---> US-004 (Merge Customer)
   |        |        |
   |        +---> US-005 (Merge Service)
   |                 |
   |                 v
   |        +---> US-006 (Generate PDF)
   |        |        |
   |        +---> US-007 (Generate HTML)
   |                 |
   |                 v
   |        +---> US-008 (Store Vouchers)
   |                 |
   |                 +---> US-009 (Idempotency)
   |
   +---> US-010 (Validate Request)
            |
            +---> US-011 (Structured Errors)
```

## Implementation Order (Recommended)

1. **Sprint 1 - Foundation**
   - US-001: Walking Skeleton (validates architecture)
   - US-010: Validate Request Data

2. **Sprint 2 - Core Flow**
   - US-002: Load Templates
   - US-004: Merge Customer Data
   - US-005: Merge Service Data

3. **Sprint 3 - Output**
   - US-006: Generate PDF
   - US-007: Generate HTML
   - US-008: Store Vouchers

4. **Sprint 4 - Robustness**
   - US-009: Idempotency
   - US-011: Structured Errors
   - US-003: Validate Placeholders
