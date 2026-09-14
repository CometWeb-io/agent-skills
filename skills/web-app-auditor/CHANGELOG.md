# Changelog

## 1.3.1 — 2026-09-12

- Correct installation dependency instructions; the schema-backed validator requires jsonschema.
- Preserve canonical repository assets and license during integration rather than replacing them with bundle metadata.

## 1.3.0 — 2026-09-12

- Add scoped currentness, evidence, safety and domain acceptance contracts.
- Normalize host metadata and verify standalone package structure.
- Validate bundled JSON Schema before cross-field checks; reject unsupported shipping verdicts and inconsistent evidence. Add executable adversarial regressions.

## 1.2

- Added explicit handoff boundaries with Release Readiness, Product Operator, Repo to Roadmap, Customer Ops, Evidence Researcher, and AI Council.
- Added candidate/build-aware QA evidence semantics so an audit cannot accidentally satisfy a mismatched release gate.
- Added `references/composability.md` with lossless coverage/finding/evidence handoff rules.
- Narrowed implicit routing away from whole-repo roadmapping and final production-release authorization.
- Added formal `VERSION` metadata.

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
