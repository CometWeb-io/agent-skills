# Verification, rollback, and repair graphs

## Repair graph

Model `depends_on` explicitly. Reject missing dependencies and cycles. One active root-cause repair should own a finding unless an explicit supersession relationship explains the overlap.

## Patch risk

Classify patch risk `LOW|MEDIUM|HIGH|CRITICAL`. HIGH/CRITICAL repairs require a rollback plan or equivalent safe reversal strategy before mutation.

## Verification plan

DEEP/strict closure requires a plan containing method and concrete checks before a repair can be considered verifiable. Closure evidence must be fresh and bound to the current candidate.

`CLOSED` is not a writing choice. Re-open when the original symptom returns, a protected invariant fails, or a regression invalidates prior verification.

`WONT_FIX` in strict/deep workflows requires an authorized decision with rationale and expiry/revisit condition; it cannot be used as a garbage chute for inconvenient findings.
