# Evaluation contract

Optimize for **real closure, not status inflation**.

## Invariants

- No `CLOSED` item without finding IDs, root cause, done condition, candidate identity, and fresh PASS verification.
- Fresh verification includes method, concrete evidence, timezone-aware observation time, and candidate match.
- A detected regression prevents closure.
- `VERIFY_FIRST` and `WONT_FIX` cannot masquerade as CLOSED repair classes.
- `WONT_FIX` requires an authorized decision source with owner, rationale, and decision time.
- `DEFERRED` requires a reason.
- No input finding disappears silently.
- Malformed inputs fail closed rather than crash.

## Golden cases

Cover valid closure, stale verification, candidate mismatch, missing timestamp, missing root cause/done condition, regression, VERIFY_FIRST closure attempt, valid/invalid WONT_FIX, deferred with/without reason, duplicate IDs, orphan repair, malformed collections.

## Champion/challenger metrics

Measure false-closure rate, root-cause consolidation quality, regression escape rate, percentage of repairs verified against the original finding, and unnecessary change surface. The lowest false-closure rate wins over the highest apparent completion rate.

Run `python3 scripts/run_evals.py` plus hardening gates before promotion.
