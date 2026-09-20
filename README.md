# Open Research Engine

> Research any topic. Every claim has a source.

**Open Research Engine** is an evidence-first research system. It imports web pages and documents, retrieves relevant material semantically, extracts reviewable claims, and produces reports whose statements link back to specific source passages.

The working product name is **SourcePilot**. The repository name remains intentionally descriptive until brand, domain, and trademark checks are complete.

## The problem

Research tools often collapse discovery, interpretation, and writing into an answer that is hard to audit. This project treats them as separate, inspectable stages:

1. preserve the supplied source and its provenance;
2. locate relevant passages;
3. propose claims and their supporting or conflicting evidence;
4. let a person review the result;
5. export a report that readers can verify.

## MVP scope

- Import URLs, PDFs, and common document formats.
- Semantic search across imported source versions.
- Claim extraction with passage-level citations.
- Document comparison and candidate contradictions.
- Markdown and PDF reports.
- API and CLI for scripted use.

## Non-goals for the first release

- Presenting generated text as verified fact without a cited source passage.
- Automatically deciding that a source is trustworthy or that a contradiction is conclusive.
- Replacing editorial, academic, legal, or scientific review.
- Building a general-purpose chat product before the evidence workflow is solid.

## Start here

- [Product brief](docs/PRODUCT.md)
- [Architecture outline](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Domain language](CONTEXT.md)
- [Architecture decisions](docs/adr/)

## Project status

Planning foundation. No runtime, storage engine, model provider, or deployment platform has been selected yet. Those choices should follow a short discovery phase and an end-to-end evidence prototype.

## Contribution principles

- Make provenance visible rather than merely asserting it.
- Keep source capture, AI proposals, and human decisions distinguishable.
- Preserve original artifacts and stable locators whenever possible.
- Treat uncertainty as data, not as an error to hide.
