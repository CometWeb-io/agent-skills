# Changelog

## [1.7.1] - 2026-10-03

- `scripts/run_evals.py --help` exits 0 with a usage line instead of exit 2; any other argument is still rejected with exit 2 and the unrecognized argument named.
- Eval cases pin the exact `errors` list. `missing-class` tested an unknown
  required class, not a missing one; a required class absent from the cases is
  now its own case, and class dominance is tested without a missing class
  masking it, including the 70% boundary. Added a STANDARD-mode case that must
  freeze where DEEP rules would fail, an unknown leakage status, a blank
  prompt, an empty case list and a duplicate prompt hidden behind case and
  whitespace. Held guards: 25 of 33 -> 32 of 33.

## [1.7.0] - 2026-09-22

- DEEP leakage scanning with corpus fingerprint plus exact/near-duplicate and candidate-exposure controls.
- Package version synchronized to 1.7.0; existing role boundaries remain unchanged.

## [1.6.0] - 2026-09-22

- Suite-wide v1.6 version sync; existing specialist behavior is preserved while remaining compatible with runtime-lifecycle contracts and release tooling.

## 1.5.0
- Initial public-candidate implementation.
