# ADR-005: Document Processing Libraries

## Status

Accepted

## Context

Need to parse and manipulate Word (.docx) and LibreOffice (.odt) templates before conversion. Requirements:
- Extract placeholder tokens (`{{customer.last_name}}`)
- Substitute placeholders with data values
- Preserve document structure and formatting
- Support both .docx and .odt formats

## Decision

Use python-docx for .docx files and odfpy for .odt files.

**Workflow:**
1. Detect file format from template_id or file extension
2. Load with appropriate library (python-docx or odfpy)
3. Extract placeholders via regex: `\{\{[a-z_.]+\}\}`
4. Substitute placeholders in-memory
5. Save to temporary file for LibreOffice conversion

## Alternatives Considered

### 1. docxtpl (Jinja2 for DOCX)
- **Pros**: Familiar Jinja2 syntax; designed for templating
- **Cons**: DOCX only; no ODT support; less control over raw document
- **Rejected**: Does not support required ODT format

### 2. LibreOffice UNO for Parsing
- **Pros**: Single tool for both formats; native handling
- **Cons**: Heavy process startup for simple parsing; complex API
- **Rejected**: Overkill for placeholder extraction; python-docx/odfpy simpler

### 3. Aspose.Words
- **Pros**: Excellent API; handles both formats
- **Cons**: Proprietary; expensive license
- **Rejected**: Violates open source preference

### 4. docx (Node.js)
- **Pros**: Good DOCX support
- **Cons**: Different language; no ODT; would require cross-process
- **Rejected**: Language mismatch

## Consequences

### Positive
- Pure Python, no subprocess for parsing
- Well-documented, stable libraries
- Direct access to document structure
- MIT/Apache licenses (permissive)

### Negative
- Two different APIs to learn/maintain
- Some edge cases may differ between libraries
- Complex documents may have parsing quirks

### Mitigations
- Abstract behind common interface in adapter
- Template validation catches parsing issues early
- Walking skeleton validates basic flow

## Library Details

### python-docx (MIT License)
- Reads/writes Office Open XML (.docx)
- Access to paragraphs, tables, runs, styles
- Version: 1.1+

### odfpy (Apache-2.0 License)
- Reads/writes OpenDocument Format (.odt)
- DOM-style access to document elements
- Version: 1.4+

## Placeholder Substitution Strategy

### python-docx
```python
for paragraph in document.paragraphs:
    for run in paragraph.runs:
        for key, value in placeholders.items():
            if "{{" + key + "}}" in run.text:
                run.text = run.text.replace("{{" + key + "}}", value)
```

### odfpy
```python
for element in document.getElementsByType(text.P):
    for text_node in element.childNodes:
        if hasattr(text_node, 'data'):
            for key, value in placeholders.items():
                if "{{" + key + "}}" in text_node.data:
                    text_node.data = text_node.data.replace("{{" + key + "}}", value)
```

## Decision Date

2026-02-17

## Decision Makers

Morgan (Solution Architect)
