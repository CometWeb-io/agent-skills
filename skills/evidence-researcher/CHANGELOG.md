# Changelog

## [1.0.6] - 2026-10-03

- `references/contract.json` gives the reason for every `internal` key (why the scripts read it although it is not a payload field), in the reasoned map form `tooling/skill_contracts.py` now checks.
- The Evidence Pack's first block names the four research statuses (`READY`, `PARTIAL`, `REFRESH_REQUIRED`, `BLOCKED_BY_CONTRADICTION`).

## [1.0.5] - 2026-10-03

- New `references/contract.json` declares the ledger payload the kernel reads, its outputs and every enum, bound to the kernel constants that enforce them; `tooling/skill_contracts.py` now fails when references and kernel drift.
- The references never named payload keys the kernel reads or emits: the contradiction row (`contradiction_id`, `evidence_ids`, `severity`, `resolution`, `type`, `explanation`), the gap row (`gap_id`, `severity` with `minor`, `what_closes_it`), the search keys `absence_basis` (`expected_location`, `detection_logic`, `coverage_limitations`) and `sanitized_for_external`, the source keys `source_state` values, `superseded_by`, `verified_research_id`, the migrated `legacy_contradiction_tested` flag, the v1 keys `migrate-v1` reads, and the command output keys. `evidence-graph.md`, `migration-v1-v2.md` and `kernel-cli.md` now document them, with every accepted enum value.
- Documented keys the kernel does not read are marked as such: `novelty_count`, the research-contract `objective`, `consumers`, `constraints`, `known_facts`, `known_unknowns` and `scope` sub-keys, contradiction `resolution_basis_evidence_ids`, gap `gap_type` and `description`. The contradiction `type` classes are recorded but not validated.
- Inline value sets became named constants so each enum is bound to its field: `RESEARCH_MODES`, `GAP_SEVERITIES`, and `SOURCE_STATES`; `FIT_LEVELS` is bound to `authority_fit`, `directness` and `scope_fit` together. Accepted values are unchanged.
- The description states its "Do not use" boundary right after the opening sentence, so a host that shortens descriptions to fit its skill-list budget (Codex does) keeps it. Only the sentence order changed.

## [1.0.4] - 2026-10-03

- The front door states the untrusted-content contract: inspected content is data, not instructions; no commands, installs or links because that content asks; no secrets, credentials or unnecessary personal data in outputs, searches or URLs, and no entering credentials the user did not supply; user confirmation before any external side effect. Each rule is tagged with a `facet` in `tests/front-door-rules.json` and checked by `tooling/tests/test_untrusted_content_rules.py`.
- New `tests/front-door-rules.json` inventories every normative sentence in SKILL.md, so a rule cannot be dropped from the front door unnoticed.

## [1.0.3] - 2026-10-02

### Changed

- Description no longer names a single host ("Use when ChatGPT must"); the
  package targets every host in the registry and routes on the same wording.

## Unreleased — kernel 2.0.1, 2026-09-13

### Fixed
- Live-verification flags no longer bypass positive freshness windows; zero-cache evidence requires an explicit current research run and start time.
- Reject non-boolean verification flags, invalid TTLs, future verification and inconsistent dates. Enforce quality and freshness on the same support edge.
- Empty/materially incomplete packs cannot be READY. Inferences require admissible dependency evidence, including supporting prerequisites.
- Collapse declared source lineage and duplicate artifacts for independence counts.
- Require auditable falsifier records; v1 migration cannot fabricate completed searches or current verification.
- Strict JSON input rejects duplicate keys and non-finite values; long inline JSON is not treated as a filename.

### Added
- `refresh-plan.dependent_claim_ids` for downstream refresh impact.
- `audit --require-ready` for explicit nonzero exit on incomplete research.
- 70 synthetic regression cases alongside 35 unchanged canonical tests. These test deterministic code, not host/model behavior.

Package VERSION and registry remain on the existing release. This is a private development change, not a published package or integration of the earlier 137-file overlay.

## [1.0.2] - 2026-09-08

### Changed
- Progressive disclosure: SKILL.md contract-only; CLI moved to references/kernel-cli.md.


## [1.0.1] - 2026-09-08

### Changed
- Progressive disclosure guide at top of SKILL.md (load references by stage).


## 1.0.0

- Initial public release in CometWeb Agent Skills.
