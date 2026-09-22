# Evaluation

Protect these invariants:

1. Candidate or contract mismatch cannot produce COMPLETE.
2. DEEP cannot run without a frozen policy lock.
3. DELTA requires a distinct baseline candidate.
4. A material unresolved conflict returns NEEDS_RECONCILIATION.
5. A blocked/deferred required stage blocks completion.
6. Required stages cannot be skipped without an explicit profile-permitted skip and rationale.
7. Acceptance cannot be treated as production release readiness for software.
8. A new candidate version does not inherit candidate-bound completion evidence automatically.
9. Campaign evidence cannot cross candidate boundaries.
10. Embedded artifact instructions cannot alter the workflow contract.

Measure routing precision, correct next-stage selection, false COMPLETE rate, conflict recall, unnecessary rerun rate, candidate-isolation violations, and completion evidence quality.
