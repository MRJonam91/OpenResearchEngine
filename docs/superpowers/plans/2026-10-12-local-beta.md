# Local Beta Implementation Plan

Historical implementation record: code completed in `a46aa1d` with 33 passing tests, local browser/PDF checks. Beta publication was superseded by the [1.0 release plan](2026-10-24-v1.md); no standalone beta release is claimed.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Release SourcePilot `0.2.0b1` with source history, correctable evidence, document comparison, PDF export, and verified local security.

**Architecture:** Extend the current SQLite service behind the existing API and CLI. Add one additive migration, expose history and comparison as read APIs, and keep PDF rendering separate from Markdown rendering while consuming the same claim objects.

**Tech Stack:** Python 3.14+, SQLite FTS5, FastAPI, pypdf, reportlab, vanilla HTML/CSS/JavaScript, pytest.

**Spec:** `docs/superpowers/specs/2026-10-12-local-beta-design.md`

## Global Constraints

- Preserve alpha workspace IDs and original objects.
- Keep server default binding to `127.0.0.1`.
- Never serve imported HTML inline on the app origin.
- Do not label full-text search as semantic search.
- Do not automatically approve claims or declare contradictions.

## Review Focus

- An old cited passage stays readable after a newer source version is imported.
- Statement edits clear prior approval and record the previous statement.
- The final evidence link cannot be removed.
- PDF text and citation identity agree with Markdown for Unicode claims.
- A forged Host or Origin header cannot read the write token or mutate data.

---

### Task 1: Source version history and search semantics

**Files:** `sourcepilot/store.py`, `sourcepilot/research.py`, `sourcepilot/api.py`, `sourcepilot/__main__.py`, `tests/test_history.py`.

- [x] Write failing tests for version listing, original download, latest search, history search, and alpha database migration.
- [x] Implement additive schema versioning and service/API/CLI interfaces.
- [x] Run history tests and the full suite.

### Task 2: Correctable claims and evidence

**Files:** `sourcepilot/store.py`, `sourcepilot/research.py`, `sourcepilot/api.py`, `sourcepilot/__main__.py`, `tests/test_revisions.py`.

- [x] Write failing tests for statement editing, revision history, stance changes, evidence removal, and last-link protection.
- [x] Implement service/API/CLI interfaces and validate ID ownership.
- [x] Run revision tests and the full suite.

### Task 3: Comparison and browser workflow

**Files:** `sourcepilot/research.py`, `sourcepilot/api.py`, `sourcepilot/static/index.html`, `sourcepilot/static/app.js`, `sourcepilot/static/app.css`, `tests/test_compare.py`.

- [x] Write failing tests for grouped comparison and invalid source selections.
- [x] Implement comparison query and browser controls for versions, compare, edit, and remove.
- [x] Verify the rendered flow in a local browser and run the full suite.

### Task 4: PDF export and release

**Files:** `sourcepilot/report.py`, `sourcepilot/api.py`, `sourcepilot/__main__.py`, `pyproject.toml`, `tests/test_pdf_report.py`, `README.md`, `docs/BETA.md`, `CHANGELOG.md`, `.github/workflows/test.yml`.

- [x] Write failing tests for PDF claim set, citation metadata, and CLI output refusal to overwrite.
- [x] Implement PDF rendering with reportlab and expose API/CLI download.
- [x] Render a sample PDF to images and inspect page layout.
- [x] Run full tests, static checks, browser smoke and Git diff check; CI execution moves to 1.0.
- [x] Commit local beta; standalone publication superseded by 1.0 with remote verification required there.
