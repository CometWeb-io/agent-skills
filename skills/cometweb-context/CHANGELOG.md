# Changelog — cometweb-context

## [1.2.1] - 2026-09-08

### Changed
- Profile source groups loaded from source-registry.json.
- SKILL.md slimmed; operational bindings registry-first.


## [1.2.0] - 2026-09-08

### Changed
- Strict JSON Schema + semantic ContextEnvelope validator.
- repo_snapshot path redaction by default; remote ahead/behind freshness fields.
- Operational First Principles / D-xxx bindings deferred to source registry.
- OpenAI agent metadata: default_prompt + ./assets icon paths.


## [1.1.0] - 2026-09-07

### Changed

- Added CometWeb First Principles as a canonical decision-input source for material product/GTM/pricing/portfolio decisions.
- Planner now includes `vault-first-principles` for product and GTM profiles.
- Added explicit handling for D-028, FP-6, fast path, decision trace and legacy decision-candidate alias registry.
- Kept the skill read-only: it retrieves governance context but never allocates decisions or mutates the vault.

## [1.0.0] - 2026-08-30

### Added

- Read-only CometWeb context gateway with targeted, standard, delta, and full refresh modes.
- Provenance, freshness, authority, conflict, sensitivity, and fallback handling.
- Typed `ContextEnvelope` output contract for downstream skills.
- Deterministic context planner, repository snapshot helper, and envelope validator.
- Source registry and explicit separation between context, evidence, and downstream decisions.
