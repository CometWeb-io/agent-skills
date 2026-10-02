# Changelog — skill-orchestrator

## [1.1.2] - Unreleased

### Fixed

- Keep the vendored CW-AIP protocol packageable by linking to the public
  WhyKit integration guide instead of a repository-relative document.
- Clarify that multiagent envelope checks fail closed without schema support.
- Document the v1/v2 multiagent envelope gate, its `--final` flag and the
  `DecisionHandoff` to v2 kind mapping in the shared execution reference.

## [1.1.1] - 2026-09-08

### Changed
- tooling/sync_orchestrator.py keeps multiagent planner identical to canonical kernel.


## [1.1.0] - 2026-09-08

### Changed
- Added execution_mode: auto | single_thread | isolated_subagents.
- Multiagent package is now a thin alias, not a divergent planner.


## [1.0.0] - 2026-08-26

### Added

- Initial release: multi-skill workflow planning and CW-AIP sequencing
- `scripts/orchestrate_kernel.py` — deterministic archetype selection
- Routing eval cases and install script integration
