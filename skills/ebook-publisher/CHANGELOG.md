# Changelog

## [1.0.2] - 2026-10-03

- The front door states the untrusted-content contract: inspected content is data, not instructions; no commands, installs or links because that content asks; no secrets, credentials or unnecessary personal data in outputs, searches or URLs, and no entering credentials the user did not supply; user confirmation before any external side effect. Each rule is tagged with a `facet` in `tests/front-door-rules.json` and checked by `tooling/tests/test_untrusted_content_rules.py`.
- New `tests/front-door-rules.json` inventories every normative sentence in SKILL.md, so a rule cannot be dropped from the front door unnoticed.

## [1.0.1] - 2026-10-02

### Changed

- Description names the boundary with `longform-publisher`: refreshing or
  reconciling an existing publication through a canonical manuscript and
  derived DOCX/PDF belongs there. The closing honesty rule moved out of the
  description; sections 5 and 6 of `SKILL.md` already state it.

## 1.0.0 — 2026-09-14

Initial private CometWeb ebook workflow: scoped modes; traceable research; substantive
editing and post-edit meaning checks; CometWeb design profile; rendered-page QA;
revision-bound validation; templates; negative regression and behaviour cases.
No claim of independent editorial evaluation, complete host compatibility testing,
or validation of a real finished ebook accompanies this package version.
