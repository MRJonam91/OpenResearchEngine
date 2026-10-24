# SourcePilot 1.0 architecture / Architettura

## Implementazione attuale

Applicazione locale Python 3.11–3.14 con FastAPI, SQLite FTS5 e interfaccia HTML/CSS/JavaScript senza build frontend. CLI e web API condividono i servizi. Gli originali sono conservati per hash; le versioni e i passaggi restano stabili. Ollama è opzionale e configurato esplicitamente sul loopback. Backup e ripristino conservano database, originali e checksum.

## Current implementation

Python 3.11–3.14, FastAPI/Uvicorn, SQLite FTS5, and vanilla HTML/CSS/JavaScript. The CLI and web API adapt shared services. There is no frontend build pipeline, external database, or mandatory model service.

| Module | Responsibility |
| --- | --- |
| `network.py`, `ingest.py` | Pinned public HTTP targets and bounded TXT/MD/HTML/PDF/DOCX extraction |
| `store.py` | SQLite schema/migration, immutable source objects, versions and passages |
| `research.py` | FTS5 retrieval, comparison, human claim/evidence changes and review history |
| `ollama.py`, `ai.py` | Loopback model capability checks, model-specific embeddings, validated proposals and execution provenance |
| `maintenance.py` | Integrity checks, consistent ZIP backup and validated restore |
| `report.py` | Reviewed Markdown/PDF reports with full source identities |
| `schemas.py`, `http_limits.py`, `api.py`, `ai_api.py`, `__main__.py` | Bounded request contracts and web/CLI adapters |

## Guiding constraints

The MVP must make evidence inspectable, preserve imported artifacts, and keep automated suggestions separate from reviewer decisions. A system may use language models, embeddings, OCR, or parsers, but none of these may erase the original source or silently turn a proposal into an accepted Claim.

## Logical flow

```text
Source import
  -> provenance capture and immutable Source Version
  -> bounded parsing / normalization
  -> locatable Passages
  -> FTS5 / optional local embedding retrieval
  -> manual claims / optional validated model proposals
  -> reviewer decisions and Report export
```

## Bounded components

| Component | Responsibility | Must retain |
| --- | --- | --- |
| Ingestion | Fetch or receive a Source and create its Source Version | origin, import time, fingerprint, original artifact when permitted |
| Extraction | Convert a version into searchable, locatable Passages | page/line/paragraph/table locators |
| Retrieval | Return relevant Passages for a question | ranking method and query context |
| Analysis | Propose Claims, Evidence Links, and Contradiction Assessments | model/prompt/version metadata and cited inputs |
| Review | Capture human acceptance, edits, rejection, and uncertainty | previous state, timestamp, rationale where supplied |
| Reporting | Render a Report from reviewed data | citation locators and export version |
| Interfaces | Expose the workflow through API, CLI, and web UI | stable identifiers and structured errors |

## Data invariants

- A Citation must resolve to one or more Passages from identified Source Versions.
- A Reported Claim must show whether it is proposed, reviewed, disputed, or unresolved.
- Reprocessing produces a new derived result; it does not overwrite a Source Version or reviewer decision.
- Each automated result records enough configuration to understand how it was produced.
- Deleting a workspace must define the fate of retained originals, derived text, indices, and exports.

## Storage and compatibility

Schema version 3 extends existing alpha/beta tables additively. SQLite connections enable foreign keys and commit/rollback per operation. Originals resolve relative to the workspace, independent of old absolute metadata paths, and are verified against their full hash before download/backup. Backups snapshot SQLite and carry a checked manifest; restore creates a new destination.

Embeddings are normalized JSON vectors cached by immutable passage and provider/model/digest identity. Retrieval scans the current vectors in process; this is intended for personal corpora, not a large hosted vector service. Analysis contexts are bounded, coverage is explicit, citations are checked before persistence, and accepted proposals remain unreviewed claims. Reports retain AI draft provenance after human editing.

## Boundaries / Confini

The server is single-user and binds to loopback. Per-run write tokens, Host/Origin checks, request limits and browser security headers protect the local interface; OS permissions protect plaintext workspace files. URL redirects are revalidated and connections use the validated numeric IP with TLS hostname verification. Models cannot invoke tools, fetch URLs, or approve claims.

Il server è monoutente e locale; i permessi del sistema operativo proteggono i dati in chiaro. Il modello propone, la persona accetta e revisiona. OCR, esecuzioni in background, account e hosting condiviso richiedono nuovi confini e controlli: vedi [roadmap](ROADMAP.md).
