# Changelog

## 1.1.0b1 — 2026-11-07

### Italiano

- **Cancellazione controllata**: aggiunta eliminazione sicura di fonti e affermazioni via UI, API REST (`DELETE /api/sources/{id}`, `DELETE /api/claims/{id}`) e CLI (`delete-source`, `delete-claim`). Protezione referenziale con rifiuto della cancellazione se una fonte ha passaggi usati in affermazioni attive.
- **Esportazione JSON**: aggiunto formato strutturato JSON per report di ricerca verificabili (`/api/report.json` e `sourcepilot report --format json`), oltre a Markdown e PDF.
- **Ingestione CSV e TSV**: supporto diretto per importazione di file tabellari delimitati con locatori di riga tracciabili.
- **Ottimizzazioni query e filtri**: eliminato overhead di connessioni multiple in `list_claims`, aggiunto filtro per stato di revisione via API (`?status=...`) e CLI (`sourcepilot claims --status ...`), e aggiunto indice `claim_status`.
- **Nuovi comandi CLI**: aggiunti `sources`, `claims`, `delete-source`, `delete-claim`.
- **Raffinamento diagnostica**: aggiunto breakdown per stato di revisione (`claim_statuses`) nei controlli di integrità del workspace.

### English

- **Controlled Deletion**: added safe deletion of sources and claims via UI, REST API (`DELETE /api/sources/{id}`, `DELETE /api/claims/{id}`), and CLI (`delete-source`, `delete-claim`). Referential safety prevents deleting sources referenced by existing claims.
- **JSON Report Export**: added structured JSON report export (`/api/report.json` and `sourcepilot report --format json`) alongside Markdown and PDF.
- **CSV & TSV Ingestion**: added direct support for delimited tabular files with locatable line passages.
- **Query Optimization & Status Filtering**: resolved connection overhead in `list_claims`, added status filtering in API and CLI, and added `claim_status` index.
- **New CLI Commands**: added `sources`, `claims`, `delete-source`, `delete-claim`.
- **Enhanced Diagnostics**: added claim status distribution breakdown (`claim_statuses`) to workspace diagnostics.

## 1.0.0 — 2026-10-24

### Italiano

- Consolidato il flusso locale web/API/CLI e supporto Python 3.11–3.14.
- Aggiunti DOCX, download PDF/DOCX da URL, connessioni HTTP a IP validati, payload tipizzati e limiti prima del parsing.
- Aggiunti diagnostica, originali portabili con verifica hash, backup/ripristino ZIP con manifest e checksum.
- Aggiunta AI Ollama locale opzionale: ricerca semantica, proposte citate, accettazione esplicita come bozza e candidati disaccordi con copertura visibile.
- Conservata la provenienza AI nei report; hash completi, licenza font PDF allegata, revisioni invalidate dopo modifiche alle prove.
- Aggiornati dipendenze, licenze, pacchetti, CI, guida e roadmap.

### English

- Stabilized the local web/API/CLI workflow and Python 3.11–3.14 support.
- Added DOCX, PDF/DOCX URL capture, pinned public HTTP targets, typed inputs, and pre-parsing request limits.
- Added integrity diagnostics, portable hash-verified originals, and checksummed ZIP backup/restore.
- Added optional local Ollama semantic retrieval, cited proposals, explicit acceptance as unreviewed claims, and candidate disagreements with accurate coverage.
- Retained AI draft provenance in reports; full hashes, attached PDF font license, and renewed review after evidence changes.
- Updated dependencies, licensing, distributions, CI, user guide, and roadmap.

## 0.2.0b1 — local beta

- Browse source versions and download retained originals; search the latest version by default or opt into history.
- Edit claims with a revision trail, change evidence stance, and remove mistaken links while retaining at least one citation.
- Compare two sources side by side using their latest indexed passages.
- Export reviewed claims as Markdown or PDF with passage and source-version metadata.
- Reject unexpected Host headers and cross-origin writes; add Windows/Linux CI.

This beta remains local and single-user. Search is SQLite full-text, not semantic; contradictions are not decided automatically.

## 0.1.0 — local alpha

- File, folder, and public URL import; SQLite full-text search; human-reviewed claims; Markdown report; local API and CLI.

## Unreleased maintenance / Manutenzione non rilasciata — 2026-11-02

- EN: Raise the pypdf minimum and tested constraint to 6.21.4 after the dependency audit reported CVE-2026-119204 and CVE-2026-119205. This updates source installation; existing 1.0.0 release artifacts are unchanged. Upgrade an installed environment with the current source/constraints before processing untrusted PDFs. [Upstream release](https://github.com/py-pdf/pypdf/releases/tag/6.21.4).
- IT: Minimo e vincolo pypdf aggiornati a 6.21.4 dopo i rilievi CVE-2026-119204 e CVE-2026-119205. La correzione riguarda l installazione dai sorgenti; i pacchetti della release 1.0.0 esistente restano invariati. Aggiornare l ambiente con sorgenti/vincoli correnti prima di elaborare PDF non fidati.
