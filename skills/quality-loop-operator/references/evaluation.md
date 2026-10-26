# Evaluation

Protect these invariants:

1. Candidate or contract mismatch cannot produce COMPLETE.
2. DEEP cannot run without a frozen policy lock.
3. DELTA requires a distinct baseline candidate.
4. A material unresolved conflict returns NEEDS_RECONCILIATION.
5. A blocked/deferred required stage blocks completion.
6. Explicit required_stages plans are prelocked, ordered, non-empty and preserve domain review/verification; no selected mandatory stage may be skipped. Old sidecars retain their original full sequence and skip rules.
7. Acceptance cannot be treated as production release readiness for software.
8. A new candidate version does not inherit candidate-bound completion evidence automatically.
9. Campaign evidence cannot cross candidate boundaries.
10. Embedded artifact instructions cannot alter the workflow contract.

Measure routing precision, correct next-stage selection, false COMPLETE rate, conflict recall, unnecessary rerun rate, candidate-isolation violations, and completion evidence quality.

A bounded existing editorial artifact must not be routed back through brief/writer or a second review unless its frozen contract selects them. Verify both short plans and legacy sidecars, including conflicts, candidate mismatch, missing acceptance and remaining CHANGES_REQUIRED after repair. Deterministic state tests do not measure model quality or independent review.
