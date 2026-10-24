# Product brief

## Contratto 1.0 / 1.0 contract

La 1.0 offre importazione locale, fonti e passaggi conservati, ricerca testuale e semantica opzionale, proposte AI citate, confronto, revisione umana, report e backup. Il modello non approva risultati. Il prodotto serve una persona sul proprio computer; l'hosting non è incluso. La [guida](USER_GUIDE.md) descrive funzioni e limiti effettivi.

Version 1.0 ships local imports, retained sources/passages, text and optional semantic search, cited AI proposals, comparison, human review, reports, and backup. Models never approve results. It serves one person on their computer; hosting is outside this release. The [guide](USER_GUIDE.md) describes shipped behavior and limits.

The original product direction below remains the vision for subsequent releases.

## Promise

Open Research Engine helps a reader answer a research question without hiding the evidence trail. The central promise is not that the system is always right; it is that every reportable factual claim can be traced to inspectable source passages or is clearly marked as unsupported, disputed, or interpretive.

## Primary users

- Students and researchers who need a reproducible reading trail.
- Journalists who need to compare accounts and retain attributable evidence.
- Developers and analysts who research technical or policy questions across changing documentation.
- Professionals who need a source-linked briefing rather than a black-box summary.

## Core workflow

1. A user creates a Research Workspace and states a question.
2. They import one or more Sources by URL or file.
3. The system records each Source Version and extracts locatable Passages.
4. Search finds passages relevant to a question; analysis proposes Claims and Evidence Links.
5. The user reviews, edits, accepts, rejects, or marks uncertainty on the proposals.
6. The system compares evidence and surfaces candidate Contradiction Assessments.
7. The user exports a Report in Markdown or PDF with citations.

## MVP acceptance criteria

- An imported artifact retains original URL or file metadata, retrieval/import time, content fingerprint, and processing status.
- Every displayed citation opens a stable locator to the supporting Passage and its Source Version.
- A generated Claim is visibly labelled as a proposal until a reviewer acts on it.
- Candidate contradictions preserve both passages and explain the possible source of conflict; they are not presented as resolved facts.
- An exported report remains useful outside the product: citations include source title, URL or document identity, version date/import date, and locator.
- The API and CLI can run the same basic import-to-report workflow without the web interface.

## Questions to resolve before implementation

1. Which source types are supported in the first vertical slice: HTML and text PDFs only, or also DOCX/EPUB?
2. What defines a stable locator for reflowing web pages and scanned PDFs?
3. Which review decisions require authorship and timestamps?
4. What data retention, deletion, copyright, and robots-policy rules apply to hosted imports?
5. What quality evaluation set will measure citation correctness, claim faithfulness, retrieval recall, and contradiction precision?

## Explicit product boundaries

- “Cited” means linked to a passage, not automatically true.
- “Contradiction” is a reviewable assessment, not an automatic verdict.
- A source's authority is context-dependent and must not be reduced to a hidden score.
- An AI-generated synthesis must expose its supporting evidence and uncertainty.
