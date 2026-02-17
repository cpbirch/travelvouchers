# Test Scenarios: Voucher Generation System

## Overview

This document catalogs all acceptance test scenarios organized by user story and milestone. Each scenario follows the Given-When-Then pattern and tests through the REST API driving port.

---

## Scenario Summary

| Milestone | User Story | Scenario Count | Error Path % |
|-----------|------------|----------------|--------------|
| Walking Skeleton | US-001 | 3 | 0% |
| Milestone 1 | US-010 | 10 | 100% |
| Milestone 2 | US-002, US-004, US-005 | 12 | 17% |
| Milestone 3 | US-006, US-007, US-008 | 13 | 8% |
| Milestone 4 | US-003, US-009, US-011 | 14 | 43% |
| **Total** | 11 stories | **52** | **40%** |

Error path coverage target: 40% (achieved)

---

## Walking Skeleton Scenarios (US-001)

**File**: `walking_skeleton.feature`
**Tags**: `@walking-skeleton`, `@critical`
**Skip Status**: None (these run first)

| # | Scenario | Purpose |
|---|----------|---------|
| 1 | Generate minimal voucher end-to-end | Validates all architectural layers work |
| 2 | Walking skeleton handles missing optional fields | Validates optional field handling |
| 3 | Walking skeleton verifies response structure | Validates response contract |

**Observable Outcomes**:
- Customer receives voucher with their name
- PDF URL is accessible and contains merged data
- Response includes all required fields for downstream consumers

---

## Milestone 1: Request Validation (US-010)

**File**: `milestone_1_validation.feature`
**Tags**: `@milestone-1`, `@validation`, `@us-010`
**Skip Status**: All scenarios marked `@skip`

| # | Scenario | Type | Error Code |
|---|----------|------|------------|
| 1 | All validation errors returned at once | Error | VALIDATION_FAILED |
| 2 | Missing customer last name rejected | Error | REQUIRED_FIELD_MISSING |
| 3 | Missing customer first name rejected | Error | REQUIRED_FIELD_MISSING |
| 4 | Missing service name rejected | Error | REQUIRED_FIELD_MISSING |
| 5 | Missing service provider rejected | Error | REQUIRED_FIELD_MISSING |
| 6 | Invalid date format DD-MM-YYYY rejected | Error | INVALID_DATE_FORMAT |
| 7 | Invalid date format MM/DD/YYYY rejected | Error | INVALID_DATE_FORMAT |
| 8 | Missing template_id rejected | Error | REQUIRED_FIELD_MISSING |
| 9 | Missing booking_id rejected | Error | REQUIRED_FIELD_MISSING |
| 10 | Empty request body rejected | Error | VALIDATION_FAILED |

**Observable Outcomes**:
- Booking service developer sees all validation errors at once
- Error messages explain expected format (e.g., "ISO 8601")
- Developers can fix integration issues quickly

---

## Milestone 2: Templates and Merging (US-002, US-004, US-005)

**File**: `milestone_2_templates_and_merging.feature`
**Tags**: `@milestone-2`, `@templates`, `@merging`
**Skip Status**: All scenarios marked `@skip`

### Template Loading (US-002)

| # | Scenario | Type |
|---|----------|------|
| 1 | Load Word template successfully | Happy Path |
| 2 | Load LibreOffice template successfully | Happy Path |
| 3 | Template not found returns clear error | Error |

### Customer Data Merging (US-004)

| # | Scenario | Type |
|---|----------|------|
| 4 | Merge complete customer data | Happy Path |
| 5 | Merge customer data with missing optional title | Optional Field |
| 6 | Handle special characters in customer names | Edge Case |
| 7 | Handle accented characters in customer names | Edge Case |

### Service Data Merging (US-005)

| # | Scenario | Type |
|---|----------|------|
| 8 | Merge airport transfer service data | Happy Path |
| 9 | Merge sightseeing tour service data | Happy Path |
| 10 | Handle missing optional service fields | Optional Field |
| 11 | Service data with special notes merged correctly | Edge Case |

**Observable Outcomes**:
- James Morrison's voucher contains "Mr Morrison"
- Elena Rodriguez's tour voucher contains "Westminster Pier"
- Patrick O'Brien's name renders with apostrophe preserved

---

## Milestone 3: Output Generation (US-006, US-007, US-008)

**File**: `milestone_3_output_generation.feature`
**Tags**: `@milestone-3`, `@output`
**Skip Status**: All scenarios marked `@skip`

### PDF Generation (US-006)

| # | Scenario | Type |
|---|----------|------|
| 1 | Generate PDF with preserved formatting | Happy Path |
| 2 | Generated PDF is within size limits | Quality |
| 3 | Generated PDF contains searchable text | Quality |
| 4 | Generated PDF with embedded logo image | Happy Path |
| 5 | Multi-page voucher with terms and conditions | Edge Case |

### HTML Generation (US-007)

| # | Scenario | Type |
|---|----------|------|
| 6 | Generate email-compatible HTML | Happy Path |
| 7 | HTML renders without network dependencies | Quality |
| 8 | Generated HTML is valid HTML5 | Quality |
| 9 | HTML contains all merged content | Happy Path |

### Storage and URLs (US-008)

| # | Scenario | Type |
|---|----------|------|
| 10 | Store voucher at predictable path | Happy Path |
| 11 | Returned URLs are accessible | Happy Path |
| 12 | Response includes both PDF and HTML URLs | Happy Path |
| 13 | Storage unavailable returns 503 with retry guidance | Error |

**Observable Outcomes**:
- Customer can print PDF voucher for service check-in
- Customer can view HTML voucher on mobile device
- Support team can find voucher by booking_id/date path

---

## Milestone 4: Robustness (US-003, US-009, US-011)

**File**: `milestone_4_robustness.feature`
**Tags**: `@milestone-4`, `@robustness`
**Skip Status**: All scenarios marked `@skip`

### Idempotency (US-009)

| # | Scenario | Type |
|---|----------|------|
| 1 | Duplicate request returns existing voucher | Critical |
| 2 | Same booking different dates creates separate vouchers | Happy Path |
| 3 | Different bookings same date creates separate vouchers | Happy Path |
| 4 | Idempotent response preserves all original metadata | Happy Path |

### Template Validation (US-003)

| # | Scenario | Type |
|---|----------|------|
| 5 | Template with unknown placeholder logs warning | Warning |
| 6 | Template with typo in placeholder detected | Error |
| 7 | Template validation passes for all known placeholders | Happy Path |
| 8 | Template validation warns about optional fields | Warning |

### Structured Errors (US-011)

| # | Scenario | Type |
|---|----------|------|
| 9 | Validation error has consistent structure | Error |
| 10 | Template not found error has consistent structure | Error |
| 11 | Storage error includes retry guidance | Error |
| 12 | All error responses include correlation ID | Error |
| 13 | Corrupted template returns 500 with error details | Error |
| 14 | Error message is human-readable | Error |

**Observable Outcomes**:
- Network retry does not create duplicate vouchers
- Marketing team catches placeholder typos before production
- Booking service can handle errors programmatically

---

## Implementation Sequence

### Phase 1: Walking Skeleton (Sprint 1)
1. Enable: `Generate minimal voucher end-to-end`
2. Implement minimal POST /vouchers endpoint
3. Enable: `Walking skeleton handles missing optional fields`
4. Enable: `Walking skeleton verifies response structure`

### Phase 2: Validation (Sprint 1)
5. Enable: `Missing customer last name rejected`
6. Enable: `Missing customer first name rejected`
7. Continue through validation scenarios...

### Phase 3: Templates (Sprint 2)
8. Enable: `Load Word template successfully`
9. Enable: `Template not found returns clear error`
10. Continue through template scenarios...

### Phase 4: Merging (Sprint 2)
11. Enable: `Merge complete customer data`
12. Continue through merging scenarios...

### Phase 5: Output (Sprint 3)
13. Enable: `Generate PDF with preserved formatting`
14. Enable: `Generate email-compatible HTML`
15. Continue through output scenarios...

### Phase 6: Robustness (Sprint 4)
16. Enable: `Duplicate request returns existing voucher`
17. Continue through robustness scenarios...

---

## Driving Port Compliance

All scenarios invoke the system through **POST /vouchers** (REST API adapter).

**Correct Pattern (used)**:
```gherkin
When I request a voucher for:
  | field        | value          |
  | template_id  | skeleton-template |
```

**Violation Pattern (avoided)**:
```gherkin
When I call GenerateVoucherUseCase.execute()  # Wrong: internal method
When I insert a Voucher into the database     # Wrong: secondary adapter
```

---

## Domain Examples Used

| Character | Booking | Service Type |
|-----------|---------|--------------|
| James Morrison | BK-2024-78432 | Airport Transfer |
| Elena Rodriguez | BK-2024-92156 | Sightseeing Tour |
| Patrick O'Brien | BK-2024-40003 | Airport Transfer |
| Carlos Rivera | BK-2024-00003 | Structure Test |

These examples from the user stories provide concrete, domain-relevant test data.
