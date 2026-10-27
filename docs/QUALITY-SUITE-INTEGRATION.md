# Quality skill integration

This repository keeps one canonical skill tree under `skills/` and one routing
registry under `registry/skills.json`. The imported bundles are therefore
treated as package sources, not as a second repository architecture.

## Included sources

| Canonical skill IDs | Source | Current package version |
| --- | --- | --- |
| `content-roaster` (compatibility alias) | CometWeb Roaster Suite | `7.0.0` |
| `repo-roaster` | CometWeb Roaster Suite | `6.2.0` |
| `science-roaster` | CometWeb Roaster Suite | `6.2.0` |
| `artifact-acceptance` | CometWeb Quality Skills | `1.7.6` |
| `benchmark-curator` | CometWeb Quality Skills | `1.7.5` |
| `content-reviewer` | CometWeb Quality Skills | `1.8.0` |
| `content-writer` | CometWeb Quality Skills | `1.7.7` |
| `quality-loop-operator` | CometWeb Quality Skills | `1.8.0` |
| `repair-operator` | CometWeb Quality Skills | `1.7.7` |
| `rubric-designer` | CometWeb Quality Skills | `1.7.7` |
| `brief-architect` | CometWeb Quality Skills with experimental PRD profile | `1.9.0` |
| `feedback-integrator` | CometWeb Quality Skills | `1.8.2` |
| `skill-auditor` | CometWeb Quality Skills | `1.7.6` |
| `skill-evaluator` | CometWeb Quality Skills | `1.8.1` |

The three roaster IDs also exist in the quality bundle. They are not copied a
second time: the dedicated Roaster Suite packages are the canonical source for
those IDs in this repository.
The Roaster Suite was imported at `6.1.4`; the table follows current package
versions, including later fixes and explicit experimental distribution metadata.
All three roasters default to compact evidence-backed prose. Their
full v6 contracts remain available when a receiving workflow requires them;
routine reviews do not require role transcripts or separate ledgers.

## Deliberately excluded

The bundles' root-level release manifests, CI workflows, validation orchestrators,
and suite-level publication files are not imported. Copying them would create a
second source of truth, duplicate checks, and unnecessary hosted-run cost. Each
skill's own `SKILL.md`, references, scripts, fixtures, tests, license, changelog,
version, icon, and host adapter remain inside its package directory.

The repository's registry, generated adapters, marketplace manifests, local
validator, public-safety checks, and existing low-cost validation workflow remain
the publication contract. A passing local test suite proves package invariants;
it does not prove behavioral improvement on every live model or host.

Content review now has one canonical instruction owner: `content-reviewer`.
`content-roaster` selects its ADVERSARIAL profile and retains v6 helper paths.
The review/v1 and roaster/v6 contracts remain distinct; see
[compatibility and migration](CONTENT-REVIEW-COMPATIBILITY.md).
