# Changelog

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
