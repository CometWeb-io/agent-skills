# Changelog

## [1.2.0] - 2026-09-18

### Fixed

- `SKILL.md` told an agent to write `library consumers` and `not applicable`,
  which are prose spellings of the engine enums `library_consumers` and
  `not_applicable`. A context file built by following the skill was rejected
  before assessment could start. `references/manifest-schema.md` had it right;
  the file an agent reads first did not.
- The risk flags were listed in prose ("major infrastructure change"), not as
  the `scope.risk_flags` keys the engine requires — two of the eleven are not
  guessable (`major_infra_change`, `legal_or_regulatory_change`) — and nothing
  said they nest under `risk_flags` at all. Keys and shape are now shown.
- `bootstrap_manifest.py` silently discarded unrecognised keys placed directly
  on `scope`, so answered risk flags came back as `unknown` and an operator who
  had resolved the risk scope saw a manifest claiming otherwise. Unrecognised
  keys now fail with the offending names and the valid list, the way an invalid
  `audience` already did.

## 1.1.0 — unreleased candidate

- Engine 2.1.0 rejects prefix-only, mutable-label and mismatching candidate binding;
  verified evidence requires the exact environment and all pinned immutable IDs.
- Reject null metadata, invalid boolean coercion, malformed/expired timestamps,
  conflicting observation times, duplicate JSON keys and non-finite arithmetic.
- Apply engine-owned minimum evidence floors; include positive nonbinding checks
  in evidence admission; never hide material unknowns through scoring weights.
- Compare raw scores/coverage against thresholds; normalize large finite weights.
- Freeze assessment requirements through an independently stored contract hash;
  previous-manifest reviews freeze by default. Report scope/context changes,
  removed findings and unverified findings separately from actual resolutions.
- Preserve input manifests and existing result files; local output writes are
  immutable and idempotent for identical contents.
- Bootstrap uses the same evidence floors and strict loader. All generated checks
  remain unknown with empty evidence.
- Canonical engine test assertions are retained; the positive fixture now uses a
  full commit ID and explicitly records its production environment. Tests are
  synthetic decision-engine checks, not model or deployment acceptance.

## 1.0.0

- Initial public release in CometWeb Agent Skills.
