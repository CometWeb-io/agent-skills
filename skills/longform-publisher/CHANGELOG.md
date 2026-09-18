# Changelog

## [1.1.0] - 2026-09-18

### Fixed

- `validate_report` raised `TypeError` instead of returning an error code when
  a field held a list or dict: ten membership tests were unhashable-unsafe, and
  every value comes from a caller-supplied report file. A non-object root now
  returns `REPORT_NOT_AN_OBJECT` rather than an `AttributeError` from the first
  `.get()`.

## 1.0.0 - 2026-09-10

- Introduced canonical `manuscript.md` publication control plane.
- Added BUILD, SOURCE_BOUND, RESEARCH_EXPAND and REFRESH modes.
- Added publication lifecycle and non-equivalence gates.
- Added deterministic source/claim admission, post-edit fidelity checks, protected invariants, derived-artifact lineage, DOCX/PDF visual-QA requirements, publication evidence and manifest parity checks.
- Added specialist boundaries for evidence research, research program readiness, humanization, copywriting, DOCX, PDF, image and content strategy workflows.
