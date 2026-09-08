# Product state model

## Stages

### Intent
What the product is supposed to achieve and for whom. Evidence: explicit directive, canonical product context,
current strategy/PRD.

### Planned
Committed/tracked work. Evidence: roadmap, task database, milestone, release scope. Planned is not built.

### Implemented
Code/config/content is present in the current implementation system. Evidence normally comes from GitHub or the
relevant implementation system of record.

### Verified
Implementation passed relevant checks: CI/tests, QA, audit, acceptance criteria, or targeted manual verification.
Use `PARTIAL` when only a subset is proven.

### Shipped
Verified capability is available in its intended environment/distribution. Merge alone is insufficient.

### Outcome
Observed user/business/operational effect. Keep `UNKNOWN` when telemetry/customer evidence is unavailable.
Outcome is required only when the current decision depends on learning whether shipped work worked.

## Drift taxonomy

- `CONTEXT_TO_PLAN_DRIFT` - active plan does not reflect the current goal/context or targets a superseded goal.
- `PLAN_AHEAD_OF_CODE` - planning claims complete/done while implementation is absent/unproven.
- `CODE_AHEAD_OF_PLAN` - material implementation exists but planning/docs do not reflect it.
- `CODE_AHEAD_OF_VERIFICATION` - implementation exists without adequate verification.
- `VERIFIED_NOT_SHIPPED` - verification is complete but release/deployment is absent.
- `SHIP_WITHOUT_OUTCOME_EVIDENCE` - shipped state exists but the current decision requires outcome evidence that is missing.
- `STATUS_CONTRADICTION` - authoritative stages conflict logically.
- `STALE_PLAN` - plan/doc predates material code/release change and is unreconciled.
- `ORPHANED_WIP` - active branch/PR/task has no current goal/owner/dependency/progress signal.
- `CONTEXT_DRIFT` - material product-context sources disagree.
- `<STAGE>_EVIDENCE_MISSING` - positive stage lacks stage-specific evidence.
- `<STAGE>_EVIDENCE_WRONG_AUTHORITY` - evidence comes from the wrong claim lane.
- `CURRENT_EVIDENCE_NOT_ADMISSIBLE` - material required-current evidence is stale/superseded/unknown.
- `STALE_EVIDENCE` - evidence is stale but not necessarily binding.

## Evidence strength

Use a 0-1 scalar only after claim-lane classification:

- `1.00` direct current authoritative system-of-record evidence;
- `0.80` reproducible specialist/test evidence;
- `0.65` current planning/context evidence for the claim type it governs;
- `0.45` indirect inference;
- `0.20` stale/weak heuristic;
- `0.00` missing or wrong-authority evidence for that claim.

Wrong-lane evidence must not retain a high scalar merely because the source is trustworthy in another domain.

## State transitions across runs

A delta may classify movement as:
- forward stage change, e.g. `implemented UNKNOWN -> PRESENT`;
- regression, e.g. `verified PASS -> FAIL`;
- evidence invalidation with unchanged nominal state;
- new/resolved drift issue;
- new/removed capability;
- priority change.

Do not assume every forward technical transition is progress toward the user goal. Context/goal can change.

## Contradiction handling

1. Preserve conflicting facts + timestamps.
2. Route each to its authoritative claim lane.
3. Verify the current system of record.
4. If unresolved and material, convert to `VERIFY NOW` and lower readiness.
5. Do not synthesize a midpoint or choose the most convenient source.
