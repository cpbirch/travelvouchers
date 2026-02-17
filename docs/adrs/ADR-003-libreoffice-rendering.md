# ADR-003: LibreOffice for Document Rendering

## Status

Accepted

## Context

Need to convert Word (.docx) and LibreOffice (.odt) templates to PDF and HTML output. Requirements:
- High fidelity conversion (preserve formatting, fonts, images)
- Support both .docx and .odt input formats
- PDF output < 500KB for typical vouchers
- HTML output with inline CSS for email compatibility
- Open source, no license costs

## Decision

Use LibreOffice in headless mode for document conversion.

**Integration approach:**
1. Primary: UNO bridge (pyuno) for in-process conversion
2. Fallback: Command-line `soffice --convert-to` if UNO issues

**Process management:**
- Pre-spawn LibreOffice process pool for performance
- Socket mode for persistent connections
- 30-second timeout per conversion

## Alternatives Considered

### 1. WeasyPrint
- **Pros**: Pure Python, no external process
- **Cons**: HTML/CSS input only; cannot process DOCX/ODT
- **Rejected**: Does not support required input formats

### 2. Pandoc
- **Pros**: Universal document converter, open source
- **Cons**: Weaker format preservation; loses complex styling; no native Python API
- **Rejected**: Insufficient format fidelity

### 3. wkhtmltopdf
- **Pros**: Good HTML to PDF conversion
- **Cons**: HTML input only; deprecated project
- **Rejected**: Does not support DOCX/ODT input

### 4. Aspose.Words
- **Pros**: Excellent conversion quality; direct Python API
- **Cons**: Proprietary; expensive license ($999+/year)
- **Rejected**: Violates open source preference; cost not justified

### 5. Microsoft Graph API
- **Pros**: Best Word fidelity (native Microsoft)
- **Cons**: Cloud dependency; requires Microsoft 365 license; network latency
- **Rejected**: Adds cloud dependency and cost

### 6. docx2pdf (win32com)
- **Pros**: High fidelity Word conversion
- **Cons**: Windows only; requires Microsoft Office
- **Rejected**: Platform dependency; requires MS Office license

## Consequences

### Positive
- Open source (MPL-2.0), no license cost
- Excellent format fidelity for both DOCX and ODT
- Industry-proven document processing
- Both PDF and HTML output from single tool
- Self-hosted, no cloud dependency

### Negative
- Heavy dependency (~500MB installed)
- Process startup overhead (mitigated by pooling)
- Memory usage per process (~100-200MB)
- Occasional conversion quirks with complex documents

### Mitigations
- Process pooling eliminates cold-start latency
- Container includes LibreOffice pre-installed
- Template validation catches problematic documents early
- Fallback to command-line if UNO bridge fails

## Performance Considerations

| Operation | Typical Duration |
|-----------|-----------------|
| Cold start | 2-3 seconds |
| Warm conversion (PDF) | 200-500ms |
| Warm conversion (HTML) | 150-400ms |
| With process pool | < 500ms total |

Target P95 < 2s achievable with warm process pool.

## Container Requirements

```dockerfile
RUN apt-get update && apt-get install -y \
    libreoffice-core \
    libreoffice-writer \
    fonts-liberation \
    --no-install-recommends
```

## Decision Date

2026-02-17

## Decision Makers

Morgan (Solution Architect)
