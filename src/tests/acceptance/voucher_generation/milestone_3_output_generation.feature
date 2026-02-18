@milestone-3 @output
Feature: Output Generation and Storage
  As a customer
  I want printable PDF and viewable HTML vouchers
  So that I can present them at service locations or view on mobile

  Background:
    Given the airport transfer template exists
    And the storage service is available

  # ============================================================================
  # US-006: Generate PDF from Merged Document
  # Sprint 3 - Output Generation
  # ============================================================================

  @us-006
  Scenario: Generate PDF with preserved formatting
    # Voucher retains the professional formatting from the marketing-created template.
    Given the template contains formatted elements:
      | element    | description           |
      | tables     | pickup details table  |
      | bold text  | service provider name |
      | colors     | company branding      |
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-60001       |
      | service_date | 2024-03-15          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers Ltd"
    Then the voucher is created successfully
    And the PDF preserves table structure
    And the PDF preserves text formatting

  @us-006 @skip
  Scenario: Generated PDF is within size limits
    # PDFs must be under 500KB to ensure fast downloads and email attachment compatibility.
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-60002       |
      | service_date | 2024-03-16          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the PDF file size is less than 500KB

  @us-006 @skip
  Scenario: Generated PDF contains searchable text
    # The PDF must contain actual text (not images of text) so customers
    # can search and copy information like confirmation codes.
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-60003       |
      | service_date | 2024-03-17          |
    And customer "James" "Morrison"
    And service details:
      | field             | value         |
      | name              | Airport Transfer |
      | provider          | CityLink      |
      | confirmation_code | CLT-99999-HRW |
    Then the voucher is created successfully
    And the PDF text is searchable
    And searching the PDF for "CLT-99999-HRW" finds a match

  @us-006 @skip
  Scenario: Generated PDF with embedded logo image
    # The CityLink logo from the template is preserved in the PDF.
    Given the template contains a company logo image
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-60004       |
      | service_date | 2024-03-18          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the PDF contains embedded images

  @us-006 @skip
  Scenario: Multi-page voucher with terms and conditions
    # Some vouchers include lengthy terms that span multiple pages.
    # Page breaks should be preserved correctly.
    Given the template "detailed-voucher-v1" spans multiple pages
    When I request a voucher for:
      | field        | value              |
      | template_id  | detailed-voucher-v1|
      | booking_id   | BK-2024-60005      |
      | service_date | 2024-03-19         |
    And customer "James" "Morrison"
    And service "Premium Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the PDF has multiple pages

  # ============================================================================
  # US-007: Generate HTML from Merged Document
  # Sprint 3 - Output Generation
  # ============================================================================

  @us-007
  Scenario: Generate email-compatible HTML
    # Elena Rodriguez receives her voucher by email.
    # The HTML must render correctly in Gmail, Outlook, and Apple Mail.
    When I request a voucher for:
      | field        | value               |
      | template_id  | sightseeing-tour-v1 |
      | booking_id   | BK-2024-70001       |
      | service_date | 2024-04-20          |
    And customer "Elena" "Rodriguez"
    And service "London Eye Tour" provided by "City Sightseeing"
    Then the voucher is created successfully
    And the response contains an HTML URL
    And the HTML includes inline CSS
    And the HTML has no external stylesheet links

  @us-007 @skip
  Scenario: HTML renders without network dependencies
    # A customer opens the voucher while in airplane mode.
    # All resources must be embedded, not fetched from external URLs.
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-70002       |
      | service_date | 2024-03-21          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the HTML has no external resource URLs
    And images are embedded as base64 data URIs

  @us-007 @skip
  Scenario: Generated HTML is valid HTML5
    # The HTML document should be valid HTML5 for maximum browser compatibility.
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-70003       |
      | service_date | 2024-03-22          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the HTML is valid HTML5

  @us-007 @skip
  Scenario: HTML contains all merged content
    # All the same content in the PDF appears in the HTML version.
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-70004       |
      | service_date | 2024-03-23          |
    And customer "James" "Morrison" with title "Mr"
    And service details:
      | field             | value                   |
      | name              | Airport Transfer        |
      | provider          | CityLink Transfers Ltd  |
      | confirmation_code | CLT-70004-HRW           |
    Then the voucher is created successfully
    And the HTML contains "Mr Morrison"
    And the HTML contains "CityLink Transfers Ltd"
    And the HTML contains "CLT-70004-HRW"

  # ============================================================================
  # US-008: Store Vouchers and Return Access URLs
  # Sprint 3 - Output Generation
  # ============================================================================

  @us-008 @skip
  Scenario: Store voucher at predictable path
    # The booking service can predict where vouchers are stored based on
    # booking_id and service_date, useful for support retrieval.
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-80001       |
      | service_date | 2024-03-15          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the PDF is stored at path containing "BK-2024-80001/2024-03-15"
    And the HTML is stored at path containing "BK-2024-80001/2024-03-15"

  @us-008 @skip
  Scenario: Returned URLs are accessible
    # The URLs returned in the response must actually work when accessed.
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-80002       |
      | service_date | 2024-03-16          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the PDF URL returns status 200
    And the PDF URL returns content type "application/pdf"
    And the HTML URL returns status 200
    And the HTML URL returns content type "text/html"

  @us-008 @skip
  Scenario: Response includes both PDF and HTML URLs
    # Every successful voucher generation returns URLs for both formats.
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-80003       |
      | service_date | 2024-03-17          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the response contains "urls.pdf"
    And the response contains "urls.html"

  @us-008 @skip
  Scenario: Storage unavailable returns 503 with retry guidance
    # When storage is down, the API returns 503 with Retry-After header so the booking service knows when to retry.
    Given the storage service is unavailable
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-80004       |
      | service_date | 2024-03-18          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the response status is 503 Service Unavailable
    And the error code is "STORAGE_UNAVAILABLE"
    And the response includes "Retry-After" header
