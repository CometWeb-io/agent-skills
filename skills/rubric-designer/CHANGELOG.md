# Changelog

## [1.7.1] - 2026-10-03

- `scripts/run_evals.py --help` exits 0 with a usage line instead of exit 2; any other argument is still rejected with exit 2 and the unrecognized argument named.
- Eval cases pin the exact `errors` list instead of `status: INVALID`, which
  passed whenever any other rule also failed. Added cases for blank identity
  fields, non-boolean flags, an empty criteria list, missing criterion id and
  fail condition, a non-blocker with a bad floor or materiality, boolean and
  out-of-range weights, and pass/fail conditions identical up to case and
  whitespace. The rubric hash is pinned, equal between a draft and its frozen
  copy and different after a revision change. Held guards: 19 of 29 -> 28 of 29.

## [1.7.0] - 2026-09-22

- Compatibility release for v1.7 shared statistical, failure-operations, handoff and release-governance contracts.
- Package version synchronized to 1.7.0; existing role boundaries remain unchanged.

## [1.6.0] - 2026-09-22

- Suite-wide v1.6 version sync; existing specialist behavior is preserved while remaining compatible with runtime-lifecycle contracts and release tooling.

## 1.5.0
- Initial public-candidate implementation.
