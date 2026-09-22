# Modes and brief versioning

Use this reference when the brief is likely to be revised, handed to multiple specialists, or used as an acceptance contract.

## Modes

- `LIGHT`: one bounded, reversible artifact; keep only objective, audience, deliverable, hard constraints, and observable must-pass criteria.
- `STANDARD`: default; include evidence policy, assumptions, unresolved decisions, exclusions, and protected invariants when material.
- `DEEP`: expensive-to-redo or multi-specialist work; require use moment, explicit scope, risk level, traceable criteria, and protected invariants for HIGH/CRITICAL risk.

Depth changes required evidence, not verbosity. Never inflate a LIGHT brief into a questionnaire.

## Version identity

Treat a materially changed brief as a new contract version. Preserve:

`brief_id`, `brief_version`, `supersedes_brief_id`, `changed_fields`, `downstream_revalidation_required`.

A change is material when it can alter claims, audience, evidence policy, scope, acceptance, protected invariants, or a consequential decision. Cosmetic wording changes do not force downstream revalidation.

## Decision rule

Never turn a consequential unresolved decision into an assumption to keep the pipeline moving. Mark it `DECISION_NEEDED`; if the decision is material and evidence is sufficient, route to the owning decision skill. If evidence is insufficient, verify first.
