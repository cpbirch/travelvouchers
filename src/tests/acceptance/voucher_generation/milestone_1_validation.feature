@milestone-1 @validation
Feature: Request Validation
  As a booking service developer
  I want clear validation errors when my requests are invalid
  So that I can fix integration issues quickly

  Background:
    Given the airport transfer template exists
    And the storage service is available

  # ============================================================================
  # US-010: Validate Request Data Before Processing
  # Sprint 1 - Foundation
  # ============================================================================

  @us-010
  Scenario: All validation errors returned at once
    # When multiple fields are invalid, the API returns all errors in a single
    # response so the developer can fix them all at once rather than playing
    # whack-a-mole with sequential requests.
    When I request a voucher with multiple validation errors:
      | field              | issue          |
      | customer.last_name | missing        |
      | service_date       | invalid format |
    Then the response status is 400 Bad Request
    And the error response contains 2 validation errors
    And error for "customer.last_name" has code "REQUIRED_FIELD_MISSING"
    And error for "service_date" has code "INVALID_DATE_FORMAT"

  @us-010
  Scenario: Missing customer last name rejected
    # Customer last_name is a required field. Requests without it must fail
    # validation before any processing begins.
    When I request a voucher for:
      | field        | value                |
      | template_id  | airport-transfer-v2  |
      | booking_id   | BK-2024-10001        |
      | service_date | 2024-03-01           |
    And customer "James" without last name
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the response status is 400 Bad Request
    And the error code is "VALIDATION_FAILED"
    And the error details include field "customer.last_name"

  @us-010
  Scenario: Missing customer first name rejected
    # Customer first_name is a required field.
    When I request a voucher for:
      | field        | value                |
      | template_id  | airport-transfer-v2  |
      | booking_id   | BK-2024-10002        |
      | service_date | 2024-03-02           |
    And customer without first name "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the response status is 400 Bad Request
    And the error details include field "customer.first_name"

  @us-010
  Scenario: Missing service name rejected
    # Service name is a required field.
    When I request a voucher for:
      | field        | value                |
      | template_id  | airport-transfer-v2  |
      | booking_id   | BK-2024-10003        |
      | service_date | 2024-03-03           |
    And customer "James" "Morrison"
    And service without name provided by "CityLink Transfers"
    Then the response status is 400 Bad Request
    And the error details include field "service.name"

  @us-010
  Scenario: Missing service provider rejected
    # Service provider is a required field.
    When I request a voucher for:
      | field        | value                |
      | template_id  | airport-transfer-v2  |
      | booking_id   | BK-2024-10004        |
      | service_date | 2024-03-04           |
    And customer "James" "Morrison"
    And service "Airport Transfer" without provider
    Then the response status is 400 Bad Request
    And the error details include field "service.provider"

  @us-010
  Scenario: Invalid date format DD-MM-YYYY rejected
    # The service_date must be in ISO 8601 format (YYYY-MM-DD).
    # European date format DD-MM-YYYY must be rejected with a helpful message.
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-10005       |
      | service_date | 15-03-2024          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the response status is 400 Bad Request
    And the error code is "VALIDATION_FAILED"
    And error for "service_date" has code "INVALID_DATE_FORMAT"
    And the error message mentions "ISO 8601"

  @us-010
  Scenario: Invalid date format MM/DD/YYYY rejected
    # US date format MM/DD/YYYY must also be rejected.
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-10006       |
      | service_date | 03/15/2024          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the response status is 400 Bad Request
    And error for "service_date" has code "INVALID_DATE_FORMAT"

  @us-010
  Scenario: Missing template_id rejected
    # The template_id field is required in every request.
    When I request a voucher without template_id for:
      | field        | value         |
      | booking_id   | BK-2024-10007 |
      | service_date | 2024-03-07    |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the response status is 400 Bad Request
    And the error details include field "template_id"

  @us-010
  Scenario: Missing booking_id rejected
    # The booking_id field is required in every request.
    When I request a voucher without booking_id for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | service_date | 2024-03-08          |
    And customer "James" "Morrison"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the response status is 400 Bad Request
    And the error details include field "booking_id"

  @us-010
  Scenario: Empty request body rejected
    # A completely empty request should return all required field errors.
    When I send an empty voucher request
    Then the response status is 400 Bad Request
    And the error response contains validation errors for required fields
