# Changelog

## [1.2.0] - 2026-10-02

### Changed

- Front door cut from 15.9 KB to 9.8 KB. Inspection routing and ledger lanes
  moved to `references/evidence-model.md` §10–11; the non-candidate list and
  the red-team checklist moved to `references/pattern-transfer.md` §9–10. Each
  workflow step names the reference to open.
- The handoff list named `competitor-profiling` and `competitors`, which this
  catalog does not ship. They are now routed to only when the host has them;
  in-repo handoffs (`competitive-intelligence`, `repo-to-roadmap`,
  `product-operator`, `ai-council`, `release-readiness`,
  `evidence-researcher`) are named by id. The description names
  `competitive-intelligence` and `repo-to-roadmap` for the overlapping cases.
- `tests/front-door-rules.json` pins every quality rule and moved checklist.

## [1.1.0] - 2026-09-18

### Fixed

- `validate_pattern_ledger.py` raised `TypeError` instead of reporting an error
  when a field held a list or dict. Fourteen membership tests were written as
  `value not in ALLOWED`, which is unhashable-unsafe, and every value comes from
  a caller-supplied JSON file — so malformed input killed the validator rather
  than being validated. Membership now goes through a helper that accepts only
  strings, and a fuzz test walks every field of a valid ledger with list, dict,
  null, negative-number and junk-string values to keep it that way.

## 1.0.0

- Initial public release in CometWeb Agent Skills.
