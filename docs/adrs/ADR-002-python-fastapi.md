# ADR-002: Python with FastAPI

## Status

Accepted

## Context

Selecting language and web framework for the voucher generation API. Requirements:
- Process Word (.docx) and LibreOffice (.odt) templates
- Convert documents to PDF and HTML via LibreOffice
- REST API with validation
- P95 latency < 2 seconds (I/O bound, not CPU bound)
- Team productivity and maintainability

## Decision

Use Python 3.11+ with FastAPI framework.

**Rationale:**
1. **Document ecosystem**: python-docx and odfpy are mature, well-maintained libraries
2. **LibreOffice integration**: Native UNO bridge (pyuno) for in-process conversion
3. **FastAPI features**: Built-in Pydantic validation, automatic OpenAPI docs, async support
4. **Performance**: Adequate for I/O-bound workload; async handles concurrency well

## Alternatives Considered

### 1. Node.js with Express
- **Pros**: Good async model, large ecosystem
- **Cons**: No mature ODT library; docx libraries less capable than python-docx; LibreOffice integration requires subprocess
- **Rejected**: Document processing ecosystem significantly weaker

### 2. Go with Gin/Echo
- **Pros**: Excellent performance, single binary deployment
- **Cons**: No ODT library; DOCX library (unioffice) is commercial; LibreOffice integration via subprocess only
- **Rejected**: Document processing libraries insufficient

### 3. Java with Spring Boot
- **Pros**: Strong LibreOffice integration (Apache POI, UNO); enterprise-ready
- **Cons**: Heavier deployment (JVM); slower startup; more verbose
- **Rejected**: Overhead not justified for single-API system

### 4. Python with Flask
- **Pros**: Simpler than FastAPI, widely known
- **Cons**: No built-in validation; manual OpenAPI; synchronous by default
- **Rejected**: FastAPI provides needed features with less boilerplate

## Consequences

### Positive
- Access to best document processing libraries
- Native LibreOffice integration path
- Type safety with type hints
- Fast development iteration
- Strong testing ecosystem (pytest)

### Negative
- Slower than Go for CPU-bound tasks (not a concern here)
- GIL limits true parallelism (mitigated by async I/O and multi-process workers)
- Deployment requires Python runtime

### Mitigations
- Use uvicorn with multiple workers for parallelism
- Profile rendering performance; optimize LibreOffice process pooling if needed
- Containerize with Python slim image

## Version Constraints

```
python >= 3.11
fastapi >= 0.100, < 0.200
uvicorn >= 0.23
pydantic >= 2.0
```

## Decision Date

2026-02-17

## Decision Makers

Morgan (Solution Architect)
