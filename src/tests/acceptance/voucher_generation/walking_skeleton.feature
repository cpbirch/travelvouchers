@walking-skeleton
Feature: Walking Skeleton - Minimal Voucher Generation
  As a development team
  I want to generate a minimal voucher end-to-end
  So that I can validate the architecture works before building full features

  Background:
    Given the skeleton template exists with placeholder "{{customer.last_name}}"
    And the storage service is available

  # ============================================================================
  # WALKING SKELETON - These scenarios run first to validate architecture
  # No @skip tags - these must pass before any other development proceeds
  # ============================================================================

  @critical @us-001
  Scenario: Generate minimal voucher end-to-end
    """
    This is the primary walking skeleton scenario that proves:
    1. API accepts requests (REST adapter works)
    2. Template loads (template repository works)
    3. Data merges (domain logic works)
    4. PDF generates (document renderer works)
    5. Storage works (voucher storage works)
    6. URL returned (response formation works)
    """
    When I request a voucher for:
      | field        | value             |
      | template_id  | skeleton-template |
      | booking_id   | BK-2024-00001     |
      | service_date | 2024-01-01        |
    And customer "James" "Morrison"
    And service "Test Service" provided by "Test Provider"
    Then the voucher is created successfully
    And the response contains a PDF URL
    And the PDF contains "Morrison"

  @critical @us-001
  Scenario: Walking skeleton handles missing optional customer fields
    """
    Validates that optional fields (like title) do not break generation.
    The template should render with empty values for missing optional fields.
    """
    When I request a voucher for:
      | field        | value             |
      | template_id  | skeleton-template |
      | booking_id   | BK-2024-00002     |
      | service_date | 2024-01-02        |
    And customer "Elena" "Rodriguez" without title
    And service "Walking Skeleton Test" provided by "Test Provider"
    Then the voucher is created successfully
    And no error is returned

  @critical @us-001
  Scenario: Walking skeleton verifies response structure
    """
    Validates the response contains all required fields for downstream consumers.
    """
    When I request a voucher for:
      | field        | value             |
      | template_id  | skeleton-template |
      | booking_id   | BK-2024-00003     |
      | service_date | 2024-01-03        |
    And customer "Carlos" "Rivera"
    And service "Structure Test" provided by "Test Provider"
    Then the voucher is created successfully
    And the response contains:
      | field        | present |
      | voucher_id   | yes     |
      | booking_id   | yes     |
      | service_date | yes     |
      | template_id  | yes     |
      | generated_at | yes     |
      | urls.pdf     | yes     |
