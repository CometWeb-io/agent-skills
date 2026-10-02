# Changelog — skill-orchestrator-multiagent

## [1.1.2] - Unreleased

### Fixed

- Bundle the core CW-AIP envelope schema and fail closed when it or `jsonschema`
  is unavailable, including after package relocation.
- State the required sibling `skill-orchestrator` installation explicitly.
- Accept CW-AIP v2 envelopes in `validate_envelope.py`: dispatch on
  `protocol_version`, check the bundled v2 core schema, recompute `payload_hash`,
  and add `--final` to reject the `pending` draft marker. A step planned as
  `DecisionHandoff` accepts a v2 `DecisionEnvelope` or `ReleaseEnvelope`.
  Unknown protocol versions now fail with a direct message.

## [1.0.0] - 2026-08-26

### Added

- Multiagent orchestrator: one subagent per specialist skill via Task/subagent API
- `orchestrate_multiagent_kernel.py` — subagent task payload builder
- Mirrored `orchestrate_kernel.py` for standalone ZIP installs
