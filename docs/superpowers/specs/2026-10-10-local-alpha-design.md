# Local alpha design

## Intent and success

Build a usable local research workspace for a person who wants to inspect evidence while drafting a cited report. The alpha succeeds when a user can start one local server, import a file or folder, find passages, create and review a claim with evidence on either side, and export Markdown whose citations identify the exact imported source version and passage locator. A CLI offers the same core workflow for automation.

## Scope

The alpha accepts UTF-8 text, Markdown, HTML, and text PDFs from browser uploads or local CLI paths. It also accepts one HTTP or HTTPS URL at a time for HTML or plain text with explicit size and timeout limits. The web UI provides folder selection through the browser file picker; the browser uploads selected files into the chosen local workspace. The CLI reads local paths directly. Imported originals are stored by SHA-256 in the workspace, so later changes to source files do not change an existing citation.

The alpha uses local full-text search with SQLite FTS5. It does not claim semantic retrieval. Claims and evidence links are entered by the user; the system does not generate claims or declare contradictions automatically. A claim with both supporting and challenging passages is shown as disputed for review. PDF export, OCR, authentication, collaboration, and external model integration are outside this alpha.

## Architecture and interfaces

Python 3.14 or newer runs a FastAPI application with a bundled static web UI and a shared domain service. SQLite stores metadata, passages, claim review state, and an FTS5 index. `pypdf` extracts text from PDFs. The CLI calls the same service functions as the API rather than making HTTP requests. The server binds to `127.0.0.1` by default; the UI's write requests carry a per-process token so unrelated web pages cannot submit local writes.

The server is started with `python -m sourcepilot serve --workspace PATH`. The CLI also supports `import PATH`, `import-url URL`, `search QUERY`, `claim TEXT --passage ID`, `review ID --status ...`, `evidence CLAIM_ID PASSAGE_ID --stance ...`, and `report --output PATH`. The API exposes corresponding JSON endpoints. The browser uses file and directory pickers, shows import failures per item, searches passages, attaches them to claims, and opens source context beside the claim under review.

## Data model and invariants

- `source`: origin kind and locator, human-readable title, creation time.
- `source_version`: source ID, SHA-256, import time, object path, MIME type, extraction status, extraction error.
- `passage`: version ID, order, locator, extracted text.
- `claim`: statement, review state (`proposed`, `approved`, `rejected`, `uncertain`), note, timestamps.
- `evidence_link`: claim ID, passage ID, stance (`supports`, `challenges`, `context`), unique per claim and passage.

Every citation resolves to a passage, source version, and source. Reimporting unchanged bytes at the same origin reuses the version; changed bytes create a new version. Extraction never mutates an existing version. A report includes approved and uncertain claims by default, excludes rejected and proposed claims, and labels uncertainty and challenging evidence. A user can opt to include proposed claims with explicit labels. Reports show a stable local citation ID, source title, origin, import date, SHA-256 prefix, and locator. The report is written to an explicit path; export does not silently overwrite an existing file.

## Data flow and errors

The ingestion layer validates type and size, computes SHA-256, stores the original object, extracts passages, and commits records in SQLite. Failed files are returned as individual errors, and other imports continue. Empty or image-only PDFs receive a clear `no extractable text` error. URL imports reject non-HTTP schemes, non-HTML/text content, oversized responses, and redirects to private or loopback network addresses. The browser shows these errors without changing prior sources.

Search returns excerpts and citation metadata. Claim review is a human action with a timestamp. The report renderer reads committed data and escapes Markdown-sensitive values in source metadata. The application does not infer truth from the existence of a citation.

## Testing and acceptance

Integration tests use temporary workspaces and real SQLite to cover: import/versioning, locators, search, claim/evidence review, report citations, duplicate import, unsupported or empty files, unsafe URL schemes, and API write protection. One browser smoke test checks the import/search/review/export path with a small fixture. A documented manual run starts the server and verifies that a report citation can be traced back to the original imported file.

## Visual direction

The UI uses a Swiss grid: white and neutral surfaces, one blue accent, sans-serif typography, hairline rules, and left-aligned content. Its signature interaction is a two-column review view where selecting a claim keeps the cited passage visible beside its review controls. Labels describe actual source and claim state; empty states avoid invented sample data.
