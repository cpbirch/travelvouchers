# Component Boundaries: Voucher Generation System

## Overview

This document defines the component boundaries, port interfaces, and dependency rules for the hexagonal architecture.

---

## Package Structure

```
src/
  voucher_merger/
    __init__.py

    # Primary Adapters (Driving)
    adapters/
      __init__.py
      primary/
        __init__.py
        rest_api.py           # FastAPI routes
        request_models.py     # Pydantic request schemas
        response_models.py    # Pydantic response schemas
        error_handlers.py     # Exception to HTTP mapping

      # Secondary Adapters (Driven)
      secondary/
        __init__.py
        filesystem_template_repo.py
        filesystem_voucher_storage.py
        libreoffice_renderer.py
        s3_voucher_storage.py      # Future

    # Application Layer
    application/
      __init__.py
      generate_voucher_use_case.py
      check_existing_use_case.py
      exceptions.py               # Application-level exceptions

    # Domain Layer
    domain/
      __init__.py
      voucher.py                  # Voucher aggregate
      template.py                 # Template entity
      value_objects.py            # VoucherId, BookingRef, etc.
      merge_context.py            # MergeContext
      template_merger.py          # Domain service
      exceptions.py               # Domain exceptions

    # Ports
    ports/
      __init__.py
      template_repository.py      # Interface
      voucher_storage.py          # Interface
      document_renderer.py        # Interface

    # Configuration
    config.py
    main.py                       # Application entry point

tests/
  unit/
    domain/
    application/
  integration/
    adapters/
  acceptance/
    features/
    step_definitions/
  fixtures/
    templates/
```

---

## Port Definitions

### Port: TemplateRepository

**Location**: `src/voucher_merger/ports/template_repository.py`

**Purpose**: Load and parse templates from storage.

```python
from abc import ABC, abstractmethod
from typing import Optional
from voucher_merger.domain.template import Template

class TemplateRepository(ABC):
    """Port for template storage access."""

    @abstractmethod
    def find_by_id(self, template_id: str) -> Optional[Template]:
        """
        Load and parse template by ID.

        Returns:
            Template with parsed placeholders, or None if not found.
        """
        pass

    @abstractmethod
    def exists(self, template_id: str) -> bool:
        """
        Check if template exists without full parsing.

        Returns:
            True if template file exists.
        """
        pass
```

**Adapters**:
- `FilesystemTemplateRepository`: Reads from local `/templates/` directory

---

### Port: VoucherStorage

**Location**: `src/voucher_merger/ports/voucher_storage.py`

**Purpose**: Persist and retrieve generated vouchers.

```python
from abc import ABC, abstractmethod
from typing import Optional
from voucher_merger.domain.value_objects import StoragePath, StorageUrls, VoucherMetadata

class VoucherStorage(ABC):
    """Port for voucher file storage."""

    @abstractmethod
    def store(
        self,
        path: StoragePath,
        pdf_content: bytes,
        html_content: str,
        metadata: VoucherMetadata
    ) -> StorageUrls:
        """
        Store PDF and HTML files.

        Args:
            path: Storage path (booking_id/service_date)
            pdf_content: PDF binary content
            html_content: HTML string content
            metadata: Voucher metadata for retrieval

        Returns:
            StorageUrls with accessible PDF and HTML URLs.

        Raises:
            StorageUnavailableError: If storage service is down.
        """
        pass

    @abstractmethod
    def exists(self, path: StoragePath) -> bool:
        """
        Check if voucher already exists at path.

        Used for idempotency check.
        """
        pass

    @abstractmethod
    def get_metadata(self, path: StoragePath) -> Optional[VoucherMetadata]:
        """
        Get metadata for existing voucher.

        Returns:
            VoucherMetadata if exists, None otherwise.
        """
        pass
```

**Adapters**:
- `FilesystemVoucherStorage`: Writes to local `/vouchers/` directory
- `S3VoucherStorage`: Writes to S3 bucket (future)

---

### Port: DocumentRenderer

**Location**: `src/voucher_merger/ports/document_renderer.py`

**Purpose**: Convert merged documents to PDF and HTML.

```python
from abc import ABC, abstractmethod
from voucher_merger.domain.template import MergedDocument

class DocumentRenderer(ABC):
    """Port for document format conversion."""

    @abstractmethod
    def render_pdf(self, document: MergedDocument) -> bytes:
        """
        Convert merged document to PDF.

        Args:
            document: Merged document with substituted placeholders.

        Returns:
            PDF binary content.

        Raises:
            RenderError: If conversion fails.
        """
        pass

    @abstractmethod
    def render_html(self, document: MergedDocument) -> str:
        """
        Convert merged document to HTML.

        Args:
            document: Merged document with substituted placeholders.

        Returns:
            HTML string with inline CSS and base64 images.

        Raises:
            RenderError: If conversion fails.
        """
        pass
```

**Adapters**:
- `LibreOfficeRenderer`: Uses LibreOffice headless for conversion

---

## Adapter Specifications

### Primary Adapter: REST API

**Location**: `src/voucher_merger/adapters/primary/rest_api.py`

**Responsibility**: HTTP interface for voucher generation.

**Endpoints**:
| Method | Path | Handler | Response |
|--------|------|---------|----------|
| POST | /vouchers | generate_voucher | 201/200/4xx/5xx |
| GET | /health | health_check | 200 |

**Dependencies**:
- `GenerateVoucherUseCase` (injected)
- Pydantic models for request/response

**Error Mapping**:
| Domain Exception | HTTP Status | Error Code |
|-----------------|-------------|------------|
| ValidationError | 400 | VALIDATION_FAILED |
| TemplateNotFoundError | 404 | TEMPLATE_NOT_FOUND |
| TemplateCorruptError | 500 | TEMPLATE_ERROR |
| RenderError | 500 | RENDER_ERROR |
| StorageUnavailableError | 503 | STORAGE_UNAVAILABLE |

---

### Secondary Adapter: FilesystemTemplateRepository

**Location**: `src/voucher_merger/adapters/secondary/filesystem_template_repo.py`

**Responsibility**: Load templates from local filesystem.

**Configuration**:
- `TEMPLATE_DIR`: Path to templates directory

**Behavior**:
- Scans for `.docx` and `.odt` files
- Uses python-docx for .docx parsing
- Uses odfpy for .odt parsing
- Extracts placeholders via regex `\{\{[a-z_.]+\}\}`

---

### Secondary Adapter: FilesystemVoucherStorage

**Location**: `src/voucher_merger/adapters/secondary/filesystem_voucher_storage.py`

**Responsibility**: Store vouchers on local filesystem.

**Configuration**:
- `VOUCHER_DIR`: Path to vouchers directory
- `BASE_URL`: URL prefix for generated URLs

**Storage Layout**:
```
{VOUCHER_DIR}/
  {booking_id}/
    {service_date}/
      voucher.pdf
      voucher.html
      metadata.json
```

**Idempotency**: Check `metadata.json` existence.

---

### Secondary Adapter: LibreOfficeRenderer

**Location**: `src/voucher_merger/adapters/secondary/libreoffice_renderer.py`

**Responsibility**: Convert documents to PDF/HTML using LibreOffice.

**Implementation Options**:
1. **UNO Bridge**: In-process via pyuno
2. **Command Line**: Subprocess `soffice --convert-to`

**Configuration**:
- `LIBREOFFICE_PATH`: Path to soffice binary
- `CONVERSION_TIMEOUT`: Max seconds per conversion (default: 30)

---

## Dependency Injection

### Container Setup

```python
# src/voucher_merger/config.py

from voucher_merger.ports.template_repository import TemplateRepository
from voucher_merger.ports.voucher_storage import VoucherStorage
from voucher_merger.ports.document_renderer import DocumentRenderer

class Container:
    """Dependency injection container."""

    def __init__(self, settings: Settings):
        self.settings = settings

    def template_repository(self) -> TemplateRepository:
        from voucher_merger.adapters.secondary.filesystem_template_repo import (
            FilesystemTemplateRepository
        )
        return FilesystemTemplateRepository(self.settings.template_dir)

    def voucher_storage(self) -> VoucherStorage:
        from voucher_merger.adapters.secondary.filesystem_voucher_storage import (
            FilesystemVoucherStorage
        )
        return FilesystemVoucherStorage(
            self.settings.voucher_dir,
            self.settings.base_url
        )

    def document_renderer(self) -> DocumentRenderer:
        from voucher_merger.adapters.secondary.libreoffice_renderer import (
            LibreOfficeRenderer
        )
        return LibreOfficeRenderer(self.settings.libreoffice_path)

    def generate_voucher_use_case(self):
        from voucher_merger.application.generate_voucher_use_case import (
            GenerateVoucherUseCase
        )
        return GenerateVoucherUseCase(
            template_repository=self.template_repository(),
            voucher_storage=self.voucher_storage(),
            document_renderer=self.document_renderer()
        )
```

---

## Dependency Rules

### Layer Dependencies

```
+------------------+     +------------------+     +------------------+
| Primary Adapters | --> | Application      | --> | Domain           |
+------------------+     +------------------+     +------------------+
                                |                        ^
                                | depends on             |
                                v                        |
                         +------------------+            |
                         | Ports            | -----------+
                         +------------------+      references
                                ^
                                | implements
                                |
                         +------------------+
                         | Secondary        |
                         | Adapters         |
                         +------------------+
```

### Import Rules

| From Package | Can Import |
|--------------|------------|
| `domain` | (nothing external) |
| `ports` | `domain.value_objects`, `domain.template` |
| `application` | `domain`, `ports` |
| `adapters.primary` | `application`, `domain.value_objects` |
| `adapters.secondary` | `ports`, `domain.value_objects`, external libs |

### Forbidden Imports

| Package | Cannot Import |
|---------|---------------|
| `domain` | `application`, `adapters`, `ports`, external libs |
| `ports` | `application`, `adapters` |
| `application` | `adapters` |
| `adapters.primary` | `adapters.secondary` |

---

## Testing Boundaries

### Unit Tests (No I/O)

| Component | Test Strategy |
|-----------|---------------|
| Domain entities | Direct instantiation, method calls |
| Domain services | Pure function testing |
| Application use cases | Mock ports |

### Integration Tests (Real Adapters)

| Component | Test Strategy |
|-----------|---------------|
| FilesystemTemplateRepo | Real filesystem, fixture templates |
| FilesystemVoucherStorage | Temp directory |
| LibreOfficeRenderer | Real LibreOffice, verify output |

### Acceptance Tests (End-to-End)

| Scope | Test Strategy |
|-------|---------------|
| Full flow | HTTP client -> API -> Storage |
| Fixtures | Pre-created templates, temp storage |

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEMPLATE_DIR` | `/templates` | Template file location |
| `VOUCHER_DIR` | `/vouchers` | Voucher storage location |
| `BASE_URL` | `http://localhost:8000` | URL prefix for voucher URLs |
| `LIBREOFFICE_PATH` | `/usr/bin/soffice` | LibreOffice binary path |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

### Settings Model

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    template_dir: str = "/templates"
    voucher_dir: str = "/vouchers"
    base_url: str = "http://localhost:8000"
    libreoffice_path: str = "/usr/bin/soffice"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
```

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-02-17 | Morgan (Solution Architect) | Initial boundaries |
