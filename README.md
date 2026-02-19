# Voucher Merger Service

Generates PDF vouchers from DOCX/ODT templates with customer and service data.

## Prerequisites

- Python 3.11+
- LibreOffice (headless) for PDF rendering:
  ```bash
  brew install --cask libreoffice   # macOS
  apt-get install libreoffice       # Debian/Ubuntu
  ```
- pip / virtualenv

## Installation

```bash
pip install -e ".[dev]"
```

## Running the Service

```bash
make dev
# or without make:
PYTHONPATH=src/main uvicorn voucher_merger.main:app --reload --port 8000
```

Auto-generated API docs: http://localhost:8000/docs

## Running Tests

```bash
make test
# or without make:
PYTHONPATH=src/main pytest src/tests/ -v
```

## Other Development Commands

| Command          | Description                        |
|------------------|------------------------------------|
| `make lint`      | ruff code linting                  |
| `make typecheck` | mypy type checking                 |
| `make clean`     | remove build artifacts and caches  |

## Project Structure

```
src/main/voucher_merger/   # Production source code
  adapters/                # FastAPI REST API, LibreOffice renderer, storage
  application/             # Use cases (GenerateVoucher)
  domain/                  # Domain models and validators
  ports/                   # Abstract interfaces
  main.py                  # Application factory + module-level app instance
src/tests/                 # Test suite
  acceptance/              # BDD acceptance tests (pytest-bdd)
docs/                      # Architecture decisions, research, analysis
Makefile                   # Developer task runner
pyproject.toml             # Project configuration and dependencies
```

## Claude.ai spec driven development using nWave

Not a single line of code was written by a person.  Instead, the entire project was developed using a spec-driven 
approach with nWave and Claude.ai.  Based on a simple single sentence product description.

If you fork and evolve this, install https://nwave.ai/ and use the `nwave` Claude CLI tool.