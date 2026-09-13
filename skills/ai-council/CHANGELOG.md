# Changelog

## Unreleased — kernel 5.0.1, 2026-09-13

### Fixed
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

Package VERSION and registry remain unchanged. This is a private development change, not a release or host/model acceptance. The earlier 137-file overlay is not integrated by this change. See [kernel admission](references/kernel-admission.md) for migration and assurance limits.

## [5.1.1] - 2026-09-08

### Changed
- SKILL.md entrypoint loads only `workflow-light|standard|deep.md` by profile (context progressive disclosure).

## [5.1.0] - 2026-09-08

### Changed
- Documented LIGHT / STANDARD / DEEP cognitive profiles; LIGHT skips DEEP machinery by default.

