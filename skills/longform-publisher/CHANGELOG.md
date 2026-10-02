# Changelog

## [1.1.2] - 2026-10-03

### Fixed

- `publication_kernel.py` reports a wrongly typed report field (`sources` as a string, a list where an object belongs, a non-string evidence ref or citation marker, a non-list action lane) as `FIELD_TYPE_INVALID:<field>` with exit 1 on every subcommand, instead of a Python traceback; `render-manifest` no longer writes a manifest for such a report.
- `scripts/run_evals.py` answers `--help` and rejects unknown arguments instead of ignoring them and running.

### Tests

- A case must now state all four results; a missing key used to default to the
  actual value. Added 19 cases (25-43): a non-object report, invalid protocol and
  mode (including an unhashable one), a missing master path, an invalid declared
  stage, a manuscript edited after hashing, HTML QA required but missing, no
  derived artifacts, one case per lifecycle step plus a stage declared past the
  gap, and the rendered manifest. Every well-shaped case also checks that
  `check_brief` accepts the manifest the report renders and rejects an edited
  one; like the CLI, the harness renders no manifest for a wrongly typed
  report. Seven malformed-field cases (44-50) cover the fix above. Held guards:
  37 of 59 -> 63 of 67 (the type checks above add eight guards).
- Both changes are covered by the 1.1.2 freeze exception in
  `docs/acceptance/longform-publisher-1.0.0.md`.

## [1.1.1] - 2026-10-02

### Changed

- Description is host-neutral (it read "Use when ChatGPT must") and states
  when not to use the skill, including the boundary with `ebook-publisher`.
  The front-door release line said 1.0.0 while `VERSION` said 1.1.0.
  No workflow, kernel or report-contract behaviour changed; see the freeze
  exception in `docs/acceptance/longform-publisher-1.0.0.md`.

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
