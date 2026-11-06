# Portfolio validation migration: 1.2.x to 2.0.0

The existing report protocol values `1.0` and `1.1`, lane names, numeric/delegation
rules, and the `validate` response shape `{valid, errors}` remain available. The
acceptance boundary is stricter: `validate` now checks that the portfolio envelope
exists and is well formed, rather than accepting an empty or partial object.
Previously accepted partial reports need the missing context added before they can
pass full validation. Do not fill missing facts with guesses.

## Consumer actions

1. Capture the actual timezone-aware `as_of`, horizon, goal, scope, capacity source,
   coverage states, and readiness from the run. If the goal or scope is unknown,
   use `primary_goal: "UNKNOWN"`, an empty `portfolio_scope`, and `BLOCKED` with
   a reason; explicitly represent unavailable sources in `coverage`.
2. Preserve existing lane items, evidence, date provenance and delegation records.
   Run `portfolio_kernel.py validate --report-json report.json` and handle `valid` and
   `errors` before calling the report complete. The shape and names of lane fields
   have not changed.
   Supplied scoring dimensions must be finite numbers in the documented 0–5 range;
   `days_to_deadline` must be an integer. Lists of source references must contain
   at least one non-empty text reference. Each `must_do`/`now` item needs a
   non-empty text `done_when` and a non-empty evidence list containing text
   references or objects with non-empty text `source` and `locator`; each
   delegate needs a non-empty text executor, question and return contract.
3. Consumers that deliberately inspect an incomplete fragment can use
   `validate-invariants --report-json fragment.json`. It returns `validation_scope:
   invariants_only` and `complete_report_validated: false`, alongside `valid` for
   the supplied invariants. An exit code 0 or `valid: true` from this explicitly
   partial command never means the complete report has been validated. `render`
   remains a renderer and does not validate.

Example partial input, valid only for a partial check:

```json
{"now": []}
```

Example blocked complete envelope, after the producer records real limitations:

```json
{"protocol_version":"1.0","as_of":"2026-11-06T10:00:00+01:00","horizon":"14d",
 "primary_goal":"UNKNOWN","portfolio_scope":[],"capacity":{"source":"unknown"},
 "coverage":{"calendar":"unavailable"},
 "readiness":{"status":"BLOCKED","reason":"Goal and scope not available"},"now":[]}
```

Verification: empty and malformed envelopes fail full validation; the blocked
example and documented 1.0/1.1 complete reports pass; previous lane evidence,
precision, delegation and future-gate controls still reject their counterexamples.
The tests are `tests/test_report_completeness.py` and `scripts/run_evals.py`.

Rollback: retain the prior installed package and its version before upgrading;
if rollback is necessary, restore that exact previously reviewed 1.2.5 package and
state clearly that its `validate` only checks provided invariants and can accept an
empty report. Do not treat old or new structural validation as source authentication.
