# Definition of Ready Checklist: Voucher Generation System

This document validates each user story against the 8-item Definition of Ready gate.

---

## DoR Criteria

| # | Criterion | Description |
|---|-----------|-------------|
| 1 | Problem statement | Clear problem in domain language |
| 2 | User/persona | Identified with specific characteristics |
| 3 | Domain examples | At least 3 examples with real data |
| 4 | UAT scenarios | Given/When/Then format, 3-7 scenarios |
| 5 | Acceptance criteria | Derived from UAT scenarios |
| 6 | Right-sized | 1-3 days effort, 3-7 scenarios |
| 7 | Technical notes | Constraints and dependencies identified |
| 8 | Dependencies | Resolved or tracked |

---

## Feature 0: Walking Skeleton

### US-001: Minimal End-to-End Voucher Generation

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Problem statement | PASS | "The development team needs to validate that the architectural approach works before building full features" |
| 2 | User/persona | PASS | "Internal development team, greenfield project context, motivation: reduce integration risk" |
| 3 | Domain examples | PASS | 3 examples: simplest happy path (James Morrison), verify integration points (Carlos Rivera), missing optional field |
| 4 | UAT scenarios | PASS | 2 scenarios in Given/When/Then format |
| 5 | Acceptance criteria | PASS | 5 checkable criteria derived from scenarios |
| 6 | Right-sized | PASS | 1-2 days estimate, 2 scenarios |
| 7 | Technical notes | PASS | "Hardcode template, simplest PDF, local storage, no HTML" |
| 8 | Dependencies | PASS | None (first story) |

**Result: READY**

---

## Feature 1: Template Processing

### US-002: Load and Parse Word/LibreOffice Templates

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Problem statement | PASS | "Booking service team needs to use professionally designed templates created by marketing" |
| 2 | User/persona | PASS | "Booking Service, integrating with marketing-created templates" |
| 3 | Domain examples | PASS | 3 examples: airport transfer (Sarah Chen), LibreOffice (Barcelona office), template not found |
| 4 | UAT scenarios | PASS | 3 scenarios covering .docx, .odt, and 404 |
| 5 | Acceptance criteria | PASS | 5 checkable criteria |
| 6 | Right-sized | PASS | 2-3 days estimate, 3 scenarios |
| 7 | Technical notes | PASS | "Template directory configurable, consider caching, placeholder regex" |
| 8 | Dependencies | PASS | Depends on US-001 (tracked) |

**Result: READY**

---

### US-003: Validate Template Placeholders Against Schema

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Problem statement | PASS | "Typos in placeholder names aren't discovered until customer receives voucher with blank fields" |
| 2 | User/persona | PASS | "Marketing team (template creators)" |
| 3 | Domain examples | PASS | 3 examples: valid template (Sarah Chen), typo detection, optional field warning |
| 4 | UAT scenarios | PASS | 3 scenarios |
| 5 | Acceptance criteria | PASS | 4 checkable criteria |
| 6 | Right-sized | PASS | 1-2 days estimate, 3 scenarios |
| 7 | Technical notes | PASS | "Levenshtein distance for suggestions, validation endpoint" |
| 8 | Dependencies | PASS | Depends on US-002 (tracked) |

**Result: READY**

---

## Feature 2: Data Merging

### US-004: Merge Customer Data into Template

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Problem statement | PASS | "Customer data in JSON format, templates expect formatted text, manual copy-paste doesn't scale" |
| 2 | User/persona | PASS | "Booking Service, has customer JSON, needs personalized voucher" |
| 3 | Domain examples | PASS | 3 examples: full data (James Morrison), minimal data (Elena Rodriguez), missing required field |
| 4 | UAT scenarios | PASS | 3 scenarios |
| 5 | Acceptance criteria | PASS | 4 checkable criteria including special character handling |
| 6 | Right-sized | PASS | 1-2 days estimate, 3 scenarios |
| 7 | Technical notes | PASS | "HTML-encode values, consider locale-aware formatting" |
| 8 | Dependencies | PASS | Depends on US-002 (tracked) |

**Result: READY**

---

### US-005: Merge Service Data into Template

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Problem statement | PASS | "Each service type has different data fields, need flexible merge for any service type" |
| 2 | User/persona | PASS | "Booking Service, multiple service types with varying fields" |
| 3 | Domain examples | PASS | 3 examples: airport transfer, sightseeing tour, missing provider |
| 4 | UAT scenarios | PASS | 3 scenarios |
| 5 | Acceptance criteria | PASS | 4 checkable criteria |
| 6 | Right-sized | PASS | 1-2 days estimate, 3 scenarios |
| 7 | Technical notes | PASS | "Schema is extensible, consider time formatting" |
| 8 | Dependencies | PASS | Depends on US-002 (tracked) |

**Result: READY**

---

## Feature 3: Output Generation

### US-006: Generate PDF from Merged Document

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Problem statement | PASS | "Customers need printable vouchers for services requiring physical presentation" |
| 2 | User/persona | PASS | "Holiday customer, needs to print or show voucher at service location" |
| 3 | Domain examples | PASS | 3 examples: transfer voucher (James Morrison), tour with images (Elena Rodriguez), multi-page |
| 4 | UAT scenarios | PASS | 5 scenarios (formatting, size, images, multipage, searchable) |
| 5 | Acceptance criteria | PASS | 5 checkable criteria |
| 6 | Right-sized | PASS | 2-3 days estimate, 5 scenarios |
| 7 | Technical notes | PASS | "LibreOffice headless, consider PDF/A format" |
| 8 | Dependencies | PASS | Depends on US-004, US-005 (tracked) |

**Result: READY**

---

### US-007: Generate HTML from Merged Document

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Problem statement | PASS | "PDFs awkward on mobile, HTML provides better readability" |
| 2 | User/persona | PASS | "Holiday customer, viewing voucher on phone or in email" |
| 3 | Domain examples | PASS | 3 examples: email-ready (James Morrison), mobile-friendly (Elena Rodriguez), offline-capable |
| 4 | UAT scenarios | PASS | 4 scenarios |
| 5 | Acceptance criteria | PASS | 5 checkable criteria |
| 6 | Right-sized | PASS | 2-3 days estimate, 4 scenarios |
| 7 | Technical notes | PASS | "Table-based layout for email, inline styles, base64 images" |
| 8 | Dependencies | PASS | Depends on US-004, US-005 (tracked) |

**Result: READY**

---

## Feature 4: Storage and Retrieval

### US-008: Store Vouchers and Return Access URLs

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Problem statement | PASS | "Generated vouchers need to be accessible later, in-memory generation insufficient" |
| 2 | User/persona | PASS | "Booking Service, Customer, Support team - all need retrieval" |
| 3 | Domain examples | PASS | 3 examples: store and return (James Morrison), support retrieval, storage failure |
| 4 | UAT scenarios | PASS | 3 scenarios |
| 5 | Acceptance criteria | PASS | 5 checkable criteria |
| 6 | Right-sized | PASS | 1-2 days estimate, 3 scenarios |
| 7 | Technical notes | PASS | "Storage backend configurable, consider signed URLs" |
| 8 | Dependencies | PASS | Depends on US-006, US-007 (tracked) |

**Result: READY**

---

### US-009: Idempotent Voucher Generation

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Problem statement | PASS | "Accidental duplicate calls create duplicate storage and confusing multiple URLs" |
| 2 | User/persona | PASS | "Booking Service, distributed system with retry logic" |
| 3 | Domain examples | PASS | 3 examples: duplicate request, same booking different date, different booking same date |
| 4 | UAT scenarios | PASS | 3 scenarios |
| 5 | Acceptance criteria | PASS | 5 checkable criteria |
| 6 | Right-sized | PASS | 1 day estimate, 3 scenarios |
| 7 | Technical notes | PASS | "Store idempotency index, consider database vs storage metadata" |
| 8 | Dependencies | PASS | Depends on US-008 (tracked) |

**Result: READY**

---

## Feature 5: Validation and Errors

### US-010: Validate Request Data Before Processing

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Problem statement | PASS | "Late validation causes confusing errors, early validation with clear messages speeds integration" |
| 2 | User/persona | PASS | "Booking Service developer, integrating with voucher API" |
| 3 | Domain examples | PASS | 3 examples: multiple errors, invalid date, invalid booking ID |
| 4 | UAT scenarios | PASS | 3 scenarios |
| 5 | Acceptance criteria | PASS | 4 checkable criteria |
| 6 | Right-sized | PASS | 1 day estimate, 3 scenarios |
| 7 | Technical notes | PASS | "JSON Schema validation baseline, custom validators for business rules" |
| 8 | Dependencies | PASS | Depends on US-001 (tracked) |

**Result: READY**

---

### US-011: Return Structured Error Responses

| # | Criterion | Status | Evidence |
|---|-----------|--------|----------|
| 1 | Problem statement | PASS | "Unstructured errors force developers to guess, structured errors enable programmatic handling" |
| 2 | User/persona | PASS | "Booking Service developer, building error handling" |
| 3 | Domain examples | PASS | 3 examples: validation error structure, template error structure, storage error with retry |
| 4 | UAT scenarios | PASS | 3 scenarios |
| 5 | Acceptance criteria | PASS | 5 checkable criteria |
| 6 | Right-sized | PASS | 1 day estimate, 3 scenarios |
| 7 | Technical notes | PASS | "Log correlation ID, consider RFC 7807" |
| 8 | Dependencies | PASS | Depends on US-010 (tracked) |

**Result: READY**

---

## Summary

| Story | Problem | Persona | Examples | UAT | AC | Size | Tech Notes | Deps | Result |
|-------|---------|---------|----------|-----|----|----- |------------|------|--------|
| US-001 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | READY |
| US-002 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | READY |
| US-003 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | READY |
| US-004 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | READY |
| US-005 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | READY |
| US-006 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | READY |
| US-007 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | READY |
| US-008 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | READY |
| US-009 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | READY |
| US-010 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | READY |
| US-011 | PASS | PASS | PASS | PASS | PASS | PASS | PASS | PASS | READY |

**All 11 stories pass Definition of Ready and are approved for DESIGN wave handoff.**

---

## Dependency Graph

```
US-001 (Walking Skeleton) ----+
     |                        |
     v                        v
US-002 (Load Templates)    US-010 (Validation)
     |                        |
     +----+----+----+         v
     |    |    |    |    US-011 (Errors)
     v    v    v    v
US-003 US-004 US-005
            |    |
            v    v
      +-----+----+-----+
      |                |
      v                v
   US-006           US-007
   (PDF)            (HTML)
      |                |
      +-------+--------+
              |
              v
           US-008 (Storage)
              |
              v
           US-009 (Idempotency)
```

---

## Handoff Readiness

**DISCUSS wave complete. Ready for DESIGN wave handoff.**

Handoff package:
- Journey artifacts: `docs/ux/voucher-merger/`
- Requirements: `docs/requirements/requirements.md`
- User stories: `docs/requirements/user-stories.md`
- Acceptance criteria: `docs/requirements/acceptance-criteria.md`
- DoR validation: `docs/requirements/dor-checklist.md` (this file)

Next actor: **solution-architect** (DESIGN wave)
