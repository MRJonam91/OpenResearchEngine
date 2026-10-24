# Local beta design

## Outcome

Publish a usable single-user beta of SourcePilot in the private repository. It must preserve the alpha workflow and its workspaces while making evidence correction and source comparison practical. The release is `0.2.0b1`.

## Beta scope

1. Source history: show every imported version of a source, allow browsing its passages, and allow downloading its retained original. Search uses the latest version of each source by default, with an explicit option to include history. Existing claim citations remain tied to their original version.
2. Claim correction: edit the statement, update review status and note, change a linked passage's stance, or remove a mistaken evidence link. Every claim must retain at least one evidence link. Editing the statement returns an approved or uncertain claim to `proposed` for fresh review. A short append-only revision history records statement/status/note changes.
3. Comparison: select two sources and a query. The service returns relevant latest-version passages from each source in separate groups. The UI displays them side by side and lets the user connect either passage to a claim. The tool does not call a disagreement a contradiction without user review.
4. PDF report: export the same included claims and citation metadata as Markdown. The PDF has a readable title, claim sections, evidence stances, source notes, page numbers, and no unsupported claim text silently omitted. The UI and CLI expose PDF output.
5. Local security and release quality: reject unexpected Host headers and cross-origin writes, stream uploads under the size cap, pin a testable dependency range, add CI, and document upgrade and backup steps.

## Non-goals

No external AI model, automated truth decision, OCR, semantic embeddings, shared hosting, or multi-user accounts in this beta. Search remains SQLite FTS5 and is labelled accordingly.

## Interfaces and data

The Python service remains the single owner of SQLite. Schema changes must migrate an alpha workspace in place without dropping sources, claims, or citations. API routes and CLI commands reuse service functions. The UI receives structured source/version and comparison data and never reads arbitrary server paths. The server binds to loopback by default and serves original files as downloads, not executable HTML in the app origin.

## Acceptance

- An alpha workspace opens with all existing claims and passage IDs intact.
- Reimporting changed bytes creates a visible new version; default search hides old passages, history search can find them, and old citations still resolve.
- A mistaken evidence link can be removed without orphaning a claim; statement edits require renewed review.
- Comparison shows passages from both selected sources and keeps citations attached to the correct version.
- Markdown and PDF reports contain the same included claim set and citation metadata.
- Browser and CLI flows pass with a real test corpus; tests run in CI on Windows and Linux.
