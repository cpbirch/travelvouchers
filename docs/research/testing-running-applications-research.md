# Testing a Running Application: Tools, Patterns, and Recommendations

**Research Date:** 2026-02-19
**Depth:** Detailed
**Project Context:** Python/FastAPI application (template-merger / voucher generation service)
**Researcher:** Nova (nw-researcher)

---

## Executive Summary

Testing a running application is a distinct discipline from unit testing. Where unit tests isolate logic, testing against a live or test-server instance validates that the full stack — routing, validation, serialisation, middleware, and dependencies — behaves correctly as an integrated system.

This research covers six testing layers: manual HTTP/API clients for rapid iteration, automated integration testing with framework-native clients, smoke testing and health-check patterns, end-to-end browser automation, contract testing, and CI/CD-integrated test pipelines.

**Key finding:** For this project (Python/FastAPI with pytest and httpx), the highest-ROI path is a two-tier strategy:

1. **Development speed**: Use FastAPI's `TestClient` / `httpx.AsyncClient` for fast, server-free integration tests plus HTTPie at the command line for quick manual probing.
2. **Deployment confidence**: Implement a `/health` endpoint and a lightweight smoke-test suite that runs against the actual running process in CI/CD.

Source evidence is rated **High** (3+ independent sources), **Medium** (2 sources), or **Low** (1 source or inference).

---

## 1. Key Findings

### 1.1 The Two Modes of "Testing a Running Application"

Evidence (High confidence — 3 sources):

There are two meaningfully different things developers call "testing a running application":

**In-process testing**: The test framework binds to the application's ASGI/WSGI interface internally. No real network socket is used. Tests are fast, deterministic, and easy to run in CI. This is what FastAPI `TestClient` and `httpx.AsyncClient` with `ASGITransport` do.

**Out-of-process testing**: The application is started as a real process (e.g., `uvicorn main:app`). Tests connect over a real TCP socket. This validates configuration, startup hooks, environment variables, and OS-level concerns that in-process testing cannot catch.

Most teams use both: in-process for the bulk of integration tests, out-of-process for smoke tests after deployment.

Sources:
- [FastAPI Testing Tutorial](https://fastapi.tiangolo.com/tutorial/testing/) — official FastAPI docs explain TestClient wraps the ASGI app directly without starting uvicorn
- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/) — documents the `ASGITransport` pattern for `httpx.AsyncClient`
- [TestDriven.io FastAPI Testing](https://testdriven.io/blog/fastapi-crud/) — practical guide covering both in-process and live-server approaches

---

### 1.2 FastAPI-Native Integration Testing (Highest ROI for This Project)

Evidence (High confidence — 4 sources):

FastAPI provides a built-in `TestClient` (wrapping `httpx`) that does not require a running server. It is the standard approach for integration tests in the Python/FastAPI ecosystem.

```python
# Basic synchronous TestClient usage
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_generate_voucher():
    response = client.post("/vouchers/generate", json={
        "template_id": "airport-transfer-v2",
        "booking_id": "BK-2026-00001",
        "service_date": "2026-03-15",
        "customer": {"name": "Alice"},
        "service": {"type": "airport-transfer"}
    })
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
```

For async endpoints, `httpx.AsyncClient` with `ASGITransport` is the preferred pattern:

```python
# Async testing with httpx.AsyncClient
import pytest
import httpx
from app.main import app

@pytest.fixture
async def async_client():
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client

@pytest.mark.anyio
async def test_health_check(async_client):
    response = await async_client.get("/health")
    assert response.status_code == 200
```

Sources:
- [FastAPI Testing Tutorial](https://fastapi.tiangolo.com/tutorial/testing/) — canonical documentation
- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/) — AsyncClient + ASGITransport pattern
- [TestDriven.io FastAPI CRUD Testing](https://testdriven.io/blog/fastapi-crud/) — real-world async test examples
- [Pythoneo FastAPI Testing Guide](https://pythoneo.com/testing-fastapi-applications/) — coverage and best practice patterns

**Important caveat:** If the application uses lifespan events (`@app.on_event("startup")` or the newer `lifespan` context manager), `AsyncClient` does not trigger them by default. Use the `asgi-lifespan` package (`LifespanManager`) to force lifespan execution in tests.

---

### 1.3 HTTP Clients for Manual Testing Against a Live Server

Evidence (High confidence — 3+ sources):

When the application is running locally (e.g., `uvicorn app.main:app --reload --port 8000`), three command-line tools cover the majority of developer needs:

#### curl

The ubiquitous baseline. Available on every Unix system without installation. Best for scripting and CI due to its stability and predictability.

```bash
# Test the voucher endpoint
curl -X POST http://localhost:8000/vouchers/generate \
  -H "Content-Type: application/json" \
  -d '{"template_id": "airport-transfer-v2", "booking_id": "BK-2026-00001"}' \
  -o voucher.pdf \
  --write-out "\nHTTP Status: %{http_code}\n"

# Quick health check
curl -sf http://localhost:8000/health && echo "OK" || echo "FAIL"
```

#### HTTPie

A Python-based CLI built for human readability. Colourised output, automatic JSON detection, and simpler syntax. Requires installation (`pip install httpie` or `brew install httpie`).

```bash
# Same request with HTTPie — much more readable
http POST localhost:8000/vouchers/generate \
  template_id=airport-transfer-v2 \
  booking_id=BK-2026-00001

# Health check
http GET localhost:8000/health
```

Key differences (evidence: multiple comparative analyses):
- curl is C-based, pre-installed, faster in automated scripts; HTTPie is Python-based, requires install, far friendlier for interactive use
- HTTPie automatically sets `Content-Type: application/json` for JSON data; curl requires explicit `-H`
- HTTPie colourises and pretty-prints response JSON; curl outputs raw bytes
- For scripting, curl is preferred; for interactive exploration, HTTPie wins

#### curlie

A third option that wraps curl with HTTPie-like syntax (`brew install curlie`). Provides HTTPie-style output while keeping curl's underlying reliability — a useful middle ground.

Sources:
- [HTTPie vs cURL: CLI Testing Tools Comparison](https://yrkan.com/blog/httpie-curl-cli-testing/) — systematic comparison with examples
- [HTTPie Official Docs — Alternatives](https://httpie.io/docs/cli/alternatives) — HTTPie's own comparison of tools
- [StackShare: curl vs HTTPie](https://stackshare.io/stackups/curl-vs-httpie) — community comparison
- [curlie GitHub](https://github.com/rs/curlie) — the hybrid tool

---

### 1.4 GUI-Based API Clients for Exploration and Documentation

Evidence (High confidence — 3 sources):

GUI clients provide a persistent, exploreable workspace for API endpoints. They are particularly useful during development when the API shape is evolving.

**Bruno** (Recommended — open source, git-native):
- Stores collections as plain text files on disk (can be committed alongside code)
- Fully offline, no cloud account required
- Supports environments, variables, scripting, and tests
- Featured by Thoughtworks Technology Radar (April 2024)
- Free core, with paid Pro/Ultimate tiers

**Insomnia** (Open source, developer-first):
- Strong GraphQL and REST support
- Local-first with optional cloud sync
- Good scripting capabilities for pre/post-request logic

**Postman** (Industry standard, partially proprietary):
- Most feature-complete: collections, monitors, mock servers, CI/CD integration
- Requires account for most collaboration features
- Best for teams that need API documentation alongside testing

**FastAPI built-in Swagger UI**:
- FastAPI automatically generates `/docs` (Swagger UI) and `/redoc` endpoints
- Zero setup — immediately available when the server starts
- Interactive: send real requests from the browser
- Ideal for quick exploration and sharing with non-technical stakeholders

Sources:
- [Bruno Official Site](https://www.usebruno.com/) — features and philosophy
- [Bruno on Git Tower Blog](https://www.git-tower.com/blog/bruno-api-client-using-git) — git-native workflow explanation
- [Top API Testing Tools 2025](https://www.stackhawk.com/blog/top-10-api-tools-for-testing-in-2025/) — comparative overview including Bruno, Insomnia, Postman
- [FastAPI Testing Tutorial](https://fastapi.tiangolo.com/tutorial/testing/) — documents built-in Swagger UI at `/docs`

---

### 1.5 Smoke Testing and Health Check Patterns

Evidence (High confidence — 4 sources):

A **health check endpoint** is the foundation of smoke testing. The Microsoft Azure Architecture Center defines it as: "Implement health monitoring by sending requests to an endpoint on your application. The application should perform the necessary checks and then return an indication of its status."

The standard pattern for a FastAPI service:

```python
# Health check endpoint — minimal implementation
from fastapi import FastAPI
from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    dependencies: dict[str, str]

@app.get("/health", response_model=HealthResponse)
async def health_check():
    # Check critical dependencies
    storage_ok = await check_storage_available()
    libreoffice_ok = await check_libreoffice_process()

    all_ok = storage_ok and libreoffice_ok
    return HealthResponse(
        status="healthy" if all_ok else "degraded",
        dependencies={
            "storage": "ok" if storage_ok else "error",
            "libreoffice": "ok" if libreoffice_ok else "error"
        }
    )
```

**Smoke test pattern** (shell script for CI/CD):

```bash
#!/usr/bin/env bash
# smoke-test.sh — runs after deployment
set -e

BASE_URL="${APP_URL:-http://localhost:8000}"
MAX_RETRIES=10
RETRY_DELAY=3

echo "Waiting for application to start..."
for i in $(seq 1 $MAX_RETRIES); do
    if curl -sf "$BASE_URL/health" > /dev/null; then
        echo "Application is up."
        break
    fi
    echo "Attempt $i/$MAX_RETRIES failed, retrying in ${RETRY_DELAY}s..."
    sleep $RETRY_DELAY
done

# Critical path smoke tests
echo "Running smoke tests..."
curl -sf "$BASE_URL/health" | python3 -c "
import sys, json
data = json.load(sys.stdin)
assert data['status'] == 'healthy', f'Health check failed: {data}'
print('Health check passed.')
"

echo "Smoke tests passed."
```

**Smoke testing with pytest** (preferred for Python projects):

```python
# tests/smoke/test_smoke.py
import pytest
import httpx

BASE_URL = "http://localhost:8000"  # Override via env var

def test_health_endpoint_returns_200():
    with httpx.Client() as client:
        response = client.get(f"{BASE_URL}/health")
    assert response.status_code == 200

def test_health_endpoint_reports_healthy():
    with httpx.Client() as client:
        response = client.get(f"{BASE_URL}/health")
    data = response.json()
    assert data["status"] == "healthy"

def test_openapi_schema_reachable():
    with httpx.Client() as client:
        response = client.get(f"{BASE_URL}/openapi.json")
    assert response.status_code == 200
```

**Best practices** for health endpoints (sourced from Microsoft Architecture Center and microservices.io):
- Return HTTP 200 for healthy, 503 for degraded/unhealthy (not just 200 for everything)
- Check downstream dependencies (databases, external services, file storage)
- Return a structured JSON body with individual dependency statuses
- Respond within 1 second; expensive checks should be cached or run asynchronously
- Secure the endpoint (avoid exposing internal system details publicly)
- Provide separate liveness (is the process running?) and readiness (is it ready to serve traffic?) endpoints for Kubernetes deployments

Sources:
- [Health Endpoint Monitoring Pattern — Microsoft Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring) — canonical pattern documentation
- [Health Check API Pattern — microservices.io](https://microservices.io/patterns/observability/health-check-api.html) — Chris Richardson's microservices pattern
- [Smoke Testing in CI/CD Pipelines — CircleCI](https://circleci.com/blog/smoke-tests-in-cicd-pipelines/) — CI/CD integration patterns and shell-based smoke tests
- [API Smoke Testing — APIdog](https://apidog.com/blog/api-testing-method-smoke-tests/) — smoke test methodology and patterns

---

### 1.6 End-to-End Testing Against a Running Application

Evidence (High confidence — 3 sources):

For applications with a web UI or complex multi-step workflows, browser automation provides the highest-confidence test layer.

**Playwright** (Microsoft, open source):
- Supports Chromium, Firefox, and WebKit natively
- TypeScript, Python, Java, and .NET language bindings
- Python bindings (`playwright` package) integrate directly with pytest via `pytest-playwright`
- Excellent for testing document download workflows (like PDF generation)
- Built-in network interception and request mocking

```python
# Example: Test that clicking "Generate Voucher" downloads a PDF
from playwright.sync_api import Page, expect

def test_voucher_download(page: Page):
    page.goto("http://localhost:8000/ui")
    page.fill("#booking-id", "BK-2026-00001")

    with page.expect_download() as download_info:
        page.click("#generate-voucher")

    download = download_info.value
    assert download.suggested_filename.endswith(".pdf")
```

**Cypress** (JavaScript/TypeScript):
- Runs tests directly inside the browser process — excellent developer experience
- Real-time test runner with time-travel debugging
- JavaScript/TypeScript only — less natural for a Python project
- Strongest for JavaScript-heavy frontends

**Key architectural difference:** Playwright uses a client-server model (test code talks to browser via protocol); Cypress embeds test code directly inside the browser process. For a Python/FastAPI project with no JavaScript frontend, Playwright's Python bindings are the more natural choice.

**When E2E is warranted for this project:** If the service grows to include a web UI, file upload workflows, or multi-step user journeys, Playwright is the appropriate choice. For the current headless API-only service, Playwright adds overhead with little benefit over httpx-based integration tests.

Sources:
- [Playwright vs Cypress — BrowserStack](https://www.browserstack.com/guide/playwright-vs-cypress) — detailed comparison
- [Playwright vs Cypress — Katalon](https://katalon.com/resources-center/blog/playwright-vs-cypress) — architectural and feature comparison for 2025
- [Comparative Analysis of Cypress and Playwright — ResearchGate](https://www.researchgate.net/publication/396039934_Comparative_analysis_of_Cypress_and_Playwright_frameworks_in_end-to-end_testing_for_applications_based_on_Angular) — academic comparative study

---

### 1.7 Contract Testing

Evidence (High confidence — 3 sources):

Contract testing addresses a specific problem: when a consumer (API client) and provider (API server) are developed independently, they can drift out of sync. Traditional integration tests catch this only when both systems are running together.

**Pact** is the dominant contract testing framework for HTTP APIs:
- Consumer writes a test expressing its expectations of the provider API
- Pact generates a JSON "contract" (pact file) from the consumer test
- The contract is published to a Pact Broker
- Provider tests replay the contract interactions against the real provider to verify compatibility

```python
# Consumer-side Pact test (Python pact-python library)
from pact import Consumer, Provider

pact = Consumer("VoucherClient").has_pact_with(Provider("VoucherService"))

def test_generate_voucher_contract():
    pact.given("a valid booking exists") \
        .upon_receiving("a voucher generation request") \
        .with_request("POST", "/vouchers/generate", body={
            "template_id": "airport-transfer-v2",
            "booking_id": "BK-2026-00001"
        }) \
        .will_respond_with(200, headers={"content-type": "application/pdf"})

    with pact:
        client = VoucherClient(base_url=pact.uri)
        result = client.generate_voucher("BK-2026-00001", "airport-transfer-v2")
        assert result.content_type == "application/pdf"
```

**When contract testing is valuable:** When the API has multiple consumers (mobile app, web frontend, partner integrations) that evolve independently. For single-consumer APIs or internal-only services, the overhead may not be justified.

**FastAPI's automatic OpenAPI schema** serves a related purpose: it documents the API contract as code, and tools like `schemathesis` can use it to automatically generate and run property-based tests against the running API.

Sources:
- [Pact Documentation](https://docs.pact.io/) — official Pact framework documentation
- [Consumer-Driven Contract Testing with Pact — RisingStack](https://blog.risingstack.com/consumer-driven-contract-testing-with-pact/) — practical introduction
- [pact-js on GitHub](https://github.com/pact-foundation/pact-js) — reference implementation and examples
- [Contract Testing with HTTPX — FastAPI Expert](https://fastapiexpert.com/blog/2022/11/03/contract-testing-with-httpx/) — FastAPI-specific contract testing approach

---

### 1.8 Knowledge Gaps

The following areas were searched but evidence was insufficient or contradictory:

1. **Performance regression testing integrated with functional tests**: Several tools (k6, Locust, JMeter) exist for load testing but their integration with pytest-based functional test suites for fast CI feedback is poorly documented. Low confidence in any specific recommendation.

2. **LibreOffice-specific testing patterns**: Testing PDF generation quality (not just status codes) — e.g., asserting that placeholder text was correctly replaced in the output PDF — requires PDF parsing libraries. Searched but found no established pattern specifically for pytest + LibreOffice + PDF content assertion. This is a project-specific knowledge gap.

3. **Mutation testing against live APIs**: Whether mutation testing (the project already uses cosmic-ray) can be extended to integration/smoke tests against a running service is undocumented in mainstream sources.

---

## 2. Tool Comparison

| Tool | Category | Language | Live Server Required | Setup Effort | Best For |
|------|----------|----------|---------------------|--------------|----------|
| FastAPI TestClient | Integration testing | Python | No (in-process) | Minimal | Fast integration tests in CI |
| httpx.AsyncClient | Async integration | Python | No (via ASGITransport) | Low | Async endpoint testing |
| httpx (direct) | Smoke / manual | Python | Yes | Minimal | Smoke tests against running process |
| curl | Manual HTTP | Any | Yes | None (pre-installed) | CI scripting, quick checks |
| HTTPie | Manual HTTP | Any | Yes | Low (pip/brew) | Interactive exploration |
| Bruno | GUI client | Any | Yes | Low | API exploration, git-versioned collections |
| Postman | GUI client | Any | Yes | Medium | Team collaboration, API documentation |
| FastAPI /docs | Built-in UI | Any | Yes | None (auto-generated) | Quick exploration, stakeholder demos |
| Playwright (Python) | E2E browser | Python | Yes | Medium | UI workflows, file download tests |
| Cypress | E2E browser | JS/TS only | Yes | Medium | JS frontend applications |
| Pact | Contract testing | Python/JS/Go | No (mock server) | High | Multi-consumer API compatibility |
| schemathesis | Property-based API | Python | Yes | Low | Auto-generated tests from OpenAPI spec |

---

## 3. Recommendations by Use Case

### 3.1 Day-to-Day Development (Fastest Feedback Loop)

**Recommended: FastAPI TestClient + pytest**

Run integration tests against the ASGI app directly. No server startup time. Full HTTP request/response cycle including middleware, routing, and validation.

```bash
# Run integration tests (no server needed)
pytest tests/integration/ -v

# Run with coverage
pytest tests/integration/ --cov=app --cov-report=term-missing
```

For quick interactive probing while the server is running:

```bash
# Start server in one terminal
uvicorn app.main:app --reload --port 8000

# Test in another terminal (HTTPie — readable output)
http POST localhost:8000/vouchers/generate template_id=airport-transfer-v2 booking_id=BK-2026-00001

# Or curl (scriptable)
curl -X POST http://localhost:8000/vouchers/generate \
  -H "Content-Type: application/json" \
  -d '{"template_id": "airport-transfer-v2", "booking_id": "BK-2026-00001"}'
```

Use FastAPI's auto-generated `/docs` (Swagger UI) for exploring the full API shape with an interactive browser interface.

---

### 3.2 CI/CD Integration Tests

**Recommended: pytest with httpx.AsyncClient (in-process) for bulk tests + shell-based smoke test post-deployment**

```yaml
# Example GitHub Actions step
- name: Run integration tests
  run: pytest tests/integration/ -v --tb=short

- name: Start server and run smoke tests
  run: |
    uvicorn app.main:app --port 8000 &
    sleep 3
    pytest tests/smoke/ -v
    kill %1
```

---

### 3.3 After Each Deployment (Smoke Tests)

**Recommended: pytest smoke suite using httpx against the real process**

Create `tests/smoke/` with minimal, fast tests that verify the application is alive and its critical path works end-to-end. These tests run against the actual deployed URL.

```python
# tests/smoke/conftest.py
import os
import pytest

@pytest.fixture(scope="session")
def base_url():
    return os.environ.get("SMOKE_TEST_URL", "http://localhost:8000")

# tests/smoke/test_smoke.py
import httpx

def test_health_returns_200(base_url):
    r = httpx.get(f"{base_url}/health")
    assert r.status_code == 200

def test_health_reports_healthy(base_url):
    r = httpx.get(f"{base_url}/health")
    assert r.json()["status"] == "healthy"

def test_openapi_schema_accessible(base_url):
    r = httpx.get(f"{base_url}/openapi.json")
    assert r.status_code == 200
    assert "paths" in r.json()
```

---

### 3.4 API Exploration and Documentation Sharing

**Recommended: FastAPI built-in `/docs` for quick demos + Bruno for versioned collections**

- Share `/docs` URL with stakeholders for interactive API exploration
- Commit Bruno collection files alongside source code so the team shares a single source of truth for example requests
- Bruno collections live in the repository — no cloud account needed, works offline

---

### 3.5 When Testing Against a Real Running Server is Necessary

**Use httpx directly** (the project already uses it) for out-of-process testing. This is appropriate for:
- Verifying startup/shutdown lifespan events work correctly
- Testing with real environment variables and configuration
- Validating the LibreOffice process integration works in the actual deployment environment
- Integration tests that must use real file storage (not mocked)

```python
# tests/live/test_live_server.py
# Requires a running server: uvicorn app.main:app --port 8000
import httpx
import os

BASE_URL = os.environ.get("TEST_SERVER_URL", "http://localhost:8000")

def test_full_voucher_generation_round_trip():
    with httpx.Client(timeout=30.0) as client:
        response = client.post(f"{BASE_URL}/vouchers/generate", json={
            "template_id": "airport-transfer-v2",
            "booking_id": "BK-2026-00042",
            "service_date": "2026-03-15",
            "customer": {"name": "Test Customer"},
            "service": {"type": "airport-transfer"}
        })
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert len(response.content) > 1000  # Non-empty PDF
```

---

## 4. Implementation Priority for This Project

Given the Python/FastAPI stack with pytest + httpx already in the technology stack, the recommended implementation order is:

**Priority 1 — Immediate (zero new dependencies):**
- Add `/health` endpoint to the FastAPI application
- Write smoke test suite in `tests/smoke/` using `httpx` (already a dependency)
- Use `FastAPI TestClient` for integration tests that don't need a live server

**Priority 2 — Short-term (one new tool):**
- Install HTTPie (`pip install httpie`) for interactive development use
- Add Bruno collection files to the repository (`/bruno/` directory at project root)
- Integrate smoke tests into CI after each deployment step

**Priority 3 — When needed (conditional on project evolution):**
- Playwright (Python) if a web UI is added
- Pact contract testing if the API gains multiple independent consumers
- schemathesis for property-based testing from the OpenAPI schema

---

## Sources

### Official Documentation

- [FastAPI Testing Tutorial](https://fastapi.tiangolo.com/tutorial/testing/) — canonical guide to TestClient
- [FastAPI Async Tests](https://fastapi.tiangolo.com/advanced/async-tests/) — AsyncClient with ASGITransport
- [Pact Documentation](https://docs.pact.io/) — contract testing framework
- [Health Endpoint Monitoring Pattern — Microsoft Azure Architecture Center](https://learn.microsoft.com/en-us/azure/architecture/patterns/health-endpoint-monitoring)
- [HTTPie Official Documentation](https://httpie.io/docs/cli/alternatives)
- [Bruno Official Documentation](https://docs.usebruno.com/testing/tests/introduction)

### Technical Articles and Guides

- [TestDriven.io — Developing and Testing an Asynchronous API with FastAPI and Pytest](https://testdriven.io/blog/fastapi-crud/)
- [Pythoneo — Testing FastAPI Applications](https://pythoneo.com/testing-fastapi-applications/)
- [Teclado — Getting Started with FastAPI Tests](https://teclado.com/fastapi-101/getting-started-with-fastapi-tests/)
- [HTTPie vs cURL — Yuri Kan](https://yrkan.com/blog/httpie-curl-cli-testing/)
- [curlie — rs/curlie GitHub](https://github.com/rs/curlie)
- [StackShare — curl vs HTTPie](https://stackshare.io/stackups/curl-vs-httpie)

### Smoke and Health Check Resources

- [CircleCI — Smoke Testing in CI/CD Pipelines](https://circleci.com/blog/smoke-tests-in-cicd-pipelines/)
- [microservices.io — Health Check API Pattern](https://microservices.io/patterns/observability/health-check-api.html)
- [APIdog — API Smoke Testing Methods](https://apidog.com/blog/api-testing-method-smoke-tests/)
- [Assertible — Automated Smoke Tests for REST APIs](https://assertible.com/blog/set-up-automated-smoke-tests-for-a-rest-api-in-5-minutes)

### E2E Testing Resources

- [BrowserStack — Playwright vs Cypress](https://www.browserstack.com/guide/playwright-vs-cypress)
- [Katalon — Playwright vs Cypress 2025](https://katalon.com/resources-center/blog/playwright-vs-cypress)
- [ResearchGate — Comparative Analysis of Cypress and Playwright](https://www.researchgate.net/publication/396039934_Comparative_analysis_of_Cypress_and_Playwright_frameworks_in_end-to-end_testing_for_applications_based_on_Angular)

### API Client Tools

- [Bruno — usebruno.com](https://www.usebruno.com/)
- [Git Tower Blog — Bruno: API Client Using Git](https://www.git-tower.com/blog/bruno-api-client-using-git)
- [StackHawk — Top 10 API Tools for Testing in 2025](https://www.stackhawk.com/blog/top-10-api-tools-for-testing-in-2025/)

### Contract Testing

- [RisingStack — Consumer-Driven Contract Testing with Pact](https://blog.risingstack.com/consumer-driven-contract-testing-with-pact/)
- [pact-js — GitHub](https://github.com/pact-foundation/pact-js)
- [FastAPI Expert — Contract Testing with HTTPX](https://fastapiexpert.com/blog/2022/11/03/contract-testing-with-httpx/)

---

*Research produced by Nova (nw-researcher). Evidence ratings: High = 3+ independent sources, Medium = 2 sources, Low = 1 source or inference. Output path: `docs/research/testing-running-applications-research.md`.*
