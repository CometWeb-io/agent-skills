# Changelog

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
