# Changelog

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
