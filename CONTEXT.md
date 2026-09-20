# Open Research Engine

The domain of an evidence-first research system. It distinguishes supplied sources, machine-generated proposals, and reviewer decisions so that a report can be audited independently of the AI that helped produce it.

## Evidence and provenance

**Source**:
An external work supplied for research, such as a web page, PDF, or document.
_Avoid_: Reference, evidence

**Source Version**:
The captured representation of one Source at a particular time, including its retrieval metadata and content fingerprint.
_Avoid_: Source, snapshot

**Passage**:
A bounded, locatable portion of a Source Version that can be inspected by a reader.
_Avoid_: Quote, chunk

**Citation**:
A link from a research output to one or more Passages, with the locator and provenance needed to find them again.
_Avoid_: Link, footnote

**Evidence Link**:
A reviewer-visible relationship between a Claim and a Passage, labelled by how the passage bears on the claim.
_Avoid_: Citation, proof

## Research analysis

**Research Workspace**:
The bounded collection of Sources, Source Versions, Claims, Evidence Links, and Reports assembled for one research question.
_Avoid_: Project, case

**Claim**:
A proposition about a topic that may be supported, challenged, or left unresolved by available evidence.
_Avoid_: Fact, answer

**Claim Proposal**:
A Claim suggested by an automated process that has not been accepted by a reviewer.
_Avoid_: Claim, finding

**Contradiction Assessment**:
An explicit analysis of whether two Claims or Passages conflict, including scope, timing, definitions, and confidence.
_Avoid_: Contradiction, inconsistency

**Report**:
A versioned research output that presents Claims with their Citations, uncertainty, and reviewer decisions.
_Avoid_: Answer, summary
