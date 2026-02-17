# ADR-001: Hexagonal Architecture

## Status

Accepted

## Context

The voucher generation system requires:
- Clear separation between business logic and infrastructure
- Testability without external dependencies
- Flexibility to swap storage backends (filesystem vs S3)
- Flexibility to swap document renderers if needed

Architecture style must support these requirements while remaining simple for a small team.

## Decision

Adopt Hexagonal Architecture (Ports and Adapters) with three layers:
1. **Domain**: Pure business logic, no dependencies
2. **Application**: Use cases orchestrating domain and ports
3. **Adapters**: Infrastructure implementations (REST API, filesystem, LibreOffice)

Define explicit ports:
- `TemplateRepository` (driven port)
- `VoucherStorage` (driven port)
- `DocumentRenderer` (driven port)

## Alternatives Considered

### 1. Simple Layered Architecture (N-tier)
- **Pros**: Familiar, less ceremony
- **Cons**: Business logic tends to leak into controllers; harder to test without mocking HTTP layer
- **Rejected**: Insufficient isolation for this document-processing domain

### 2. Clean Architecture (Uncle Bob)
- **Pros**: Similar benefits to hexagonal
- **Cons**: More layers (entities, use cases, interface adapters, frameworks); over-engineered for single-API system
- **Rejected**: Hexagonal achieves same goals with fewer layers

### 3. No Explicit Architecture (Scripts)
- **Pros**: Fast initial development
- **Cons**: Quickly becomes unmaintainable; testing requires real LibreOffice
- **Rejected**: Cannot meet testability and maintainability requirements

## Consequences

### Positive
- Domain logic testable in isolation (no I/O mocking needed)
- Storage adapter swappable without domain changes
- Clear dependency direction (outside -> inside)
- Ports provide explicit contracts for testing

### Negative
- More files than flat structure
- Indirection may seem like overkill initially
- Team must understand port/adapter pattern

### Mitigations
- Document dependency rules clearly
- Use linting to enforce import rules
- Start with minimal adapters, add as needed

## References

- Alistair Cockburn, "Hexagonal Architecture" (2005)
- "Ports and Adapters" pattern

## Decision Date

2026-02-17

## Decision Makers

Morgan (Solution Architect)
