Feature: Voucher Generation from Templates
  As an internal booking service
  I want to generate vouchers by merging templates with customer and service data
  So that customers receive confirmation documents for their booked services

  Background:
    Given the template "airport-transfer-v2" exists in the template registry
    And the template contains placeholders "{{customer.first_name}}", "{{customer.last_name}}", "{{service.name}}"
    And the storage service is available

  # =============================================================================
  # HAPPY PATH SCENARIOS
  # =============================================================================

  @happy-path @walking-skeleton
  Scenario: Generate voucher for airport transfer booking
    Given the booking service has a confirmed booking "BK-2024-78432"
    And the customer data is:
      | field      | value           |
      | title      | Mr              |
      | first_name | James           |
      | last_name  | Morrison        |
      | email      | j.morrison@email.com |
    And the service data is:
      | field             | value                                    |
      | name              | Airport Transfer - Heathrow to Central   |
      | provider          | CityLink Transfers Ltd                   |
      | pickup_time       | 14:30                                    |
      | pickup_location   | Heathrow Terminal 5, Arrivals Hall       |
      | dropoff_location  | Marriott Hotel, Grosvenor Square         |
      | passengers        | 2                                        |
      | confirmation_code | CLT-78432-HRW                            |
    When the booking service requests a voucher with:
      | field        | value                |
      | template_id  | airport-transfer-v2  |
      | booking_id   | BK-2024-78432        |
      | service_date | 2024-03-15           |
    Then the response status is 201 Created
    And the response contains a voucher_id matching pattern "V-2024-78432-*"
    And the response contains a pdf_url pointing to stored PDF
    And the response contains an html_url pointing to stored HTML
    And the stored PDF contains "Mr Morrison"
    And the stored PDF contains "Airport Transfer - Heathrow to Central"
    And the stored PDF contains "CityLink Transfers Ltd"

  @happy-path
  Scenario: Generate voucher for sightseeing tour booking
    Given the template "sightseeing-tour-v1" exists in the template registry
    And the booking service has a confirmed booking "BK-2024-92156"
    And the customer data is:
      | field      | value              |
      | title      | Ms                 |
      | first_name | Elena              |
      | last_name  | Rodriguez          |
    And the service data is:
      | field             | value                          |
      | name              | London Eye and Thames Cruise   |
      | provider          | City Sightseeing London        |
      | tour_date         | 2024-04-20                     |
      | tour_time         | 10:00                          |
      | meeting_point     | Westminster Pier               |
      | duration          | 3 hours                        |
      | confirmation_code | CSL-92156-LON                  |
    When the booking service requests a voucher with:
      | field        | value                |
      | template_id  | sightseeing-tour-v1  |
      | booking_id   | BK-2024-92156        |
      | service_date | 2024-04-20           |
    Then the response status is 201 Created
    And the stored PDF contains "Ms Rodriguez"
    And the stored PDF contains "London Eye and Thames Cruise"

  # =============================================================================
  # IDEMPOTENCY SCENARIOS
  # =============================================================================

  @idempotency
  Scenario: Duplicate request returns existing voucher without regeneration
    Given a voucher already exists for booking "BK-2024-78432" and date "2024-03-15"
    And the voucher was generated at "2024-02-17T10:23:45Z"
    When the booking service requests a voucher with:
      | field        | value                |
      | template_id  | airport-transfer-v2  |
      | booking_id   | BK-2024-78432        |
      | service_date | 2024-03-15           |
    Then the response status is 200 OK
    And the response contains the same voucher_id as the existing voucher
    And the response contains the original generated_at timestamp "2024-02-17T10:23:45Z"
    And no new voucher files are created in storage

  @idempotency
  Scenario: Same booking with different service date creates new voucher
    Given a voucher already exists for booking "BK-2024-78432" and date "2024-03-15"
    When the booking service requests a voucher with:
      | field        | value                |
      | template_id  | airport-transfer-v2  |
      | booking_id   | BK-2024-78432        |
      | service_date | 2024-03-16           |
    Then the response status is 201 Created
    And the response contains a different voucher_id than the existing voucher

  # =============================================================================
  # VALIDATION ERROR SCENARIOS
  # =============================================================================

  @error-handling @validation
  Scenario: Request with non-existent template returns 404
    Given the template "non-existent-template" does not exist
    When the booking service requests a voucher with:
      | field        | value                  |
      | template_id  | non-existent-template  |
      | booking_id   | BK-2024-99999          |
      | service_date | 2024-05-01             |
    Then the response status is 404 Not Found
    And the error code is "TEMPLATE_NOT_FOUND"
    And the error message contains "non-existent-template"

  @error-handling @validation
  Scenario: Request missing required customer field returns 400
    Given the customer data is missing "last_name"
    When the booking service requests a voucher with valid template and service data
    Then the response status is 400 Bad Request
    And the error code is "VALIDATION_FAILED"
    And the error details include:
      | field              | code                   |
      | customer.last_name | REQUIRED_FIELD_MISSING |

  @error-handling @validation
  Scenario: Request missing required service field returns 400
    Given the service data is missing "name"
    When the booking service requests a voucher with valid template and customer data
    Then the response status is 400 Bad Request
    And the error code is "VALIDATION_FAILED"
    And the error details include:
      | field        | code                   |
      | service.name | REQUIRED_FIELD_MISSING |

  @error-handling @validation
  Scenario: Request with invalid date format returns 400
    When the booking service requests a voucher with:
      | field        | value                |
      | template_id  | airport-transfer-v2  |
      | booking_id   | BK-2024-78432        |
      | service_date | 15-03-2024           |
    Then the response status is 400 Bad Request
    And the error code is "VALIDATION_FAILED"
    And the error details include:
      | field        | code                |
      | service_date | INVALID_DATE_FORMAT |
    And the error message mentions "ISO 8601"

  # =============================================================================
  # TEMPLATE ERROR SCENARIOS
  # =============================================================================

  @error-handling @template
  Scenario: Corrupted template file returns 500
    Given the template "corrupted-template" exists but is corrupted
    When the booking service requests a voucher with:
      | field        | value              |
      | template_id  | corrupted-template |
      | booking_id   | BK-2024-11111      |
      | service_date | 2024-06-01         |
    Then the response status is 500 Internal Server Error
    And the error code is "TEMPLATE_ERROR"
    And the error message indicates a template parsing problem

  @error-handling @template
  Scenario: Template with unresolved placeholder logs warning but succeeds
    Given the template "extra-placeholders" contains placeholder "{{service.special_instructions}}"
    And the service data does not include "special_instructions"
    When the booking service requests a voucher with:
      | field        | value              |
      | template_id  | extra-placeholders |
      | booking_id   | BK-2024-22222      |
      | service_date | 2024-06-15         |
    Then the response status is 201 Created
    And the generated voucher renders "{{service.special_instructions}}" as empty string
    And a warning is logged about unresolved placeholder

  # =============================================================================
  # STORAGE ERROR SCENARIOS
  # =============================================================================

  @error-handling @storage
  Scenario: Storage service unavailable returns 503
    Given the storage service is unavailable
    When the booking service requests a voucher with valid data
    Then the response status is 503 Service Unavailable
    And the error code is "STORAGE_UNAVAILABLE"
    And the response includes "Retry-After" header

  # =============================================================================
  # OUTPUT FORMAT SCENARIOS
  # =============================================================================

  @output
  Scenario: Generated PDF is valid and readable
    When the booking service requests a voucher with valid data
    Then the response status is 201 Created
    And the pdf_url returns a valid PDF document
    And the PDF document is less than 500KB in size
    And the PDF document contains searchable text

  @output
  Scenario: Generated HTML is valid and styled
    When the booking service requests a voucher with valid data
    Then the response status is 201 Created
    And the html_url returns valid HTML5 document
    And the HTML document includes inline CSS for email compatibility
    And the HTML document renders correctly without external resources
