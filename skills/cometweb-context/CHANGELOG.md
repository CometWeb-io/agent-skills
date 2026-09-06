# Changelog — cometweb-context

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
