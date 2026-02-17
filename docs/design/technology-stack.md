# Technology Stack: Voucher Generation System

## Stack Overview

| Layer | Technology | Version | License |
|-------|------------|---------|---------|
| Language | Python | 3.11+ | PSF (open source) |
| Web Framework | FastAPI | 0.100+ | MIT |
| ASGI Server | uvicorn | 0.23+ | BSD-3-Clause |
| Document Processing | python-docx | 1.1+ | MIT |
| Document Processing | odfpy | 1.4+ | Apache-2.0 |
| PDF Generation | LibreOffice | 7.5+ | MPL-2.0 |
| PDF Library | uno (pyuno) | bundled | MPL-2.0 |
| HTML Generation | LibreOffice | 7.5+ | MPL-2.0 |
| Validation | pydantic | 2.0+ | MIT |
| Testing | pytest | 7.0+ | MIT |
| Testing (BDD) | pytest-bdd | 7.0+ | MIT |
| HTTP Testing | httpx | 0.24+ | BSD-3-Clause |

---

## Language: Python 3.11+

### Decision
Python with type hints and modern async support.

### Rationale
- **Document processing ecosystem**: Best libraries for DOCX/ODT manipulation
- **LibreOffice integration**: Native Python UNO bridge (pyuno)
- **Team productivity**: Readable, maintainable code
- **FastAPI compatibility**: Excellent async web framework support

### Alternatives Considered

| Alternative | Evaluation | Rejection Reason |
|-------------|------------|------------------|
| Node.js | Good async, weak DOCX/ODT support | No mature ODT library, LibreOffice integration complex |
| Go | Excellent performance | Poor document processing libraries, no ODT support |
| Java | Strong LibreOffice integration | Heavier deployment, slower startup |

### Trade-offs
- **Accepted**: Slower than Go for pure computation
- **Mitigated**: I/O bound workload (file processing), async handles well

---

## Web Framework: FastAPI

### Decision
FastAPI with Pydantic validation.

### Rationale
- **Built-in validation**: Pydantic models match domain requirements
- **OpenAPI generation**: Automatic API documentation
- **Async native**: Non-blocking I/O for storage operations
- **Type safety**: Full type hint support
- **Performance**: One of fastest Python frameworks

### Alternatives Considered

| Alternative | Evaluation | Rejection Reason |
|-------------|------------|------------------|
| Flask | Simpler, widely known | No built-in validation, manual OpenAPI |
| Django REST | Full-featured | Overkill for single-endpoint API |
| Starlette | FastAPI foundation | FastAPI adds validation layer we need |

### Configuration
- Production: uvicorn with gunicorn process manager
- Development: uvicorn with reload
- Workers: 4+ for production (match CPU cores)

---

## Document Processing: python-docx + odfpy

### Decision
python-docx for .docx files, odfpy for .odt files.

### Rationale
- **Native Python**: No external dependencies for parsing
- **Placeholder extraction**: Easy regex-based placeholder finding
- **Format preservation**: Maintain formatting during read/modify
- **Maturity**: Both libraries stable and well-maintained

### Alternatives Considered

| Alternative | Evaluation | Rejection Reason |
|-------------|------------|------------------|
| docxtpl | Template-focused | Less control over raw document manipulation |
| unoconv (Python) | Unified interface | Requires LibreOffice for parsing (overhead) |
| Aspose.Words | Excellent features | Proprietary, paid license |

### Usage Pattern
1. **Read**: python-docx/odfpy loads document structure
2. **Modify**: In-memory placeholder replacement
3. **Write**: Save modified document to temp file
4. **Convert**: LibreOffice converts to PDF/HTML

---

## PDF/HTML Generation: LibreOffice Headless

### Decision
LibreOffice in headless mode via UNO bridge or command-line.

### Rationale
- **Format fidelity**: Best Word/ODT to PDF conversion
- **Open source**: MPL-2.0 license, no cost
- **HTML support**: Generates email-compatible HTML
- **Industry standard**: Proven in enterprise document workflows

### Alternatives Considered

| Alternative | Evaluation | Rejection Reason |
|-------------|------------|------------------|
| WeasyPrint | Python-native PDF | No DOCX/ODT input support |
| wkhtmltopdf | HTML to PDF | No DOCX/ODT input support |
| Pandoc | Universal converter | Weaker format preservation |
| Microsoft Graph API | Excellent Word support | Cloud dependency, requires license |
| Aspose | Excellent conversion | Proprietary, expensive |

### Integration Approach
1. **Primary**: UNO bridge (pyuno) for in-process conversion
2. **Fallback**: soffice command-line if UNO issues

### Performance Considerations
- **Process pool**: Pre-spawn LibreOffice instances
- **Socket mode**: LibreOffice listening on socket for requests
- **Timeout**: 30s per conversion, fail fast

---

## Validation: Pydantic

### Decision
Pydantic v2 for request/response validation.

### Rationale
- **FastAPI integration**: Native support
- **Declarative**: Schema-as-code
- **Error messages**: Structured validation errors
- **Performance**: v2 significantly faster than v1

### Schema Definition
```python
class VoucherRequest(BaseModel):
    template_id: str
    booking_id: str = Field(pattern=r"^BK-\d{4}-\d{5}$")
    service_date: date
    customer: CustomerData
    service: ServiceData
```

---

## Storage: Filesystem (S3-compatible interface)

### Decision
Local filesystem for walking skeleton, S3-compatible for production.

### Rationale
- **Simplicity**: Filesystem for development/testing
- **Scalability**: S3 for production volume
- **Portability**: Abstract via port interface

### Storage Adapter Options
| Adapter | Use Case |
|---------|----------|
| FilesystemStorage | Development, testing, walking skeleton |
| S3Storage | Production with AWS |
| MinioStorage | Self-hosted S3-compatible |

### Path Structure
```
/vouchers/{booking_id}/{service_date}/
  voucher.pdf
  voucher.html
  metadata.json
```

---

## Testing Stack

### Unit Tests: pytest
- Domain logic testing
- Mocked adapters
- Fast feedback (< 5 seconds full suite)

### Integration Tests: pytest + httpx
- Test REST API with TestClient
- In-memory storage adapter
- Real LibreOffice conversion

### Acceptance Tests: pytest-bdd
- Gherkin scenarios from requirements
- End-to-end with real storage
- Performance assertions

### Test Fixtures
```
tests/
  fixtures/
    templates/
      skeleton-template.docx
      airport-transfer-v2.docx
      sightseeing-tour-v1.odt
```

---

## Development Tools

| Tool | Purpose | License |
|------|---------|---------|
| ruff | Linting + formatting | MIT |
| mypy | Type checking | MIT |
| pre-commit | Git hooks | MIT |
| pytest-cov | Coverage | MIT |

### Quality Gates
- Type coverage: 100% (strict mode)
- Test coverage: 80% minimum
- Lint: zero warnings

---

## Deployment Dependencies

### Container Requirements
```dockerfile
# Base image with LibreOffice
FROM python:3.11-slim

# Install LibreOffice headless
RUN apt-get update && apt-get install -y \
    libreoffice-core \
    libreoffice-writer \
    --no-install-recommends

# Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt
```

### System Dependencies
- LibreOffice 7.5+
- fontconfig (for font rendering)
- fonts-liberation (standard fonts)

---

## License Summary

All components use permissive open source licenses:

| License | Components |
|---------|------------|
| MIT | FastAPI, Pydantic, python-docx, pytest, ruff |
| BSD | uvicorn, httpx |
| Apache-2.0 | odfpy |
| MPL-2.0 | LibreOffice |
| PSF | Python |

**No proprietary or paid licenses required.**

---

## Version Pinning Strategy

### Production
- Pin major.minor versions in requirements.txt
- Dependabot for security updates
- Quarterly dependency review

### Example requirements.txt
```
fastapi>=0.100,<0.200
uvicorn>=0.23,<0.30
pydantic>=2.0,<3.0
python-docx>=1.1,<2.0
odfpy>=1.4,<2.0
pytest>=7.0,<8.0
pytest-bdd>=7.0,<8.0
httpx>=0.24,<0.30
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-17 | Morgan (Solution Architect) | Initial stack selection |
