# Evaluation contract

Optimize for **learning from independent failures without overfitting**.

## Invariants

- Repetition is measured across distinct `context_id`, not repeated runs of the same context.
- A one-off issue is WATCH unless it is a clearly systemic BLOCKER with evidence.
- A proposal requires either independent recurrence or severe systemic evidence **and** a regression test or explicit owned test gap.
- Ambiguous root layers stay WATCH rather than triggering shotgun edits.
- Invalid severity/root-layer/input shapes fail closed.
- The skill proposes changes by default; it does not silently mutate other skills.

## Golden cases

Cover independent recurrence, duplicate context repeated runs, systemic blocker, recurring pattern without regression test, valid test gap, ambiguous root layer, invalid record, and no-signal cases.

## Champion/challenger metrics

Measure proposal precision, repeated-failure recall, overfit rate, regression-test attachment rate, recurrence after accepted changes, and cross-host/model stability. A change is only VERIFIED after the targeted failure drops without new invariant regressions.

Run `python3 scripts/run_evals.py` plus hardening gates before promotion.
