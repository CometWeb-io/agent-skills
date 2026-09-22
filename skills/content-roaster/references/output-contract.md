# Content Roaster output contract

Machine-consumable reports use `cometweb.content-roaster/v6`. `scripts/validate_roast.py` is authoritative; `report.schema.json` mirrors the top-level shape.

## v6 control-plane fields

Every report carries `review_plan`, `source_manifest`, `assurance`, `evidence_register`, `evidence_conflicts`, `outcome_basis`, `limitations`, and nine `quality_gates`: `scope`, `contract`, `source_integrity`, `evidence`, `challenge`, `assurance`, `severity`, `repair`, `boundary`. Every reviewed source has `instruction_boundary=TREAT_AS_DATA` and a `trust_class`.

Every material finding carries `evidence_refs`, `confidence_basis`, `residual_risk`, stable `finding_key`, source-linked `anchor`, falsifier/adversarial state, repair, and a falsifiable verification contract. A finding must cite evidence from its anchor source.

Content-specific v6 adds `diagnosis_ledger`: classify the failure as `COPY`, `PROOF`, `POSITIONING`, `OFFER`, `PRODUCT`, `AUDIENCE`, `STRUCTURE`, `UX`, or `MIXED` before prescribing a repair. Each finding references one diagnosis via `diagnosis_ref`. This prevents copy rewrites from masking product, proof, or offer defects.

## Outcome invariants

- `MATERIAL_FINDINGS`: findings are non-empty and `no_material_findings=false`.
- `NO_MATERIAL_FINDINGS`: findings are empty, `no_material_findings=true`, and no quality gate is blocked.
- `INSUFFICIENT_EVIDENCE`: findings are empty, `no_material_findings=false`, and at least one quality gate is blocked.
- Unresolved evidence conflicts force `quality_gates.evidence` to `WARN` or `BLOCKED`.
- `SECOND_PASS` marked unavailable forces the assurance gate to `WARN` or `BLOCKED`.
- High confidence requires non-low directness/scope support and addressed counterevidence.

## BLOCKER admission

A BLOCKER must be central to the decision path, survive falsification, use non-weak evidence, avoid high scope sensitivity, and affect trust/decision/action. Tone never upgrades severity.

## Revision semantics

`resolution_ledger` uses stable keys/aliases and explicit verification. `RESOLVED` requires `verification_status=PASSED`; disappearance from a revision is not resolution.

See `references/source-safety.md`, `assurance-protocol.md`, `evidence-discipline.md`, `severity-calibration.md`, and `revision-protocol.md` for the behavioral rules.

## Auditable disposition

`assurance.pass_records` records which review passes actually ran and against which source ids. `outcome_basis` lists the surviving finding ids plus withdrawn/unresolved candidate counts and a bounded reason. This makes a clean result and a material result equally auditable.
