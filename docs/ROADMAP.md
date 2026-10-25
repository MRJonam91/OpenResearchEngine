# Roadmap

## Stato 1.0.0 / Shipped in 1.0.0

[Release stabile / Stable release](https://github.com/MRJonam91/OpenResearchEngine/releases/tag/v1.0.0), pubblicazione e verifiche confermate il 25 ottobre 2026 / publication and checks confirmed on 25 October 2026.

| Area | Stato / Status |
| --- | --- |
| Import TXT/MD/HTML/PDF/DOCX, originali, versioni, passaggi | Completato / Shipped |
| Web app locale, API e CLI | Completato / Shipped |
| FTS5, confronto affiancato e revisione umana | Completato / Shipped |
| Semantica e proposte citate tramite Ollama locale opzionale | Completato / Shipped; qualità dipendente dal modello / model-dependent quality |
| Markdown/PDF e provenienza AI | Completato / Shipped |
| Diagnostica, backup/ripristino portabile | Completato / Shipped |

La 1.0 consolida il flusso personale locale. I controlli automatici validano struttura, citazioni e integrità; non certificano la verità dei contenuti. Il [piano 1.0](superpowers/plans/2026-10-24-v1.md) registra implementazione e verifiche.

Version 1.0 stabilizes the personal local workflow. Automated checks validate structure, citations, and integrity; they do not certify content truth. The [1.0 plan](superpowers/plans/2026-10-24-v1.md) records implementation and release validation.

## Priorità successive / Next priorities

1. **1.0.x affidabilità / reliability:** regressioni, aggiornamenti dipendenze, accessibilità e miglioramento delle segnalazioni d'errore / regressions, dependency updates, accessibility, and clearer errors.
2. **1.1 qualità ricerca / research quality:** corpus con licenza e aspettative di recupero, valutazione di citazioni e disaccordi, confronto tra modelli con metadati riproducibili / licensed evaluation corpus, retrieval/citation/disagreement evaluation, reproducible model comparisons.
3. **1.2 scala personale / personal scale:** indicizzazione incrementale in background, cancellazione controllata, PDF multilingua e localizzazione UI / background incremental indexing, controlled deletion, multilingual PDF fonts, and UI localization.
4. **Ricerca futura / later research:** OCR con posizioni verificabili, nuovi formati e scoperta web assistita; hosting e multiutenza solo con identità, autorizzazioni e policy dati dedicate / locatable OCR, more formats, assisted web discovery; hosting only with dedicated identity, authorization, and data controls.

## Piano originario / Original staged vision

The stages below remain a product vision. Completed pieces are listed above; unshipped evaluation/hosting gates remain future work.

## 0. Discovery and evaluation

- Define the initial user journey, privacy posture, licensing assumptions, and source-ingestion policy.
- Assemble a small, licensed evaluation corpus with expected citations and known disagreements.
- Set measurable quality gates: passage retrieval, citation correctness, claim faithfulness, and contradiction precision.
- Stack selected for 1.0: Python/FastAPI/SQLite with optional local Ollama.

**Exit condition:** a written scope, evaluation fixture set, and a decision record for material technology commitments.

## 1. Evidence-core prototype

- Import HTML and text-based PDFs.
- Version sources, normalize content, and create stable passage locators.
- Implement search and a reviewable claim proposal flow.
- Render Markdown reports with source-linked citations.

**Exit condition:** a repeatable import-to-report workflow on the evaluation corpus, with manual review.

## 2. MVP interfaces

- Publish a versioned local API and CLI.
- Add a minimal research workspace interface.
- Support document comparison and candidate contradiction assessments.
- Export PDF and record report versions.

**Exit condition:** a non-developer can complete the core workflow and independently inspect every citation.

## 3. Reliability and hosted option

- Add authentication, authorization, deletion workflows, observability, backups, and rate limits.
- Expand import types and OCR only after their citation quality meets the evaluation gate.
- Offer optional hosted deployment while preserving a credible local/self-hosted path.

**Exit condition:** documented operational controls and a sustainable hosting-cost model.

## Backlog guardrails

Do not add autonomous publishing, uncited “answers”, opaque authority scoring, or broad social features ahead of evidence quality and review ergonomics.
