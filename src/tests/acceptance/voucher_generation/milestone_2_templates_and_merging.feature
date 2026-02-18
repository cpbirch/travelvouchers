@milestone-2 @templates @merging
Feature: Template Loading and Data Merging
  As a booking service
  I want to use marketing-created templates and merge customer/service data
  So that vouchers are professionally branded and personalized

  Background:
    Given the storage service is available

  # ============================================================================
  # US-002: Load and Parse Word/LibreOffice Templates
  # Sprint 2 - Core Flow
  # ============================================================================

  @us-002
  # The system loads .docx files created by marketing in Microsoft Word.
  # James Morrison is booking an airport transfer using the standard template.
  Scenario: Load Word template successfully
    Given the template "airport-transfer-v2" exists as a Word document
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-20001       |
      | service_date | 2024-03-15          |
    And customer "James" "Morrison" with title "Mr"
    And service "Airport Transfer - Heathrow to Central" provided by "CityLink Transfers Ltd"
    Then the voucher is created successfully
    And the PDF preserves the template formatting

  @us-002
  # The system also supports .odt files created in LibreOffice.
  # Elena Rodriguez is booking a sightseeing tour using the Barcelona office template.
  Scenario: Load LibreOffice template successfully
    Given the template "sightseeing-tour-v1" exists as a LibreOffice document
    When I request a voucher for:
      | field        | value               |
      | template_id  | sightseeing-tour-v1 |
      | booking_id   | BK-2024-20002       |
      | service_date | 2024-04-20          |
    And customer "Elena" "Rodriguez" with title "Ms"
    And service "London Eye and Thames Cruise" provided by "City Sightseeing London"
    Then the voucher is created successfully

  @us-002
  # When a booking service requests a non-existent template,
  # they receive a clear 404 error with the template name.
  Scenario: Template not found returns clear error
    Given the template "old-template-2019" does not exist
    When I request a voucher for:
      | field        | value            |
      | template_id  | old-template-2019|
      | booking_id   | BK-2024-20003    |
      | service_date | 2024-03-20       |
    And customer "James" "Morrison"
    And service "Test Service" provided by "Test Provider"
    Then the response status is 404 Not Found
    And the error code is "TEMPLATE_NOT_FOUND"
    And the error message contains "old-template-2019"

  # ============================================================================
  # US-004: Merge Customer Data into Template
  # Sprint 2 - Core Flow
  # ============================================================================

  @us-004 @skip
  # James Morrison's full customer profile is merged into the template.
  # All customer placeholders are replaced with his data.
  Scenario: Merge complete customer data
    Given the template with customer placeholders exists
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-40001       |
      | service_date | 2024-03-15          |
    And customer "James" "Morrison" with:
      | field | value                |
      | title | Mr                   |
      | email | j.morrison@email.com |
      | phone | +44 7700 900123      |
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the PDF contains "Mr Morrison"
    And the PDF contains "James"

  @us-004 @skip
  # Elena Rodriguez only provided required fields (no title).
  # The voucher generates successfully with title rendered as empty.
  Scenario: Merge customer data with missing optional title
    Given the template with "Dear {{customer.title}} {{customer.last_name}}" exists
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-40002       |
      | service_date | 2024-03-16          |
    And customer "Elena" "Rodriguez" without title
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the PDF contains "Rodriguez"

  @us-004 @skip
  # Patrick O'Brien has an apostrophe in his last name.
  # The system must handle special characters correctly in both PDF and HTML.
  Scenario: Handle special characters in customer names
    Given the template with customer name placeholders exists
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-40003       |
      | service_date | 2024-03-17          |
    And customer "Patrick" "O'Brien"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the PDF contains "O'Brien"

  @us-004 @skip
  # Hans Muller (with umlaut) books a voucher.
  # International characters must render correctly.
  Scenario: Handle accented characters in customer names
    Given the template with customer name placeholders exists
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-40004       |
      | service_date | 2024-03-18          |
    And customer "Hans" "Mueller"
    And service "Airport Transfer" provided by "CityLink Transfers"
    Then the voucher is created successfully
    And the PDF contains "Mueller"

  # ============================================================================
  # US-005: Merge Service Data into Template
  # Sprint 2 - Core Flow
  # ============================================================================

  @us-005 @skip
  # James Morrison's airport transfer includes pickup/dropoff details.
  # All transfer-specific fields merge into the template.
  Scenario: Merge airport transfer service data
    Given the template "airport-transfer-v2" exists with service placeholders
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-50001       |
      | service_date | 2024-03-15          |
    And customer "James" "Morrison"
    And service details:
      | field             | value                              |
      | name              | Airport Transfer - Heathrow        |
      | provider          | CityLink Transfers Ltd             |
      | pickup_time       | 14:30                              |
      | pickup_location   | Heathrow Terminal 5, Arrivals Hall |
      | dropoff_location  | Marriott Hotel, Grosvenor Square   |
      | passengers        | 2                                  |
      | confirmation_code | CLT-78432-HRW                      |
    Then the voucher is created successfully
    And the PDF contains "14:30"
    And the PDF contains "Heathrow Terminal 5"
    And the PDF contains "Marriott Hotel"
    And the PDF contains "CLT-78432-HRW"

  @us-005 @skip
  # Elena Rodriguez's tour voucher uses different fields (meeting_point, tour_time).
  # The same merge logic handles different service types.
  Scenario: Merge sightseeing tour service data
    Given the template "sightseeing-tour-v1" exists with tour placeholders
    When I request a voucher for:
      | field        | value               |
      | template_id  | sightseeing-tour-v1 |
      | booking_id   | BK-2024-50002       |
      | service_date | 2024-04-20          |
    And customer "Elena" "Rodriguez"
    And service details:
      | field             | value                        |
      | name              | London Eye and Thames Cruise |
      | provider          | City Sightseeing London      |
      | tour_time         | 10:00                        |
      | meeting_point     | Westminster Pier             |
      | duration          | 3 hours                      |
      | confirmation_code | CSL-92156-LON                |
    Then the voucher is created successfully
    And the PDF contains "Westminster Pier"
    And the PDF contains "10:00"

  @us-005 @skip
  # A minimal service booking with only required fields (name, provider).
  # Optional fields render as empty without errors.
  Scenario: Handle missing optional service fields
    Given the template with optional service placeholders exists
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-50003       |
      | service_date | 2024-03-20          |
    And customer "James" "Morrison"
    And service "Basic Transfer" provided by "Budget Transfers"
    Then the voucher is created successfully

  @us-005 @skip
  # The notes field can contain special requirements like accessibility needs.
  Scenario: Service data with special notes merged correctly
    Given the template with service notes placeholder exists
    When I request a voucher for:
      | field        | value               |
      | template_id  | airport-transfer-v2 |
      | booking_id   | BK-2024-50004       |
      | service_date | 2024-03-21          |
    And customer "James" "Morrison"
    And service details:
      | field    | value                        |
      | name     | Airport Transfer             |
      | provider | CityLink Transfers           |
      | notes    | Wheelchair accessible vehicle required |
    Then the voucher is created successfully
    And the PDF contains "Wheelchair accessible"
