# Publication state model

## Canonical stages

`BRIEFED -> SOURCE_READY -> OUTLINE_LOCKED -> DRAFTED -> CLAIMS_RECONCILED -> EDITED -> MASTER_LOCKED -> FORMAT_READY -> RELEASE_READY -> PUBLISHED`

Use the earliest defensible stage.

- `BRIEFED`: purpose, audience, publication type and source/output policy are sufficiently defined.
- `SOURCE_READY`: required source/evidence inputs for current drafting scope are admitted.
- `OUTLINE_LOCKED`: section structure and coverage contract are stable enough to draft.
- `DRAFTED`: full intended manuscript body exists, but claim reconciliation is not implied.
- `CLAIMS_RECONCILED`: material claims, citations, scope, uncertainty and gaps have been checked against admitted sources.
- `EDITED`: editorial/style pass completed; substantial rewrites may still require fidelity admission.
- `MASTER_LOCKED`: canonical `manuscript.md` is accepted for derivation and its hash/version are frozen.
- `FORMAT_READY`: every required derived artifact for the current release passed generation, lineage, parity and required QA.
- `RELEASE_READY`: publication package has no critical open gap and is ready for the target release action.
- `PUBLISHED`: publication event is evidenced.

Side states: `NEEDS_RESEARCH`, `NEEDS_AUTHOR_INPUT`, `BLOCKED`, `SUPERSEDED`, `ARCHIVED`.

A side state does not erase historical stage evidence. For example, a previously PUBLISHED edition may be stale and require REFRESH without pretending it was never published.

## Non-equivalences

Evidence Pack != manuscript. Outline != draft. Draft != reconciled manuscript. Humanized != fidelity-verified. Generated file != FORMAT_READY. File existence != PUBLISHED. PUBLISHED != current.
