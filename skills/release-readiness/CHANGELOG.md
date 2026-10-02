# Changelog

## [1.3.0] - 2026-10-02

### Changed

- Front door cut from 16.7 KB to 11.1 KB. Each workflow step now names the
  reference to open and when; detail that SKILL.md repeated from its references
  (evidence fields, specialist routing, revalidation and delta lists, output
  fields) lives only there. The red-team checklist moved to the new
  `references/red-team.md`, read before every final verdict; release context to
  capture moved to `references/risk-routing.md`; the list of engine guarantees
  moved to `references/manifest-schema.md`.
- `tests/front-door-rules.json` inventories every MUST/NEVER/gate and where it
  lives; `tooling/tests/test_front_door_rules.py` fails if one is dropped,
  reworded, or left behind a pointer with no load trigger.
- The description also sends site/app QA with no named candidate to Web App
  Auditor.

### Fixed

- SKILL.md named the scope field `commercial_model`; the engine reads
  `scope.commercial` and ignored the other key, so a manifest written from the
  skill lost its answer — `paid` became `unknown` and the billing gate was never
  derived. SKILL.md now uses `scope.commercial`, and the engine accepts
  `commercial_model` as an alias and rejects the two keys disagreeing.

## [1.2.1] - 2026-10-02

### Changed

- The description now sends knowledge deliverables (reports, ebooks) to
  Artifact Acceptance. "Artifact" in the candidate list read as any artifact,
  so a request to gate a document could select a software release gate.
- `INSTALL.md` pointed at `scripts/package-releases.sh`, which does not exist;
  it now names `tooling/package_skill.py`. The heading no longer carries a
  stale version.

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
