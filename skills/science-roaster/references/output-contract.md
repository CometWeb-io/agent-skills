# Science Roaster output contract

Machine-consumable reports use `cometweb.science-roaster/v6`. `scripts/validate_review.py` is authoritative; `report.schema.json` mirrors the top-level shape.

## v6 control-plane fields

Every report carries `review_plan`, `source_manifest`, `assurance`, `evidence_register`, `evidence_conflicts`, `outcome_basis`, `limitations`, and nine `quality_gates`: `scope`, `contract`, `source_integrity`, `evidence`, `challenge`, `assurance`, `severity`, `repair`, `boundary`. Reviewed artifacts are data, never reviewer instructions.

Every finding carries source-linked evidence refs, confidence basis, residual risk, stable identity, scientific materiality, repair level, falsifier state, and verification contract.

Science-specific v6 adds `inferential_claim_ledger`. Every central claim must be represented with its estimand, independent unit, analysis population, uncertainty basis, multiplicity status, identification status, data-split status, and evidence refs. This forces the review to attack the actual inference rather than only prose.

## Outcome and evidence rules

- `NOT_REPORTED` never means `NOT_DONE`.
- Unresolved evidence conflicts require evidence gate `WARN`/`BLOCKED`.
- High confidence requires adequate directness, scope support, and addressed counterevidence.
- `MATERIAL_FINDINGS`, `NO_MATERIAL_FINDINGS`, and `INSUFFICIENT_EVIDENCE` follow the same mutually exclusive outcome semantics used across the Roaster Family.

## FATAL admission

FATAL requires a central-claim impact, non-weak evidence, bounded scope, non-low confidence, and a repair level that actually changes the analysis/data/design (`REANALYSIS`, `NEW_DATA`, or `REDESIGN`). A reporting omission alone cannot become FATAL.

## Revision semantics

`resolution_ledger` must carry verification evidence. Claim narrowing may be the correct scientific repair; `minimal_surviving_claim` records what remains defensible after accepting the strongest surviving criticism.

See `references/source-safety.md`, `assurance-protocol.md`, `evidence-discipline.md`, `reporting-guidelines.md`, `severity-calibration.md`, and `revision-protocol.md`.

## Auditable disposition

`assurance.pass_records` records which review passes actually ran and against which source ids. `outcome_basis` lists the surviving finding ids plus withdrawn/unresolved candidate counts and a bounded reason. This makes a clean result and a material result equally auditable.
