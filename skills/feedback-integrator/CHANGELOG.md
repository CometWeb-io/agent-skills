# Changelog

## [1.7.1] - 2026-10-03

- `scripts/run_evals.py --help` exits 0 with a usage line instead of exit 2; any other argument is still rejected with exit 2 and the unrecognized argument named.
- Eval cases pin the invalid-record reason, the watch reason and the
  retirement reason, not only the status. Added promotion cases for every
  input rule (missing or equal versions, zero or boolean case counts, negative
  improvements or regressions, blank scope, a safety regression), timestamps
  that are not strings or carry no timezone, a duplicated record that must not
  add independence, and `min_count: 1`. Held guards: 23 of 33 -> 31 of 33.

## [1.7.0] - 2026-09-22

- Preserve minimized reproductions and bisection evidence when converting failures into regression proposals.
- Package version synchronized to 1.7.0; existing role boundaries remain unchanged.

## [1.6.0] - 2026-09-22

- Added the RUNTIME root-cause layer for host/model/version drift and rollout-only failures.

## [1.4.0] - 2026-09-21

### Changed
- Synchronized with Quality Skills v1.4 contracts, replay/cache semantics, quality-debt governance, and skill meta-quality handoffs where applicable.
- Preserved existing specialist ownership boundaries.


## [1.3.0] - 2026-09-21

### Added
- v1.3 governance/calibration integration and stronger quality-loop interoperability.

## [1.2.0] - 2026-09-21

### Added

- Added learning windows, CONFIRMED/FALSE_POSITIVE/RESOLVED/UNKNOWN outcomes and strict evaluation-plan requirements.
- Added batch-isolation rules and advanced progressive reference material without bloating the front-door SKILL.md.
- Expanded real-host specifications with two v1.2 behavior cases.

### Hardened

- Kept deterministic behavior, coverage, mutation, fuzz, routing and post-package regression gates mandatory.

## [1.1.0] - 2026-09-21

### Hardened

- Expanded deterministic behavior coverage and fail-closed malformed-input coverage.
- Added role-specific output/evaluation contracts instead of shared generic templates.
- Strengthened evidence provenance, freshness, candidate binding, severity calibration, and premature-completion guards where applicable.
- Added natural-discovery and negative-control real-host eval specifications.
- Verified deterministic clean packaging and post-unpack eval execution at suite level.

### Changed

- Tightened cross-skill ownership boundaries and routing signals for English and Polish prompts.
- Updated integration proposal to Quality Loop v1.1.0.

## [1.0.0] - 2026-09-21

### Added

- Public-quality first release of the CometWeb quality loop skill.
- Executable contract/eval harness and explicit neighboring-skill boundaries.

### Hardened

- Second-pass adversarial review after the 0.9.0 suite first passed.
- Stronger premature-completion, evidence-lane, and false-green guards where applicable.

## 1.6.0

- Added RUNTIME root-cause layer for host/model drift and rollout incidents.
