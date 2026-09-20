# Roadmap

## 0. Discovery and evaluation

- Define the initial user journey, privacy posture, licensing assumptions, and source-ingestion policy.
- Assemble a small, licensed evaluation corpus with expected citations and known disagreements.
- Set measurable quality gates: passage retrieval, citation correctness, claim faithfulness, and contradiction precision.
- Select the implementation stack only after the first vertical slice clarifies needs.

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
