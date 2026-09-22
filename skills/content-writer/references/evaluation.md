# Evaluation contract

Optimize for **useful prose with claim integrity**, not length or stylistic flourish.

## Invariants

A regression exists if:

- a material `SUPPORTED` claim can pass without structured `source` + `locator` evidence;
- a freshness-sensitive claim can pass without timezone-aware `observed_at` and `CURRENT|NEAR_EXPIRY` status;
- a material `INFERRED` claim lacks basis claims or is presented as direct fact;
- `OPINION`, `EXAMPLE`, `UNRESOLVED`, or `UNSUPPORTED` is silently presented as fact;
- unresolved/unsupported material claims remain release-eligible;
- malformed claim ledgers crash instead of failing closed.

## Golden cases

Maintain: current sourced number; stale/unbounded current claim; supported-without-evidence; inference with/without basis; opinion/example fact inflation; unresolved material claim; duplicate IDs; empty ledger; malformed evidence.

## Champion/challenger metrics

Use the same brief and source pack. Compare unsupported-claim rate, material claim recall, reader-question coverage, redundancy, source hallucination rate, brief compliance, and context/token cost. A prettier draft is not a win if factual discipline regresses.

## Verification

Run `python3 scripts/run_evals.py`; then fuzz, coverage, mutation and package-regression gates for a release candidate. Real-host evaluation should compare with-skill vs without-skill and include negative trigger controls.
