# Changelog

## 1.4.1 — 2026-09-12

- Reconcile the runtime bundle with main: preserve machine-readable source routing, ambiguity reporting, CRM authority-gap and confidential-summary guards.
- Keep public-claim verification ahead of generic social/content routing.

## 1.4.0 — 2026-09-12

- Add scoped currentness, evidence, safety and domain acceptance contracts.
- Normalize host metadata and verify standalone package structure.
- Reject path escape, parent-repository confusion, ambiguous timestamps, empty provenance and unsupported deltas; redact normal snapshot errors.

# Changelog — cometweb-context

## [1.3.0] - 2026-09-07

### Changed
- Split human-facing output from machine/downstream handoff: direct users now receive a compact operator brief while downstream agents retain the full ContextEnvelope.
- Defined that `full` controls retrieval breadth, not response verbosity.
- Added response budgets for targeted, standard/delta, and full modes and removed raw ContextEnvelope JSON from default user-facing output.
- Added anti-wall-of-text rules: no duplicated facts, no exhaustive source/task lists, no tables unless they improve compression, and no verbose process narration.
- Added explicit `DIRECT_USER`, `DOWNSTREAM`, and `DEBUG / EXPLICIT_DETAIL` output lanes.

## [1.2.0] - 2026-09-07

### Fixed
- Broadened skill trigger coverage for full CometWeb/portfolio, cross-project, Notion+GitHub, and "what changed" requests.
- Added a dedicated `portfolio` profile so whole-CometWeb requests no longer collapse into a single-product context plan.
- Added First Principles governance preflight for material product/GTM/pricing/portfolio decisions without turning context into a decision layer.
- Hardened ContextEnvelope validation: source/fact IDs, authority/access/sensitivity enums, timestamps, baseline, handoff, and optional governance state.
- Prevented local filesystem path leakage from repository snapshots by default.
- Made missing local CometWeb root a clean GitHub-fallback condition instead of a misleading repository failure.

### Improved
- Expanded claim-specific connector/source routing and CRM fallback rules.
- Added legacy decision-candidate handling guidance so advisory `D-xxx` labels are not mistaken for binding decisions.
- Added runtime behavior tests for portfolio routing, delta/full modes, governance preflight, envelope referential integrity, and repo snapshot privacy.

## [1.0.0] - 2026-08-30

### Added
- Read-only CometWeb context gateway with targeted, standard, delta, and full refresh modes.
- Provenance, freshness, authority, conflict, sensitivity, and fallback handling.
- Typed `ContextEnvelope` output contract for downstream skills.
- Deterministic context planner, repository snapshot helper, and envelope validator.
- Source registry and explicit separation between context, evidence, and downstream decisions.
