# Changelog

## [1.7.1] - 2026-10-03

- `scripts/run_evals.py --help` exits 0 with a usage line instead of exit 2; any other argument is still rejected with exit 2 and the unrecognized argument named.

## [1.7.0] - 2026-09-22

- Preserve paired/stability evidence through EvaluationResultV17 and require it for advanced rollout.
- Package version synchronized to 1.7.0; existing role boundaries remain unchanged.

## [1.6.0] - 2026-09-22

- Added skill runtime lifecycle coordination for canary/staged/full rollout, rollback, deprecation, compatibility, and observation windows.

## [1.4.0] - 2026-09-21

### Changed
- Synchronized with Quality Skills v1.4 contracts, replay/cache semantics, quality-debt governance, and skill meta-quality handoffs where applicable.
- Preserved existing specialist ownership boundaries.


## [1.3.0] - 2026-09-21

### Added
- Initial quality-loop control plane.
- Frozen policy-lock enforcement for DEEP/DELTA.
- Candidate/contract lineage checks.
- Reviewer-roaster conflict state.
- Profile-specific next-stage selection.
- Repository handoff boundary to release-readiness.
- Campaign/batch isolation guidance.

## 1.6.0

- Added post-evaluation skill runtime lifecycle: compatibility, canary, staged/full rollout, rollback and deprecation state.
