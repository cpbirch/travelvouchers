# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the Voucher Generation System.

## Index

| ADR | Title | Status | Summary |
|-----|-------|--------|---------|
| [ADR-001](ADR-001-hexagonal-architecture.md) | Hexagonal Architecture | Accepted | Ports and adapters pattern for domain isolation |
| [ADR-002](ADR-002-python-fastapi.md) | Python with FastAPI | Accepted | Language and framework selection |
| [ADR-003](ADR-003-libreoffice-rendering.md) | LibreOffice Rendering | Accepted | PDF/HTML generation via LibreOffice headless |
| [ADR-004](ADR-004-file-based-idempotency.md) | File-Based Idempotency | Accepted | Storage path existence for duplicate detection |
| [ADR-005](ADR-005-document-processing-libraries.md) | Document Processing Libraries | Accepted | python-docx and odfpy for template manipulation |

## ADR Template

New ADRs should follow this structure:

```markdown
# ADR-NNN: Title

## Status
[Proposed | Accepted | Deprecated | Superseded by ADR-XXX]

## Context
[What is the issue we are addressing?]

## Decision
[What is our solution?]

## Alternatives Considered
[What other options did we evaluate?]

## Consequences
[What are the positive and negative results?]

## Decision Date
[YYYY-MM-DD]

## Decision Makers
[Who made this decision?]
```

## ADR Process

1. Create new ADR in `docs/adrs/` with next sequential number
2. Status starts as "Proposed"
3. Review with team
4. Update status to "Accepted" when approved
5. Update this README index
