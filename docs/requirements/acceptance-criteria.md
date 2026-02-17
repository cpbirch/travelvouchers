# Acceptance Criteria: Voucher Generation System

This document consolidates all acceptance criteria and Gherkin scenarios for the voucher generation system.

---

## Feature 0: Walking Skeleton

### US-001: Minimal End-to-End Voucher Generation

**Acceptance Criteria**
- [ ] API endpoint POST /vouchers accepts request and returns 201
- [ ] PDF is generated and stored
- [ ] PDF URL in response is accessible
- [ ] PDF contains merged customer.last_name value
- [ ] Missing optional fields do not cause errors

**Gherkin Scenarios**

```gherkin
Feature: Walking Skeleton - Minimal Voucher Generation
  As a developer
  I want to validate the end-to-end architecture
  So that I can build features on a proven foundation

  @walking-skeleton @critical
  Scenario: Generate minimal voucher end-to-end
    Given the skeleton template exists with placeholder "{{customer.last_name}}"
    And the storage service is available
    When I request a voucher with:
      | field        | value              |
      | template_id  | skeleton-template  |
      | booking_id   | BK-TEST-001        |
      | service_date | 2024-01-01         |
    And customer data:
      | field      | value    |
      | first_name | James    |
      | last_name  | Morrison |
    And service data:
      | field    | value         |
      | name     | Test Service  |
      | provider | Test Provider |
    Then the response status is 201 Created
    And the response contains a pdf_url
    And the PDF at that URL contains "Morrison"

  @walking-skeleton
  Scenario: Walking skeleton handles missing optional fields
    Given the skeleton template exists
    When I request a voucher without customer.title
    Then the response status is 201 Created
    And no error is returned
```

---

## Feature 1: Template Processing

### US-002: Load and Parse Word/LibreOffice Templates

**Acceptance Criteria**
- [ ] System loads .docx files from template directory
- [ ] System loads .odt files from template directory
- [ ] Template formatting (fonts, tables, images) is preserved
- [ ] All `{{placeholder}}` tokens are identified
- [ ] Missing template returns 404 with TEMPLATE_NOT_FOUND error

**Gherkin Scenarios**

```gherkin
Feature: Template Loading
  As a booking service
  I want to use marketing-created templates
  So that vouchers have professional branding

  @template @happy-path
  Scenario: Load Word template successfully
    Given the template "airport-transfer-v2" exists as a .docx file
    And the template contains placeholders:
      | placeholder              |
      | {{customer.first_name}}  |
      | {{customer.last_name}}   |
      | {{service.name}}         |
    When the system loads template "airport-transfer-v2"
    Then the template is parsed successfully
    And 3 placeholders are identified

  @template @happy-path
  Scenario: Load LibreOffice template successfully
    Given the template "sightseeing-tour-v1" exists as a .odt file
    When the system loads template "sightseeing-tour-v1"
    Then the template is parsed successfully

  @template @error
  Scenario: Template not found returns 404
    Given the template "non-existent" does not exist
    When a voucher is requested with template_id "non-existent"
    Then the response status is 404 Not Found
    And the error code is "TEMPLATE_NOT_FOUND"
    And the error message contains "non-existent"
```

### US-003: Validate Template Placeholders

**Acceptance Criteria**
- [ ] All placeholders validated against known schema
- [ ] Unknown placeholders reported with suggestions
- [ ] Optional field usage generates warnings
- [ ] Validation can run independently of voucher generation

**Gherkin Scenarios**

```gherkin
Feature: Template Placeholder Validation
  As a marketing user
  I want to validate templates before use
  So that placeholder typos are caught early

  @validation @template
  Scenario: All placeholders valid
    Given a template with placeholders:
      | placeholder              |
      | {{customer.first_name}}  |
      | {{service.name}}         |
    When the template is validated
    Then validation passes with no errors

  @validation @template @error
  Scenario: Unknown placeholder detected
    Given a template with placeholder "{{customer.lst_name}}"
    When the template is validated
    Then validation fails with error for "customer.lst_name"
    And the error suggests "Did you mean: customer.last_name?"

  @validation @template @warning
  Scenario: Optional field warning
    Given a template with placeholder "{{customer.phone}}"
    When the template is validated
    Then validation passes
    And a warning is generated: "customer.phone is optional and may be empty"
```

---

## Feature 2: Data Merging

### US-004: Merge Customer Data

**Acceptance Criteria**
- [ ] All `{{customer.*}}` placeholders replaced with values
- [ ] Missing optional fields render as empty string
- [ ] Missing required fields (first_name, last_name) return 400
- [ ] Special characters in names handled correctly (O'Brien, Muller)

**Gherkin Scenarios**

```gherkin
Feature: Customer Data Merging
  As a booking service
  I want customer data merged into templates
  So that vouchers are personalized

  @merge @customer @happy-path
  Scenario: Merge complete customer data
    Given a template with "Dear {{customer.title}} {{customer.last_name}}"
    And customer data:
      | field      | value    |
      | title      | Mr       |
      | first_name | James    |
      | last_name  | Morrison |
    When the data is merged
    Then the output contains "Dear Mr Morrison"

  @merge @customer @optional
  Scenario: Merge with missing optional title
    Given a template with "Dear {{customer.title}} {{customer.last_name}}"
    And customer data:
      | field      | value     |
      | first_name | Elena     |
      | last_name  | Rodriguez |
    When the data is merged
    Then the output contains "Dear  Rodriguez"

  @merge @customer @error
  Scenario: Reject missing required field
    Given customer data:
      | field      | value |
      | first_name | James |
    And customer data is missing "last_name"
    When a voucher is requested
    Then the response status is 400 Bad Request
    And the error details include:
      | field              | code                   |
      | customer.last_name | REQUIRED_FIELD_MISSING |

  @merge @customer @edge-case
  Scenario: Handle special characters in names
    Given customer data:
      | field      | value    |
      | first_name | Patrick  |
      | last_name  | O'Brien  |
    When the data is merged
    Then the output contains "O'Brien" (apostrophe preserved)
```

### US-005: Merge Service Data

**Acceptance Criteria**
- [ ] All `{{service.*}}` placeholders replaced with values
- [ ] Missing optional service fields render as empty string
- [ ] Missing required fields (name, provider) return 400
- [ ] Different service types use same merge logic

**Gherkin Scenarios**

```gherkin
Feature: Service Data Merging
  As a booking service
  I want service data merged into templates
  So that vouchers show booking details

  @merge @service @happy-path
  Scenario: Merge transfer service data
    Given a template with "Pickup: {{service.pickup_time}} at {{service.pickup_location}}"
    And service data:
      | field           | value               |
      | name            | Airport Transfer    |
      | provider        | CityLink Transfers  |
      | pickup_time     | 14:30               |
      | pickup_location | Heathrow Terminal 5 |
    When the data is merged
    Then the output contains "Pickup: 14:30 at Heathrow Terminal 5"

  @merge @service @happy-path
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

  @merge @service @error
  Scenario: Reject missing provider
    Given service data:
      | field | value            |
      | name  | Airport Transfer |
    And service data is missing "provider"
    When a voucher is requested
    Then the response status is 400 Bad Request
    And the error details include:
      | field            | code                   |
      | service.provider | REQUIRED_FIELD_MISSING |
```

---

## Feature 3: Output Generation

### US-006: Generate PDF Output

**Acceptance Criteria**
- [ ] PDF generated from merged document
- [ ] Formatting preserved (fonts, tables, colors)
- [ ] Images preserved at reasonable quality
- [ ] File size under 500KB for typical vouchers
- [ ] PDF contains searchable text (not image-only)

**Gherkin Scenarios**

```gherkin
Feature: PDF Generation
  As a customer
  I want a printable PDF voucher
  So that I can present it at the service location

  @output @pdf @happy-path
  Scenario: Generate PDF with preserved formatting
    Given a merged document with:
      | element    | present |
      | tables     | yes     |
      | bold text  | yes     |
      | colors     | yes     |
    When PDF is generated
    Then the PDF preserves table structure
    And the PDF preserves bold formatting
    And the PDF preserves colors

  @output @pdf @size
  Scenario: PDF file size within limits
    Given a typical merged voucher document
    When PDF is generated
    Then the PDF file size is less than 500KB

  @output @pdf @images
  Scenario: Generate PDF with images
    Given a merged document with a logo image
    When PDF is generated
    Then the PDF contains the image
    And the image is legible at print resolution

  @output @pdf @multipage
  Scenario: Generate multi-page PDF
    Given a merged document spanning 2 pages
    When PDF is generated
    Then the PDF has 2 pages
    And page breaks are in correct positions

  @output @pdf @searchable
  Scenario: PDF contains searchable text
    Given a generated PDF with text "Morrison"
    When text search is performed for "Morrison"
    Then the text is found in the PDF
```

### US-007: Generate HTML Output

**Acceptance Criteria**
- [ ] HTML generated from merged document
- [ ] CSS is inline (no external stylesheets)
- [ ] Images embedded as base64 data URIs
- [ ] Valid HTML5 document structure
- [ ] Renders correctly without network access

**Gherkin Scenarios**

```gherkin
Feature: HTML Generation
  As a customer
  I want an HTML voucher
  So that I can view it on mobile or in email

  @output @html @happy-path
  Scenario: Generate email-compatible HTML
    Given a merged document with styled content
    When HTML is generated
    Then the HTML includes inline CSS
    And no external stylesheet links are present

  @output @html @images
  Scenario: Generate HTML with embedded images
    Given a merged document with a logo image
    When HTML is generated
    Then images are embedded as base64 data URIs
    And no external image URLs are referenced

  @output @html @validation
  Scenario: HTML validates as HTML5
    Given a generated HTML voucher
    When validated against HTML5 spec
    Then no validation errors are reported

  @output @html @offline
  Scenario: HTML renders without network
    Given a generated HTML voucher
    When rendered in a browser with network disabled
    Then the voucher displays completely
    And all images are visible
```

---

## Feature 4: Storage and Retrieval

### US-008: Store Vouchers and Return URLs

**Acceptance Criteria**
- [ ] PDF stored at predictable path
- [ ] HTML stored at predictable path
- [ ] URLs returned in API response
- [ ] URLs are accessible by authorized services
- [ ] Storage failure returns 503 with Retry-After

**Gherkin Scenarios**

```gherkin
Feature: Voucher Storage
  As a booking service
  I want vouchers stored with accessible URLs
  So that customers can download them later

  @storage @happy-path
  Scenario: Store voucher and return URLs
    Given a generated PDF and HTML voucher
    And booking_id is "BK-2024-78432"
    And service_date is "2024-03-15"
    When the voucher is stored
    Then PDF is stored at path containing "BK-2024-78432/2024-03-15"
    And HTML is stored at path containing "BK-2024-78432/2024-03-15"
    And the response contains "pdf_url"
    And the response contains "html_url"

  @storage @access
  Scenario: Stored URLs are accessible
    Given a stored voucher with:
      | url_type | url                                              |
      | pdf_url  | https://storage.example.com/.../voucher.pdf      |
      | html_url | https://storage.example.com/.../voucher.html     |
    When the pdf_url is accessed
    Then HTTP status is 200
    And Content-Type is "application/pdf"
    When the html_url is accessed
    Then HTTP status is 200
    And Content-Type is "text/html"

  @storage @error
  Scenario: Storage failure returns 503
    Given the storage service is unavailable
    When a voucher generation is attempted
    Then the response status is 503 Service Unavailable
    And the error code is "STORAGE_UNAVAILABLE"
    And the response includes "Retry-After" header
```

### US-009: Idempotent Voucher Generation

**Acceptance Criteria**
- [ ] Idempotency key is booking_id + service_date
- [ ] Duplicate request returns 200 (not 201)
- [ ] Original generated_at timestamp preserved
- [ ] No storage write on duplicate
- [ ] Different dates = different vouchers

**Gherkin Scenarios**

```gherkin
Feature: Idempotent Generation
  As a booking service
  I want safe retry behavior
  So that network issues don't create duplicates

  @idempotency @critical
  Scenario: Duplicate request returns existing voucher
    Given a voucher was generated with:
      | field        | value             |
      | booking_id   | BK-2024-78432     |
      | service_date | 2024-03-15        |
      | voucher_id   | V-2024-78432-0315 |
      | generated_at | 2024-02-17T10:23:45Z |
    When a voucher is requested with:
      | field        | value         |
      | booking_id   | BK-2024-78432 |
      | service_date | 2024-03-15    |
    Then the response status is 200 OK
    And the response contains voucher_id "V-2024-78432-0315"
    And the response contains generated_at "2024-02-17T10:23:45Z"
    And no new files are written to storage

  @idempotency
  Scenario: Same booking different dates creates separate vouchers
    Given a voucher exists for booking "BK-2024-78432" date "2024-03-15"
    When a voucher is requested with:
      | field        | value         |
      | booking_id   | BK-2024-78432 |
      | service_date | 2024-03-16    |
    Then the response status is 201 Created
    And the voucher_id is different from the existing voucher

  @idempotency
  Scenario: Different bookings same date creates separate vouchers
    Given a voucher exists for booking "BK-2024-78432" date "2024-03-15"
    When a voucher is requested with:
      | field        | value         |
      | booking_id   | BK-2024-78433 |
      | service_date | 2024-03-15    |
    Then the response status is 201 Created
    And the voucher_id is different from the existing voucher
```

---

## Feature 5: Validation and Errors

### US-010: Validate Request Data

**Acceptance Criteria**
- [ ] All validation runs before processing starts
- [ ] Multiple errors returned in single response
- [ ] Each error includes field path and error code
- [ ] Error messages are actionable (include expected format)

**Gherkin Scenarios**

```gherkin
Feature: Request Validation
  As a booking service developer
  I want clear validation errors
  So that I can fix integration issues quickly

  @validation @request
  Scenario: Return all validation errors at once
    Given a request with multiple issues:
      | field              | issue          |
      | customer.last_name | missing        |
      | service_date       | invalid format |
    When the request is validated
    Then the response status is 400 Bad Request
    And the error details include 2 items
    And error for "customer.last_name" has code "REQUIRED_FIELD_MISSING"
    And error for "service_date" has code "INVALID_DATE_FORMAT"

  @validation @request @date
  Scenario: Validate date format
    Given service_date is "15-03-2024"
    When the request is validated
    Then the response status is 400 Bad Request
    And error code is "INVALID_DATE_FORMAT"
    And error message contains "ISO 8601"
    And error message contains "YYYY-MM-DD"

  @validation @request @booking-id
  Scenario: Validate booking_id format
    Given booking_id is "78432"
    When the request is validated
    Then the response status is 400 Bad Request
    And error code is "INVALID_FORMAT"
    And error message contains "BK-YYYY-NNNNN"
```

### US-011: Structured Error Responses

**Acceptance Criteria**
- [ ] All errors use consistent JSON structure
- [ ] Error code is machine-readable (enum)
- [ ] Message is human-readable
- [ ] Correlation ID present for tracing
- [ ] 503 errors include retry_after

**Gherkin Scenarios**

```gherkin
Feature: Error Response Structure
  As a booking service developer
  I want structured error responses
  So that I can handle errors programmatically

  @error @structure
  Scenario: Validation error structure
    Given a validation failure occurs
    When the error response is returned
    Then the response contains:
      | field          | type   |
      | error          | string |
      | message        | string |
      | correlation_id | string |
      | details        | array  |

  @error @structure
  Scenario: Template error structure
    Given template "missing-template" does not exist
    When a voucher is requested with that template
    Then the response status is 404 Not Found
    And the response contains:
      | field          | value              |
      | error          | TEMPLATE_NOT_FOUND |
      | correlation_id | (present)          |

  @error @structure @retry
  Scenario: Storage error includes retry_after
    Given the storage service is unavailable
    When a voucher generation fails
    Then the response status is 503 Service Unavailable
    And the response contains:
      | field       | type    |
      | error       | string  |
      | retry_after | integer |
    And HTTP header "Retry-After" is present
```

---

## Cross-Cutting Scenarios

### Security

```gherkin
Feature: Security
  As a system administrator
  I want the API secured
  So that only authorized services can generate vouchers

  @security @critical
  Scenario: Unauthenticated request rejected
    Given no authentication credentials
    When a voucher is requested
    Then the response status is 401 Unauthorized

  @security
  Scenario: PII not logged
    Given a voucher is generated with customer email "j.morrison@email.com"
    When checking application logs
    Then the email address does not appear in logs
```

### Performance

```gherkin
Feature: Performance
  As a booking service
  I want fast voucher generation
  So that customers don't wait long

  @performance @critical
  Scenario: Generation completes within SLA
    Given a typical voucher request
    When the voucher is generated
    Then the response is received within 2 seconds (P95)

  @performance
  Scenario: Concurrent requests handled
    Given 10 simultaneous voucher requests
    When all requests are processed
    Then all requests complete successfully
    And no request exceeds 5 seconds
```
