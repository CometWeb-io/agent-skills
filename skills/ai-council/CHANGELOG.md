# Changelog

## [5.2.0] - 2026-09-18

### Fixed

- Unknown provenance counted as independent confirmation, which SKILL.md and
  references/evidence-policy.md both forbid. `independence_grade` folded a
  missing `provider`/`model_family` into the literal string "unknown" and then
  compared it, so an adviser declaring nothing "differed" from one declaring a
  real provider and both scored I3. On `mean_independence_grade` that reads 0.75
  where the evidence supports 0.25 — a threefold overstatement of how much
  confirmation a panel actually provides, produced by a blank field. A pair is
  now compared only when both sides declare provider and model.

- A decision with three or more named options was labelled `binary`.
  `infer_decision_archetype` read the question text only and never looked at
  the `options` the caller supplied, so the contract carried three options and
  then described their shape wrongly. The generic `binary` fallback is now
  upgraded to `option_selection` when three or more options are given; a domain
  archetype such as `pricing` or `m_and_a` is left alone, because it drives
  specialist routing, and an explicit `decision_type` from the caller still wins.

- Retain every required gatekeeper even when the selected mode's budget is exceeded; normalize LIGHT to FAST and reject unknown modes.
- Preserve declared BLOCK constraints, reject missing required gates, prevent confidence from erasing critical gaps, and prevent TEST from bypassing unimplemented controls.
- Reject malformed gate primitives and missing binding confidence dimensions instead of silently clamping or omitting them.
- Require timezone-aware temporal inputs, honor expiry, reject future/conflicting observations and unknown policies, and avoid treating empty freshness input as clearance.
- Report missing/invalid watch observations as UNKNOWN; preserve all watch findings and request revalidation for stale or unobserved decisions.
- Inspect unresolved opposition even when the contradiction-test flag is false; empty/uncovered material claims are not ready.
- Exclude missing/invalid forecast probabilities instead of scoring them as zero; report invalid and unresolved counts.

### Added
- `gate --required-gates-json` and `--require-go`; CLI freshness defaults to UNKNOWN. The Python API retains its legacy default for compatibility.
- Bounded strict CLI JSON parsing, rejecting duplicate keys and non-finite values with a nonzero, non-payload error response.
- 89 synthetic regression cases alongside 38 unchanged canonical tests (including 12 existing subtests).

## [5.1.1] - 2026-09-08

### Changed
- SKILL.md entrypoint loads only `workflow-light|standard|deep.md` by profile (context progressive disclosure).

## [5.1.0] - 2026-09-08

### Changed
- Documented LIGHT / STANDARD / DEEP cognitive profiles; LIGHT skips DEEP machinery by default.
