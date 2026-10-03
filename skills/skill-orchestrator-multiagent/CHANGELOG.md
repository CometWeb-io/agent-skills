# Changelog — skill-orchestrator-multiagent

## [1.1.3] - 2026-10-03

### Security

- The untrusted-content contract is carried by `skill-orchestrator`, whose front door this alias loads first; `tooling/tests/test_untrusted_content_rules.py` checks that hand-off instead of duplicating the rules here.
- New `tests/front-door-rules.json` inventories every normative sentence in SKILL.md, so a rule cannot be dropped from the front door unnoticed.

### Fixed

- Reject an authorizing v2 verdict next to an unresolved gate: a `GO` or release
  `GO_WITH_CONTROLS` whose `gates` include `BLOCK` or `COUNSEL_REQUIRED` (any
  letter case), and a decision `GO` whose `human_approval` is `required`,
  `pending` or `denied`. Before this, an empty `blockers` list was enough for the
  gate to hand such an envelope to the next step, although
  `tooling/validate_envelope.py` rejected it.
- The shared `references/multiagent-execution.md` ran `scripts/orchestrate_multiagent_kernel.py` and `scripts/validate_envelope.py` as if they shipped with every orchestrator package; both exist only in `skill-orchestrator-multiagent`. Each command now changes into that package first, and the payload step says to fall back to `execution_mode=single_thread` when it is not installed. `tooling/tests/test_orchestrator_reference_commands.py` checks every command in both packages' references.

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
