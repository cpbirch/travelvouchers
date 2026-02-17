# Design Documentation: Voucher Generation System

## Overview

This directory contains the technical architecture and design documentation for the Voucher Generation System (Template Merger).

## Documents

| Document | Purpose |
|----------|---------|
| [architecture-design.md](architecture-design.md) | System context, C4 diagrams, hexagonal structure |
| [technology-stack.md](technology-stack.md) | Technology choices with rationale |
| [component-boundaries.md](component-boundaries.md) | Port/adapter definitions, package structure |
| [data-models.md](data-models.md) | Domain entities, value objects, DTOs |

## Architecture Summary

### Style
Hexagonal Architecture (Ports and Adapters) as a single deployable monolith.

### Technology Stack
- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Document Processing**: python-docx, odfpy
- **Rendering**: LibreOffice headless
- **Storage**: Filesystem (S3-compatible)

### Key Components

```
Primary Adapter:     REST API (FastAPI)
                          |
                          v
Application:         GenerateVoucherUseCase
                          |
          +---------------+---------------+
          |               |               |
          v               v               v
Ports:    TemplateRepo    Renderer        Storage
          |               |               |
          v               v               v
Adapters: Filesystem      LibreOffice     Filesystem/S3
```

### Quality Attributes

| Attribute | Target |
|-----------|--------|
| Latency | P95 < 2 seconds |
| Throughput | 10 req/s |
| Reliability | 99.9% success |
| Idempotency | 100% |

## ADRs

Architecture Decision Records are in [../adrs/](../adrs/README.md).

## Walking Skeleton (US-001)

The first story implements a minimal end-to-end flow:
- Single hardcoded template
- PDF output only (no HTML)
- Local filesystem storage
- No idempotency check

This validates the architecture before building full features.

## Handoff

This design package is ready for handoff to the acceptance-designer (DISTILL wave).

### Handoff Contents
- Architecture design with C4 diagrams
- Technology stack with rationale and ADRs
- Component boundaries with port definitions
- Data models with domain entities and DTOs
- 5 ADRs documenting key decisions

### Next Steps (DISTILL Wave)
1. Create acceptance test scenarios from user stories
2. Define test fixtures (sample templates, test data)
3. Design test infrastructure (TestClient, mock adapters)
