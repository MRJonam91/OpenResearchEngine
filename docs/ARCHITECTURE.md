# Architecture outline

## Guiding constraints

The MVP must make evidence inspectable, preserve imported artifacts, and keep automated suggestions separate from reviewer decisions. A system may use language models, embeddings, OCR, or parsers, but none of these may erase the original source or silently turn a proposal into an accepted Claim.

## Logical flow

```text
Source import
  -> provenance capture and immutable Source Version
  -> parsing / OCR / normalization
  -> locatable Passages
  -> semantic index and retrieval
  -> claim and comparison proposals
  -> reviewer decisions and Report export
```

## Bounded components

| Component | Responsibility | Must retain |
| --- | --- | --- |
| Ingestion | Fetch or receive a Source and create its Source Version | origin, import time, fingerprint, original artifact when permitted |
| Extraction | Convert a version into searchable, locatable Passages | page/section/character locators and extraction confidence |
| Retrieval | Return relevant Passages for a question | ranking method and query context |
| Analysis | Propose Claims, Evidence Links, and Contradiction Assessments | model/prompt/version metadata and cited inputs |
| Review | Capture human acceptance, edits, rejection, and uncertainty | reviewer, timestamp, rationale where supplied |
| Reporting | Render a Report from reviewed data | citation locators and export version |
| Interfaces | Expose the workflow through API, CLI, and later UI | stable identifiers and structured errors |

## Data invariants

- A Citation must resolve to one or more Passages from identified Source Versions.
- A Reported Claim must show whether it is proposed, reviewed, disputed, or unresolved.
- Reprocessing produces a new derived result; it does not overwrite a Source Version or reviewer decision.
- Each automated result records enough configuration to understand how it was produced.
- Deleting a workspace must define the fate of retained originals, derived text, indices, and exports.

## Deliberately undecided implementation choices

The repository does not yet commit to a programming language, database, vector store, model provider, web framework, queue, or hosting service. The discovery phase should choose these from the evidence-proven MVP slice, operational cost, data-control requirements, and contributor ergonomics—not from an assumed stack.

## First technical spike

Build one reproducible vertical slice using a small, consented corpus:

1. import one HTML page and one text PDF;
2. preserve originals and create locatable passages;
3. retrieve passages for a question;
4. create one claim proposal with supporting and challenging evidence;
5. approve it manually;
6. export a Markdown report with working links/locators.

This spike should establish the evidence model and evaluation fixtures before a public interface is built.
