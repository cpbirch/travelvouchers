@milestone-4 @robustness
Feature: Robustness - Idempotency, Validation, and Error Handling
  As a booking service operating in a distributed environment
  I want safe retry behavior and clear error responses
  So that network issues do not create duplicates and I can handle errors programmatically

  Background:
    Given the airport transfer template exists
    And the storage service is available

  # ============================================================================
  # US-009: Idempotent Voucher Generation
  # Sprint 4 - Robustness
  # ============================================================================

  # The booking service retried due to network timeout.
  # The second request should return the original voucher, not create a duplicate.
  @us-009 @critical
  Scenario: Duplicate request returns existing voucher
    Given a voucher was previously generated for:
      | field        | value               |
      | booking_id   | BK-2024-90001       |
      | service_date | 2024-03-15          |
    And the original voucher was created at "2024-02-17T10:23:45Z"
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-90001       |
      | service_date | 2024-03-15          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the response status is 200 OK
    And the response contains the original voucher_id
    And the response contains generated_at "2024-02-17T10:23:45Z"
    And no new files are written to storage

  # James Morrison has a transfer on March 15 and another on March 16.
  # Each date is a separate service, requiring a separate voucher.
  @us-009 @skip
  Scenario: Same booking different dates creates separate vouchers
    Given a voucher exists for booking "BK-2024-90002" date "2024-03-15"
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-90002       |
      | service_date | 2024-03-16          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the response status is 201 Created
    And the voucher_id is different from the existing voucher

  # James Morrison (BK-2024-90003) and Elena Rodriguez (BK-2024-90004)
  # both have transfers on March 15. Each needs their own voucher.
  @us-009 @skip
  Scenario: Different bookings same date creates separate vouchers
    Given a voucher exists for booking "BK-2024-90003" date "2024-03-15"
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-90004       |
      | service_date | 2024-03-15          |
    And customer "Elena" "Rodriguez"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the response status is 201 Created
    And the voucher_id is different from the existing voucher

  # When returning a cached voucher, all metadata from the original
  # generation must be preserved.
  @us-009 @skip
  Scenario: Idempotent response preserves all original metadata
    Given a voucher was previously generated with:
      | field        | value               |
      | booking_id   | BK-2024-90005       |
      | service_date | 2024-03-15          |
      | template_id  | airport-transfer-v2 |
      | voucher_id   | V-2024-90005-0315   |
    When I request a duplicate voucher for booking "BK-2024-90005" date "2024-03-15"
    Then the response status is 200 OK
    And the response contains voucher_id "V-2024-90005-0315"
    And the response contains template_id "airport-transfer-v2"

  # ============================================================================
  # US-003: Validate Template Placeholders Against Schema
  # Sprint 4 - Robustness
  # ============================================================================

  # Marketing created a template with {{customer.nickname}} which is not
  # in the schema. The voucher generates with the placeholder rendered empty,
  # and a warning is logged for operations.
  @us-003 @skip
  Scenario: Template with unknown placeholder logs warning but succeeds
    Given the template "custom-placeholders" contains "Hello {{customer.nickname}}"
    When I request a voucher for:
      | field        | value              |
      | template_id  | custom-placeholders|
      | booking_id   | BK-2024-30001      |
      | service_date | 2024-03-25         |
    And customer "James" "Morrison"
    And service "Test Service" provided by "Test Provider"
    Then the voucher is created successfully
    And a warning is logged about unknown placeholder "customer.nickname"

  # A template contains {{customer.lst_name}} (typo for last_name).
  # The system should detect this and suggest the correct placeholder.
  @us-003 @skip
  Scenario: Template with typo in placeholder detected
    Given the template "typo-template" contains "Dear {{customer.lst_name}}"
    When the template "typo-template" is validated
    Then validation reports unknown placeholder "customer.lst_name"
    And validation suggests "Did you mean: customer.last_name?"

  # A well-formed template with only valid placeholders passes validation.
  @us-003 @skip
  Scenario: Template validation passes for all known placeholders
    Given the template "valid-template" contains only known placeholders:
      | placeholder              |
      | {{customer.first_name}}  |
      | {{customer.last_name}}   |
      | {{service.name}}         |
      | {{service.provider}}     |
    When the template "valid-template" is validated
    Then validation passes with no errors

  # Using {{customer.phone}} is valid but may render empty for customers
  # who did not provide phone numbers. This generates a warning.
  @us-003 @skip
  Scenario: Template validation warns about optional fields
    Given the template "optional-fields" contains "Phone: {{customer.phone}}"
    When the template "optional-fields" is validated
    Then validation passes
    And validation warns "customer.phone is optional and may be empty"

  # ============================================================================
  # US-011: Return Structured Error Responses
  # Sprint 4 - Robustness
  # ============================================================================

  # All validation errors follow the same JSON structure for
  # programmatic handling by the booking service.
  @us-011 @skip
  Scenario: Validation error has consistent structure
    When I request a voucher with missing customer last_name
    Then the response status is 400 Bad Request
    And the error response contains:
      | field          | type   |
      | error          | string |
      | message        | string |
      | correlation_id | string |
      | details        | array  |

  # 404 errors also follow the standard error structure.
  @us-011 @skip
  Scenario: Template not found error has consistent structure
    When I request a voucher with template_id "non-existent"
    Then the response status is 404 Not Found
    And the error response contains:
      | field          | value              |
      | error          | TEMPLATE_NOT_FOUND |
    And the error response contains a correlation_id

  # 503 errors include retry_after so the booking service knows
  # when to retry the request.
  @us-011 @skip
  Scenario: Storage error includes retry guidance
    Given the storage service is temporarily unavailable
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-11001       |
      | service_date | 2024-03-28          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the response status is 503 Service Unavailable
    And the error response contains "retry_after" as integer
    And the response header "Retry-After" is present

  # Every error response includes a correlation_id that support
  # can use to find related log entries.
  @us-011 @skip
  Scenario: All error responses include correlation ID
    When I request a voucher with invalid data
    Then the error response contains a correlation_id
    And the correlation_id is logged with the error

  # If a template file is corrupted (invalid DOCX/ODT), the error
  # response identifies it as a template problem.
  @us-011 @skip
  Scenario: Corrupted template returns 500 with error details
    Given the template "corrupted-template" exists but is corrupted
    When I request a voucher for:
      | field        | value              |
      | template_id  | corrupted-template |
      | booking_id   | BK-2024-11002      |
      | service_date | 2024-03-29         |
    And customer "James" "Morrison"
    And service "Test Service" provided by "Test Provider"
    Then the response status is 500 Internal Server Error
    And the error code is "TEMPLATE_ERROR"
    And the error response contains a correlation_id

  # Error messages should be understandable by developers without
  # looking up error codes.
  @us-011 @skip
  Scenario: Error message is human-readable
    When I request a voucher with service_date "invalid-date"
    Then the response status is 400 Bad Request
    And the error message is human-readable
    And the error message explains what was wrong
