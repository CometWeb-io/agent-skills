# Changelog

## [1.1.0] - 2026-10-02

### Changed

- Front door cut from 15.7 KB to 8.7 KB, with a trigger table for the six
  references. Continuous-monitoring semantics and failure modes moved to
  `references/monitoring-policy.md` §9–10, the contradiction checklist into
  `references/source-policy.md` §6, and the report quality gate to
  `references/output-contract.md` §9.
- SKILL.md and `references/integrations.md` routed to nine skills this catalog
  does not ship (`competitors`, `sales-enablement`, `pricing`, `ads`,
  `customer-research`, `seo-audit`, `ai-seo`, `product-marketing`,
  `marketing-loops`) as if they were present. In-repo handoffs are now listed
  first; the others are used only when the host has them installed.
- The description sends mechanism extraction for your own product to
  product-teardown.
- `tests/front-door-rules.json` pins every rule and moved checklist.

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
