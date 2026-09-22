# Evaluation contract

Optimize for **READY precision and premature-completion resistance**.

## Invariants

- Candidate and acceptance contract identities are bound before a verdict.
- At least one required gate exists.
- Required PASS needs structured evidence tied to the same candidate, with source, locator, and timezone-aware observation time.
- Required FAIL => `NOT_READY`; required UNKNOWN => `DEFER`.
- Required N/A requires rationale and is never a substitute for missing evidence.
- Open blocking BLOCKER/MAJOR => `NOT_READY`.
- `READY_WITH_CONTROLS` may carry only bounded MINOR/NOTE controls and can never bypass a required gate.
- Controls require issue, owner, and revisit condition.
- A candidate change invalidates the prior verdict.

## Golden cases

Cover clean READY, missing identity, no required gates, missing candidate-bound evidence, stale/mismatched candidate, required FAIL/UNKNOWN/N/A, open blocker, complete/incomplete controls, required-gate bypass, malformed findings/controls/gates.

## Champion/challenger metrics

Measure false READY rate first, then unnecessary DEFER rate, stale-verdict catch rate, candidate-mismatch catch rate, and decision clarity. Never trade a material false-green increase for convenience.

Run `python3 scripts/run_evals.py` and all hardening gates before promotion.
