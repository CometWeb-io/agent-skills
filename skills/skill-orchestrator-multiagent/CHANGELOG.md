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
- Apply the CW-AIP v1 kind schemas in `validate_envelope.py`: an
  `EvidenceEnvelope` or `DecisionHandoff` is checked against its bundled kind
  schema, so a missing `research_contract`, `material_claims` or `verdict` fails
  between steps. A missing bundled kind schema fails closed instead of falling
  back to the core schema.
- Reject an authorizing verdict that lists blockers: v1 `DecisionHandoff` and v2
  `ReleaseEnvelope` with `GO` or `GO_WITH_CONTROLS`, and v2 `DecisionEnvelope`
  with `GO`.
- Declare `referencing` in `RUNTIME.json`: the validator imports it directly to
  resolve the bundled kind schemas (it was only present as a `jsonschema`
  dependency).

## [1.0.0] - 2026-08-26

### Added

- Multiagent orchestrator: one subagent per specialist skill via Task/subagent API
- `orchestrate_multiagent_kernel.py` — subagent task payload builder
- Mirrored `orchestrate_kernel.py` for standalone ZIP installs
