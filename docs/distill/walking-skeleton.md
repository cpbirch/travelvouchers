# Walking Skeleton: Voucher Generation System

## Purpose

The walking skeleton is the first deliverable that proves the architecture works end-to-end. It is a minimal, fully functional slice through all architectural layers that delivers observable user value.

---

## Walking Skeleton Definition

### User Goal
> "As a booking service, I can generate a voucher for a customer so they receive confirmation of their service booking."

### Observable Outcome
A customer (James Morrison) receives a PDF voucher containing their name, accessible via a URL.

### Scope

| Component | Walking Skeleton Implementation |
|-----------|--------------------------------|
| REST API | POST /vouchers (single endpoint) |
| Validation | Minimal (required fields only) |
| Template | Hardcoded skeleton-template |
| Merge | Single placeholder: `{{customer.last_name}}` |
| PDF Render | LibreOffice headless (simplest output) |
| HTML Render | Deferred (not in skeleton) |
| Storage | Local filesystem |
| Idempotency | Deferred (not in skeleton) |

---

## Acceptance Scenarios

### Scenario 1: Generate minimal voucher end-to-end (Critical)

```gherkin
@walking-skeleton @critical @us-001
Scenario: Generate minimal voucher end-to-end
  Given the skeleton template exists with placeholder "{{customer.last_name}}"
  And the storage service is available
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
```

**What This Proves**:
1. REST adapter accepts HTTP requests and routes to use case
2. Template repository loads template from storage
3. Domain service merges data into template
4. Document renderer converts to PDF
5. Storage adapter persists the file
6. Response includes accessible URL

### Scenario 2: Optional field handling

```gherkin
@walking-skeleton @us-001
Scenario: Walking skeleton handles missing optional fields
  Given the skeleton template exists
  When I request a voucher without customer.title
  Then the voucher is created successfully
  And no error is returned
```

**What This Proves**:
- Optional field omission does not break the flow
- Domain correctly handles missing optional data

### Scenario 3: Response contract

```gherkin
@walking-skeleton @us-001
Scenario: Walking skeleton verifies response structure
  When I request a voucher with valid data
  Then the response contains:
    | field        | present |
    | voucher_id   | yes     |
    | booking_id   | yes     |
    | service_date | yes     |
    | template_id  | yes     |
    | generated_at | yes     |
    | urls.pdf     | yes     |
```

**What This Proves**:
- API contract is correct for downstream consumers
- All required response fields are populated

---

## Architecture Validation

The walking skeleton proves these architectural decisions work:

### Hexagonal Architecture
```
[Booking Service]
       |
       | POST /vouchers
       v
+------+------+
| REST Adapter|  <-- Primary/Driving Adapter
+------+------+
       |
       v
+------+------+
| Use Case    |  <-- Application Layer
+------+------+
       |
       v
+------+------+
| Domain      |  <-- Domain Layer (Template.merge())
+------+------+
       |
       +----------+----------+
       |          |          |
       v          v          v
  Template   Renderer   Storage
   Repo      (LibreOffice) Adapter
   (Port)     (Port)       (Port)
```

### Layer Dependencies Validated
- REST Adapter depends only on Use Case (correct)
- Use Case depends on Domain and Ports (correct)
- Domain depends on nothing external (correct)
- Adapters implement Ports (correct)

---

## What is NOT in the Walking Skeleton

These features are explicitly deferred:

| Feature | Deferred To | Reason |
|---------|-------------|--------|
| HTML output | US-007 (Sprint 3) | Not needed to prove architecture |
| Idempotency | US-009 (Sprint 4) | Adds complexity without proving integration |
| Full validation | US-010 (Sprint 1, after skeleton) | Skeleton needs minimal validation only |
| Template registry | US-002 (Sprint 2) | Hardcoded template is sufficient |
| Multiple placeholders | US-004, US-005 (Sprint 2) | One placeholder proves the pattern |

---

## Implementation Checklist

### Infrastructure
- [ ] FastAPI application created
- [ ] uvicorn server running
- [ ] Template directory mounted
- [ ] Storage directory mounted
- [ ] LibreOffice headless available

### Code
- [ ] POST /vouchers endpoint implemented
- [ ] GenerateVoucherUseCase created
- [ ] Voucher domain entity created
- [ ] Template entity with merge() method
- [ ] TemplateRepository port and filesystem adapter
- [ ] DocumentRenderer port and LibreOffice adapter
- [ ] VoucherStorage port and filesystem adapter

### Tests
- [ ] Walking skeleton scenarios pass
- [ ] PDF URL is accessible
- [ ] PDF contains merged data

---

## Definition of Done

The walking skeleton is complete when:

1. **Demonstrable to stakeholders**: A product owner can see:
   - Send request with customer name "Morrison"
   - Receive PDF URL in response
   - Open PDF and see "Morrison" in the document

2. **All architectural layers exercised**: Every layer in the hexagon is called

3. **Acceptance tests pass**: All 3 walking skeleton scenarios are green

4. **No mocks in production path**: Real filesystem, real LibreOffice (mocks only in tests)

---

## Stakeholder Demo Script

1. "I'm going to generate a voucher for James Morrison's airport transfer."
2. [Show POST request in terminal/Postman]
3. "The system returns a 201 with a PDF URL."
4. [Click PDF URL]
5. "Here's the voucher with Morrison's name."
6. "This proves our architecture works end-to-end."

---

## Next Steps After Walking Skeleton

Once the walking skeleton passes:

1. **Sprint 1 continues**: Implement US-010 (Request Validation)
2. **Sprint 2 begins**: US-002 (Load Templates), US-004/005 (Merging)
3. **Acceptance tests enabled one at a time**: Remove @skip, implement, commit
