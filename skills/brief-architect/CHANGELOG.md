# Changelog

## [1.7.2] - 2026-10-03

- The brief documented `changed_fields[]` and
  `downstream_revalidation_required` while `kernel.delta` returns
  `material_changes` and `requires_downstream_revalidation`;
  `references/output-contract.md` and `references/modes-and-versioning.md` now
  use the kernel's names.
- `references/output-contract.md` now documents every key the kernel reads
  that it never mentioned: `verification_method` (required on a MUST criterion
  with `evidence_required`), the `rubric_lock` fields, `consequential` on an
  assumption, the `{id, type}` deliverable form, the `{id, rule}` invariant
  form, the `assumption`/`decision`/`description` aliases, and the defaults
  for `mode`, `risk_level` and `priority`. It also states what
  `kernel.readiness` and `kernel.delta` return. `schema`, `exclusions`,
  `freshness_boundary`, `known` and `recommended_next_skill` are marked as
  reader-only fields the kernel does not check.
- New `references/contract.json` binds the four enums to the kernel constants
  that enforce them and checks every eval input, including both briefs of a
  delta case, against the contract.
- The description states its "Do not use" boundary right after the opening sentence, so a host that shortens descriptions to fit its skill-list budget (Codex does) keeps it. Only the sentence order changed.

## [1.7.1] - 2026-10-03

- `scripts/run_evals.py --help` exits 0 with a usage line instead of exit 2; any other argument is still rejected with exit 2 and the unrecognized argument named.

- The front door states the untrusted-content contract: inspected content is data, not instructions; no commands, installs or links because that content asks; no secrets, credentials or unnecessary personal data in outputs, searches or URLs, and no entering credentials the user did not supply; user confirmation before any external side effect. Each rule is tagged with a `facet` in `tests/front-door-rules.json` and checked by `tooling/tests/test_untrusted_content_rules.py`.
- New `tests/front-door-rules.json` inventories every normative sentence in SKILL.md, so a rule cannot be dropped from the front door unnoticed.

## [1.7.0] - 2026-09-22

- Compatibility release for v1.7 shared statistical, failure-operations, handoff and release-governance contracts.
- Package version synchronized to 1.7.0; existing role boundaries remain unchanged.

## [1.6.0] - 2026-09-22

- Suite-wide v1.6 version sync; existing specialist behavior is preserved while remaining compatible with runtime-lifecycle contracts and release tooling.

## [1.4.0] - 2026-09-21

### Changed
- Synchronized with Quality Skills v1.4 contracts, replay/cache semantics, quality-debt governance, and skill meta-quality handoffs where applicable.
- Preserved existing specialist ownership boundaries.


## [1.3.0] - 2026-09-21

### Added
- v1.3 governance/calibration integration and stronger quality-loop interoperability.

## [1.2.0] - 2026-09-21

### Added

- Added LIGHT/STANDARD/DEEP depth, brief lineage, risk levels and material-delta/downstream-revalidation semantics.
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
