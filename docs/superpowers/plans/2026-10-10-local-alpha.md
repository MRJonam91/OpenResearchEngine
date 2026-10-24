# Local Alpha Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver a local web app and CLI that import sources, search passages, review cited claims, and export a verifiable Markdown report.

**Architecture:** A Python domain service owns SQLite and immutable source objects. FastAPI and argparse are thin interfaces over that service; a static browser UI handles upload, search, review, and export. All data stays in an explicit local workspace.

**Tech Stack:** Python 3.14+, FastAPI, Uvicorn, pypdf, SQLite FTS5, vanilla HTML/CSS/JavaScript, pytest.

**Spec:** `docs/superpowers/specs/2026-10-10-local-alpha-design.md`

## Global Constraints

- Bind the server to `127.0.0.1` by default.
- Preserve original imported bytes by SHA-256 inside the workspace.
- Every citation resolves to an imported source version and passage locator.
- An AI process cannot approve claims; this alpha has no AI claim generation.
- Search is SQLite full-text, not semantic search.
- No PDF export or OCR in the alpha.

## Review Focus

- Reimport of changed bytes at one path creates a new version while old citations still point to old bytes.
- A PDF with no selectable text reports an extraction error without creating false passages.
- A malicious URL cannot use the importer to request loopback or private-network targets.
- A report does not silently include proposed or rejected claims.
- A write request from another website cannot mutate a local workspace.

---

### Task 1: Local store and import

**Files:** `pyproject.toml`, `sourcepilot/store.py`, `sourcepilot/ingest.py`, `tests/test_ingest.py`

**Interfaces:** `ResearchStore(workspace)` opens schema; `import_file(path)` and `import_bytes(name, data, origin)` return source/version summaries; `list_sources()` and `list_passages(source_id)` return plain dictionaries.

- [ ] Write tests for text import, SHA object retention, passage locators, duplicate import, changed source version, HTML text, and empty/unsupported input.
- [ ] Run `python -m pytest tests/test_ingest.py -q` and confirm feature failures.
- [ ] Implement the smallest store, extractor, and import transaction that satisfy the tests.
- [ ] Run the tests and inspect the stored originals and locators.

### Task 2: Search, review, and report

**Files:** `sourcepilot/research.py`, `sourcepilot/report.py`, `tests/test_research.py`

**Interfaces:** `search(query)`, `create_claim(text, passage_id)`, `add_evidence(claim_id, passage_id, stance)`, `review_claim(claim_id, status, note)`, `list_claims()`, and `render_report(include_proposed=False)` operate on the same store.

- [ ] Write tests for FTS results, evidence links, human review states, disputed claims, and report citation metadata.
- [ ] Run `python -m pytest tests/test_research.py -q` and confirm feature failures.
- [ ] Implement search, review, and deterministic Markdown rendering.
- [ ] Run tests, including the proposed/rejected exclusion cases.

### Task 3: Local API and CLI

**Files:** `sourcepilot/api.py`, `sourcepilot/__main__.py`, `tests/test_interfaces.py`

**Interfaces:** `create_app(workspace)` exposes JSON endpoints; `python -m sourcepilot` exposes the command set in the spec.

- [ ] Write tests for upload, source and passage listing, search, claim workflow, Markdown download, CLI round trip, and unauthorized writes.
- [ ] Run `python -m pytest tests/test_interfaces.py -q` and confirm feature failures.
- [ ] Implement the API and CLI as thin service adapters with stable error messages.
- [ ] Run tests and a direct CLI round trip.

### Task 4: Browser UI and final verification

**Files:** `sourcepilot/static/index.html`, `sourcepilot/static/app.css`, `sourcepilot/static/app.js`, `README.md`, `docs/ALPHA.md`

**Interfaces:** Browser UI calls the local API and displays import, search, review, evidence, and export states.

- [ ] Build the Swiss grid interface and real empty states; support file and folder pickers.
- [ ] Add interactions for imports, search, claim creation, evidence linking, review, and report download.
- [ ] Run the full pytest suite and one browser smoke test with a real local server.
- [ ] Update setup, run, limitations, and data location instructions; run `git diff --check`.
