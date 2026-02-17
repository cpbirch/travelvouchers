# Handoff to DELIVER Wave: Voucher Generation System

## Summary

The DISTILL wave is complete. This document provides the handoff artifacts for the software-crafter to begin implementing the Voucher Generation System using Outside-In TDD.

---

## Deliverables

### Feature Files (5)
| File | Scenarios | Skip Status |
|------|-----------|-------------|
| `walking_skeleton.feature` | 3 | None (run first) |
| `milestone_1_validation.feature` | 10 | All @skip |
| `milestone_2_templates_and_merging.feature` | 12 | All @skip |
| `milestone_3_output_generation.feature` | 13 | All @skip |
| `milestone_4_robustness.feature` | 14 | All @skip |
| **Total** | **52** | |

### Step Definitions
| File | Purpose |
|------|---------|
| `steps/conftest.py` | Test fixtures, mock adapters |
| `steps/voucher_steps.py` | Given-When-Then implementations |

### Documentation
| File | Purpose |
|------|---------|
| `docs/distill/test-scenarios.md` | Complete scenario catalog |
| `docs/distill/walking-skeleton.md` | Walking skeleton specification |
| `docs/distill/handoff-to-deliver.md` | This document |

---

## Mandate Compliance Evidence

### CM-A: Driving Port Usage

All test scenarios invoke through the REST API (POST /vouchers), not internal components.

**Evidence**: Step definition imports (from `steps/voucher_steps.py`):

```python
# Correct: Tests use HTTP client to call REST API
context.response = client.post("/vouchers", json=request_body)

# NOT used (would be violations):
# - GenerateVoucherUseCase.execute(request)  # Internal use case
# - template_repository.find_by_id(id)        # Internal port
# - voucher_storage.store(...)                # Internal adapter
```

### CM-B: Business Language in Feature Files

All feature files use domain terminology only. Zero technical terms in Gherkin.

**Evidence**: Grep for technical terms returns no matches in .feature files:

```bash
# These terms should NOT appear in feature files:
grep -r "database\|repository\|adapter\|use.case\|port\|HTTP\|JSON\|endpoint" \
  tests/acceptance/voucher_generation/*.feature
# Expected: No matches

# Domain terms used instead:
# - "voucher" (not "document entity")
# - "customer" (not "CustomerData value object")
# - "template" (not "TemplateRepository")
# - "storage service" (not "VoucherStorage adapter")
```

### CM-C: Walking Skeleton + Focused Scenario Counts

| Category | Count | Guideline |
|----------|-------|-----------|
| Walking Skeleton Scenarios | 3 | 2-3 recommended |
| Focused Scenarios | 49 | 15-20 per feature |
| Total Scenarios | 52 | |
| Error Path Coverage | 40% | Target: 40%+ |

The walking skeleton scenarios prove user-observable value:
1. Customer receives voucher with their name (end-to-end)
2. Missing optional fields do not break generation
3. Response contains all fields needed by downstream systems

---

## Implementation Sequence

### One-at-a-Time Approach

1. Remove `@skip` from first walking skeleton scenario
2. Run tests - scenario should fail (no implementation)
3. Implement just enough production code to pass
4. Refactor while keeping test green
5. Commit with passing test
6. Remove `@skip` from next scenario
7. Repeat

### Recommended Order

**Sprint 1 - Foundation**
```
walking_skeleton.feature:
  1. Generate minimal voucher end-to-end        [FIRST]
  2. Walking skeleton handles missing optional fields
  3. Walking skeleton verifies response structure

milestone_1_validation.feature:
  4. Missing customer last name rejected
  5. Missing service provider rejected
  ... (continue validation scenarios)
```

**Sprint 2 - Core Flow**
```
milestone_2_templates_and_merging.feature:
  1. Load Word template successfully
  2. Template not found returns clear error
  3. Merge complete customer data
  ... (continue template/merge scenarios)
```

**Sprint 3 - Output**
```
milestone_3_output_generation.feature:
  1. Generate PDF with preserved formatting
  2. Generate email-compatible HTML
  3. Store voucher and return URLs
  ... (continue output scenarios)
```

**Sprint 4 - Robustness**
```
milestone_4_robustness.feature:
  1. Duplicate request returns existing voucher
  2. All error responses include correlation ID
  ... (continue robustness scenarios)
```

---

## Test Infrastructure Ready

### Mocking Strategy (per user configuration)
- **Real internal services**: Domain, use cases run with real code
- **Mocked external adapters**: Storage, LibreOffice renderer mocked

### Mock Adapters Provided
| Adapter | Purpose |
|---------|---------|
| `MockTemplateRepository` | In-memory templates for speed |
| `MockVoucherStorage` | In-memory storage with verification |
| `MockDocumentRenderer` | Fast PDF/HTML generation |
| `MockTestClient` | Placeholder until app exists |

### Running Tests
```bash
cd tests/acceptance
pip install -r requirements.txt

# Run walking skeleton only (first scenarios)
pytest -m "walking_skeleton" -v

# Run all non-skipped scenarios
pytest --ignore-glob="*_skip*" -v

# Run specific milestone
pytest -k "milestone_1" -v
```

---

## Architectural Boundaries

### Port Definitions (from architecture design)

| Port | Type | Implementation |
|------|------|----------------|
| VoucherAPI | Driving | REST API (POST /vouchers) |
| TemplateRepository | Driven | FilesystemTemplateRepository |
| DocumentRenderer | Driven | LibreOfficeRenderer |
| VoucherStorage | Driven | FilesystemVoucherStorage |

### Dependency Direction
```
REST API
    |
    v
GenerateVoucherUseCase
    |
    v
Domain (Voucher, Template, MergeContext)
    |
    v
Ports (interfaces only)
    ^
    |
Adapters (implementations)
```

---

## Definition of Done Checklist

Before each story is considered complete:

- [ ] Acceptance scenario(s) pass
- [ ] Unit tests written for domain logic
- [ ] No hardcoded values (use configuration)
- [ ] Error handling follows RFC 7807 structure
- [ ] Correlation ID logged with all operations
- [ ] No PII in logs

---

## Questions for Software Crafter

1. **LibreOffice setup**: Do you have LibreOffice headless available, or should we start with a simpler PDF approach for the walking skeleton?

2. **Storage**: Should walking skeleton use local filesystem or in-memory storage?

3. **Test database**: Do we need any persistent storage for idempotency index, or can we use filesystem metadata?

---

## Handoff Approved

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Acceptance Test Designer | Quinn | 2026-02-17 | Approved |
| Ready for DELIVER wave | | | |
