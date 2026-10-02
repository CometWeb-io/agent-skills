# Changelog

## [1.0.2] - 2026-10-02

### Changed

- Description adds an explicit do-not-use boundary (one-time profiles without
  monitoring intent, comparison pages, own pricing, full visibility audits) and
  no longer presents `competitor-profiling`, which this catalog does not ship,
  as a sibling the host can route to.

## [1.0.1] - 2026-09-18

### Fixed

- `evals/evals.json` spelled its expectation key `expected` while every other
  behavioural suite in the repository uses `expect`. Nothing read either file,
  so nothing noticed; a grader written against one suite would have found no
  expectations in this one and reported all ten cases as passing. Renamed to
  `expect`, and `tooling/tests/test_model_eval_suites.py` now holds the shape.

## 1.0.0

- Initial public release in CometWeb Agent Skills.
