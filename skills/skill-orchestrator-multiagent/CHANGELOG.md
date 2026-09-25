# Changelog — skill-orchestrator-multiagent

## [1.1.2] - Unreleased

### Fixed

- Bundle the core CW-AIP envelope schema and fail closed when it or `jsonschema`
  is unavailable, including after package relocation.
- State the required sibling `skill-orchestrator` installation explicitly.

## [1.0.0] - 2026-08-26

### Added

- Multiagent orchestrator: one subagent per specialist skill via Task/subagent API
- `orchestrate_multiagent_kernel.py` — subagent task payload builder
- Mirrored `orchestrate_kernel.py` for standalone ZIP installs
