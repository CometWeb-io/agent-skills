# Changelog

## 1.1.1

- Added `tests/test_validate_report.py` — golden fixtures plus invariant regression cases.
- Added `extras/cursor-rule.mdc` for Cursor routing.

## 1.1

- Added environment-aware mutation safety; production/unknown default read-only.
- Added privacy-safe evidence handling and explicit policy-blocked coverage.
- Added host capability profiles with proof/confidence limits.
- Split defects, usability risks, recommendations, and needs-repro.
- Added mandatory Expected basis to reduce heuristic false positives.
- Recalibrated severity around user impact; removed automatic blocker shortcuts.
- Made `standard` sampling explicit and reserved zero-sampling exhaustion for
  `forensic`.
- Added evidence manifest and structured `audit-report.json` contract.
- Added stdlib `scripts/validate_report.py` with cross-field protocol checks.
- Added JSON schemas, positive/negative validator fixtures, and OpenAI metadata.
- Simplified ChatGPT frontmatter to `name` + `description` for compatibility.
