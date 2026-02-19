# Root Cause Analysis: No Easy Way to Start the FastAPI Service

**Date:** 2026-02-19
**Analyst:** Rex (nw-troubleshooter)
**Methodology:** Toyota 5 Whys, multi-causal
**Project:** template-merger / voucher-merger service
**Location:** `/Users/chris/Dev/learning/template-merger`

---

## Problem Statement

There is no easy way for a developer to start the FastAPI service locally. A developer cloning this repository has no documented, single-command path to run the application. They must independently discover the PYTHONPATH requirement, the factory-function uvicorn invocation pattern, and the correct module path — none of which are captured anywhere in the project.

**Observable impact:** A new developer cannot run the service without reverse-engineering the project structure.

**Scope boundary:** This analysis covers the local developer experience of starting the service. It excludes CI/CD pipelines, production deployment, and the existing test infrastructure (which uses FastAPI `TestClient` in-process and does not require the server to start).

---

## Evidence Gathered

Evidence collected by reading project files directly. Each item includes its source.

### E1 — No Makefile
- **Source:** `Glob /Users/chris/Dev/learning/template-merger/Makefile` — no files found
- **Finding:** No Makefile exists. No `make run`, `make dev`, or `make start` targets available.

### E2 — No scripts/ directory
- **Source:** `Glob /Users/chris/Dev/learning/template-merger/scripts/**/*` — no files found
- **Finding:** No shell scripts exist. No `run.sh`, `start-dev.sh`, or equivalent.

### E3 — No docker-compose file
- **Source:** `Glob /Users/chris/Dev/learning/template-merger/docker-compose*` — no files found
- **Finding:** No containerised local development path exists.

### E4 — No root-level README
- **Source:** `Glob /Users/chris/Dev/learning/template-merger/README*` — no root README found
- **Finding:** No `README.md` at the project root. The only README files are inside `docs/adrs/`, `docs/design/`, and `.pytest_cache/` — none of which document how to start the service.
- **Corroborating evidence:** `pyproject.toml` line 9 contains `# readme = "README.md"  # Uncomment when README exists` — this is an explicit acknowledgement that the README is absent.

### E5 — No [project.scripts] in pyproject.toml
- **Source:** `/Users/chris/Dev/learning/template-merger/pyproject.toml` (full read)
- **Finding:** The `[project]` section contains no `[project.scripts]` table. No `voucher-merger-start` or equivalent CLI entry point is defined. Running `pip install -e .` would create no executable.

### E6 — No hatch environment with run commands
- **Source:** `/Users/chris/Dev/learning/template-merger/pyproject.toml` (full read)
- **Finding:** No `[tool.hatch.envs]` section exists. The hatch configuration is limited to `[tool.hatch.build.targets.wheel]`. There is no `hatch run serve` or equivalent command defined.

### E7 — Application uses a factory function, not a module-level app instance
- **Source:** `/Users/chris/Dev/learning/template-merger/src/main/voucher_merger/main.py`
- **Finding:** The module exposes `create_app()` (a factory function with optional dependency injection parameters). There is no module-level `app = create_app()` instance. There is no `if __name__ == "__main__"` block.
- **Consequence:** The standard uvicorn invocation `uvicorn voucher_merger.main:app` fails because `app` does not exist as a module attribute. The correct pattern requires the `--factory` flag: `uvicorn voucher_merger.main:create_app --factory`.

### E8 — Non-standard source layout requires PYTHONPATH manipulation
- **Source:** `/Users/chris/Dev/learning/template-merger/pyproject.toml`, line 34: `packages = ["src/main/voucher_merger"]`
- **Finding:** The package source lives at `src/main/voucher_merger/`, not at the project root. Running uvicorn from the project root without setting `PYTHONPATH=src/main` (or installing the package) causes `ModuleNotFoundError: No module named 'voucher_merger'`.

### E9 — Test infrastructure works but uses in-process client, not a live server
- **Source:** `/Users/chris/Dev/learning/template-merger/src/tests/acceptance/voucher_generation/steps/conftest.py`, lines 279–312
- **Finding:** The `app` fixture has a `TODO` comment and currently returns `None`. The `client` fixture falls back to `MockTestClient` which returns HTTP 501 for all requests. The acceptance tests do not require or test a running server. The test path does not document the server start command either.

### E10 — No .env.example or environment variable documentation
- **Source:** `Glob /Users/chris/Dev/learning/template-merger/.env*` — no files found
- **Finding:** No `.env.example` file exists. If any environment variables are required to start the service, they are undocumented.

### E11 — walking-skeleton.md lists "uvicorn server running" as unchecked
- **Source:** `/Users/chris/Dev/learning/template-merger/docs/distill/walking-skeleton.md`, line 157: `- [ ] uvicorn server running`
- **Finding:** The walking skeleton implementation checklist explicitly marks `uvicorn server running` as incomplete. The project is in an early development phase where the server startup path was never finalised.

### E12 — Research document exists but is not linked to a startup guide
- **Source:** `/Users/chris/Dev/learning/template-merger/docs/research/testing-running-applications-research.md`
- **Finding:** The project has a detailed research document on testing a running application, including the correct uvicorn invocation `uvicorn app.main:app --reload --port 8000`. However, this research is not translated into project-specific startup instructions, and it references a generic `app.main:app` pattern that does not match this project's factory pattern.

---

## 5 Whys Analysis

The problem has three parallel causal branches. Each is followed independently to WHY level 5.

---

### Branch A: No startup command is defined

**WHY 1A:** There is no single command to start the service.
- Evidence: E1 (no Makefile), E2 (no scripts/), E5 (no project.scripts), E6 (no hatch envs)

**WHY 2A:** No startup command is defined because no developer task runner is configured.
- Evidence: pyproject.toml has no `[project.scripts]`, no `[tool.hatch.envs]`. No Makefile, no scripts directory.
- Why were none configured? Proceed to WHY 3A.

**WHY 3A:** No task runner was configured because the project was scaffolded for testing, not for running.
- Evidence: The DISTILL wave produced test infrastructure (feature files, step definitions, mock adapters). The handoff document (`docs/distill/handoff-to-deliver.md`) describes the implementation sequence in terms of TDD cycles — `pytest` commands, not server start commands. The focus was on making tests pass, not on running the service.

**WHY 4A:** The scaffolding focused on testing because the development methodology (Outside-In TDD) front-loads test infrastructure before production infrastructure.
- Evidence: `docs/distill/handoff-to-deliver.md` mandates a "one-at-a-time" TDD approach: remove `@skip`, run tests (fail), implement code, commit. The walking skeleton checklist (`E11`) shows `uvicorn server running` as an unchecked item, confirming this infrastructure was noted but not yet addressed.

**WHY 5A — Root Cause A:** No process or checklist item exists to require a developer startup path before the project leaves the DISTILL/early-DELIVER phase. The Definition of Done (`docs/distill/handoff-to-deliver.md`) has six checklist items, none of which address developer ergonomics such as "service can be started with a single documented command." The project has a DoD for individual stories but no project-level setup DoD.

---

### Branch B: The factory pattern makes the correct uvicorn invocation non-obvious

**WHY 1B:** Even a developer who knows uvicorn cannot start this service using the standard pattern.
- Evidence: E7 — `voucher_merger.main:app` fails because there is no `app` attribute. The `--factory` flag is required.

**WHY 2B:** The factory pattern was chosen to support dependency injection in tests.
- Evidence: `main.py` docstring: "This factory function allows dependency injection for testing. If no dependencies are provided, production adapters are used." The test conftest (`E9`) shows a commented-out `create_app(template_repository=..., ...)` call — confirming the factory was designed for test DI.

**WHY 3B:** The design chose test DI convenience over startup simplicity.
- Evidence: The factory signature takes four optional parameters. The `create_app()` with no arguments creates production adapters — it would work as a uvicorn factory. But no module-level `app = create_app()` alias was added, and no `__main__` block was added, leaving the run path entirely implicit.

**WHY 4B:** No design decision captured the trade-off between factory pattern and startup ergonomics.
- Evidence: `docs/adrs/ADR-002-python-fastapi.md` exists but was not read in depth. The test conftest comment (`# TODO: Import and configure the actual FastAPI app when implemented`) and the walking-skeleton checklist (`- [ ] uvicorn server running`) indicate startup was a known gap, but no ADR addresses the startup invocation pattern.

**WHY 5B — Root Cause B:** The application factory pattern was implemented without a companion startup alias or documented invocation pattern. The design decision to use a factory function (valid for DI) was never completed with the complementary decision of how the service is actually started outside of tests.

---

### Branch C: No documentation captures the PYTHONPATH requirement or module path

**WHY 1C:** A developer does not know to set `PYTHONPATH=src/main` before invoking uvicorn.
- Evidence: E8 — the package is at `src/main/voucher_merger/`, requiring `PYTHONPATH` or `pip install -e .` for module resolution. E4 — no README exists.

**WHY 2C:** No documentation captures the PYTHONPATH requirement because no root README was written.
- Evidence: `pyproject.toml` line 9 explicitly comments out `# readme = "README.md"  # Uncomment when README exists`, confirming the README is a known absence, not an oversight.

**WHY 3C:** The README was deferred because the project is in an early development phase where implementation was prioritised.
- Evidence: The DISTILL-to-DELIVER handoff (`E11`) describes a phase-gated methodology. The DISTILL wave produced design and test scaffolding. The DELIVER wave is expected to implement code. Documentation of the running application was not assigned to either wave explicitly.

**WHY 4C:** Neither the DISTILL wave deliverables nor the DELIVER wave Definition of Done includes a requirement for a developer-facing startup guide.
- Evidence: `docs/distill/handoff-to-deliver.md` DoD checklist (lines 207–213) contains six items: acceptance scenarios, unit tests, no hardcoded values, RFC 7807 errors, correlation ID logging, no PII in logs. None address "developer can start the service."

**WHY 5C — Root Cause C:** The project's Definition of Done and wave deliverable checklists contain no requirement for developer ergonomics documentation (README, startup instructions, environment setup). This category of work is not owned by any phase of the current methodology, so it accumulates as undone.

---

## Root Causes Identified

Three independent root causes, all contributing to the same symptom:

| ID | Root Cause | Branch |
|----|-----------|--------|
| RC-A | No project-level setup Definition of Done exists. The DoD covers story-level quality but not "developer can run the service." | A |
| RC-B | The application factory pattern was implemented without a companion startup alias (`app = create_app()` at module level) or a `__main__` block, leaving the uvicorn invocation path entirely implicit and requiring knowledge of the `--factory` flag. | B |
| RC-C | Developer ergonomics documentation (README, startup instructions) is not owned by any phase in the current DISTILL/DELIVER methodology. Neither wave's deliverable checklist includes it. | C |

These root causes are independent: RC-A is a process gap, RC-B is a code design gap, RC-C is a documentation ownership gap. All three must be addressed to fully resolve the problem.

---

## Proposed Solutions

Solutions are categorised as **Immediate** (restore developer ability to start the service now) or **Permanent** (prevent recurrence in future features/projects).

---

### Solution 1 — Add a module-level app alias to main.py [Immediate, addresses RC-B]

**What:** Add `app = create_app()` at the bottom of `main.py`, below the factory function.

**Why it works:** This makes the standard uvicorn invocation work: `uvicorn voucher_merger.main:app --reload`. It does not break the factory pattern — tests still call `create_app(template_repository=..., ...)` for DI. The `app` alias is just a convenience for the production startup path.

**Optionally also add a `__main__` block:**
```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("voucher_merger.main:app", host="0.0.0.0", port=8000, reload=True)
```
This allows `python -m voucher_merger.main` as an alternative start method.

**File to modify:** `/Users/chris/Dev/learning/template-merger/src/main/voucher_merger/main.py`

**Implementation detail:** Add after the closing of `create_app()`:
```python
# Module-level app instance for uvicorn and tooling that expects `module:app`.
# For dependency injection (e.g. tests), call create_app() directly.
app = create_app()
```

---

### Solution 2 — Add a [project.scripts] entry to pyproject.toml [Immediate, addresses RC-A + RC-B]

**What:** Add a `[project.scripts]` table to `pyproject.toml` defining a `voucher-merger-start` entry point.

**Why it works:** After `pip install -e .`, developers (and CI) can run `voucher-merger-start` without knowing the uvicorn module path or PYTHONPATH setup.

**File to modify:** `/Users/chris/Dev/learning/template-merger/pyproject.toml`

**Implementation detail:**
```toml
[project.scripts]
voucher-merger-start = "uvicorn.main:main"
```

Note: The simpler and more conventional approach for FastAPI services is to expose the app via Solution 1 and document the uvicorn invocation in a Makefile or README rather than wrapping uvicorn's CLI, because uvicorn's CLI options (port, reload, log level) need to be configurable. A `[project.scripts]` entry for the service itself is most useful as a production entry point; for development, a Makefile target is more ergonomic.

---

### Solution 3 — Add a Makefile with dev targets [Immediate, addresses RC-A + RC-C]

**What:** Create `/Users/chris/Dev/learning/template-merger/Makefile` with standard development targets.

**Why it works:** A Makefile provides a single discoverable location for all developer tasks. It captures the PYTHONPATH setup, the uvicorn invocation pattern, and the test commands in one place.

**Implementation detail:**
```makefile
.PHONY: run dev test lint typecheck install

PYTHONPATH := src/main
MODULE := voucher_merger.main:app

install:
	pip install -e ".[dev]"

run:
	PYTHONPATH=$(PYTHONPATH) uvicorn $(MODULE) --host 0.0.0.0 --port 8000

dev:
	PYTHONPATH=$(PYTHONPATH) uvicorn $(MODULE) --host 0.0.0.0 --port 8000 --reload

test:
	PYTHONPATH=$(PYTHONPATH) pytest src/tests/ -v

lint:
	ruff check src/

typecheck:
	mypy src/main/
```

Note: If Solution 1 is also implemented (module-level `app` alias), the Makefile does not require `PYTHONPATH` when the package is installed via `pip install -e .`.

---

### Solution 4 — Add a root README.md [Immediate, addresses RC-C]

**What:** Create `/Users/chris/Dev/learning/template-merger/README.md` documenting how to install, configure, and start the service.

**Minimum viable content:**
- Prerequisites (Python version, LibreOffice headless)
- Installation: `pip install -e ".[dev]"`
- Starting the server: the exact uvicorn command with PYTHONPATH
- Running tests: the exact pytest command
- API exploration: `http://localhost:8000/docs` (FastAPI auto-generated Swagger UI)

**Why it works:** Directly addresses RC-C by giving the documentation a home and an owner (the project itself, committed alongside the code).

---

### Solution 5 — Add developer ergonomics to the Definition of Done [Permanent, addresses RC-A + RC-C]

**What:** Update the project DoD (in `docs/distill/handoff-to-deliver.md` or a dedicated project standards document) to include:

```
- [ ] Service can be started with a single documented command from a clean checkout
- [ ] README.md exists at project root with setup and start instructions
- [ ] All required environment variables are documented in .env.example
```

**Why it works:** Addresses RC-A at its root. Every future feature or project phase that goes through this checklist will be blocked from "done" status until developer ergonomics are in place. This prevents the current situation from recurring.

**File to modify:** `/Users/chris/Dev/learning/template-merger/docs/distill/handoff-to-deliver.md`

---

### Solution 6 — Activate the app fixture in conftest.py [Permanent, addresses RC-B]

**What:** The acceptance test conftest has a TODO (line 287–296) that comments out the `create_app()` call. Once Solution 1 (module-level `app` alias) is in place, activate this fixture so acceptance tests use the real app.

**Why it works:** When the acceptance test `client` fixture uses the real app via `FastAPI TestClient`, the test suite validates that the application can actually be instantiated — providing a regression signal if the startup path breaks.

**File to modify:** `/Users/chris/Dev/learning/template-merger/src/tests/acceptance/voucher_generation/steps/conftest.py`

---

## Backward Validation

Each root cause is validated by tracing forward: "If this root cause exists, does it produce the observed symptom?"

### Validation of RC-A (No project-level setup DoD)

Forward chain: No setup DoD -> developer ergonomics are never required -> no Makefile, no startup command is created -> developer cannot start service with a single command.

Verification: The project has been through at least two waves (DISTILL, partial DELIVER) and across multiple commits (7a1c117 and earlier). No Makefile or startup script has been created in any of them. This is consistent with the absence of a process requirement. RC-A validates.

### Validation of RC-B (Factory without startup alias)

Forward chain: Factory pattern chosen for DI -> no `app` module attribute added -> standard `uvicorn module:app` fails -> developer must know `--factory` flag or factory invocation pattern -> non-obvious start command.

Verification: `main.py` confirmed to have `create_app()` and no `app = ...` at module level and no `__main__` block. `uvicorn voucher_merger.main:app` would raise `AttributeError`. RC-B validates.

### Validation of RC-C (Documentation not owned by any phase)

Forward chain: No phase owns startup documentation -> handoff document DoD has no documentation requirement -> DELIVER wave implements code without writing a README -> no README exists at project root -> developer has no reference for the startup command.

Verification: `pyproject.toml` line 9 explicitly comments out the readme field ("Uncomment when README exists"), confirming README creation was deferred deliberately, not forgotten accidentally. The DoD checklist in `handoff-to-deliver.md` contains zero documentation items. RC-C validates.

### Cross-validation: Do the three root causes contradict each other?

No. RC-A (process), RC-B (code design), and RC-C (documentation ownership) operate at different levels of the system. Fixing only RC-B (adding the `app` alias) still leaves no documented invocation path (RC-C) and no process to prevent recurrence (RC-A). All three must be addressed for a complete resolution.

### Completeness check: Do the root causes collectively explain all observed symptoms?

Symptom 1 — No single command to start the service: explained by RC-A (no task runner configured) + RC-C (no README to document an ad-hoc command).

Symptom 2 — Standard uvicorn invocation fails: explained by RC-B (factory pattern without alias).

Symptom 3 — PYTHONPATH requirement is undiscoverable: explained by RC-C (no README) + RC-A (non-standard layout not compensated by tooling).

All three symptoms are accounted for. No unexplained symptoms remain.

---

## Recommended Next Steps (Priority Ordered)

### Priority 1 — Unblock developers today (30 minutes of effort)

1. **Implement Solution 1:** Add `app = create_app()` to the bottom of `main.py`. This immediately enables `PYTHONPATH=src/main uvicorn voucher_merger.main:app --reload` and fixes the factory attribute gap.

2. **Implement Solution 3:** Create a `Makefile` with `make dev` (wraps the uvicorn command with PYTHONPATH) and `make test`. This gives developers a single discoverable entry point without any installation step.

### Priority 2 — Make the service self-documenting (1–2 hours of effort)

3. **Implement Solution 4:** Write a root `README.md`. Minimum viable content: prerequisites, `pip install -e ".[dev]"`, `make dev` or the raw uvicorn command, `make test`, and a link to `http://localhost:8000/docs`.

4. **Uncomment `pyproject.toml` line 9:** Set `readme = "README.md"` once the README exists, so tooling (PyPI, hatch, IDEs) picks it up.

### Priority 3 — Prevent recurrence (30 minutes of effort)

5. **Implement Solution 5:** Add developer ergonomics items to the project Definition of Done. The three checklist items above ensure that future waves of development cannot complete without a working startup path.

6. **Implement Solution 6:** Activate the `app` fixture in `conftest.py` once `create_app()` is working end-to-end. This creates an automated regression signal for the startup path within the existing test suite.

---

*Analysis produced by Rex (nw-troubleshooter) using Toyota 5 Whys methodology. Evidence gathered from direct file reads on 2026-02-19. All findings are traceable to specific file locations and line numbers cited above.*
