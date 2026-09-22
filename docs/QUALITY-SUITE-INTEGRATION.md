# Quality skill integration

This repository keeps one canonical skill tree under `skills/` and one routing
registry under `registry/skills.json`. The imported bundles are therefore
treated as package sources, not as a second repository architecture.

## Included sources

| Canonical skill IDs | Source | Version choice |
| --- | --- | --- |
| `content-roaster`, `science-roaster`, `repo-roaster` | CometWeb Roaster Suite | `6.0.0` |
| `artifact-acceptance`, `benchmark-curator`, `brief-architect`, `content-reviewer`, `content-writer`, `feedback-integrator`, `quality-loop-operator`, `repair-operator`, `rubric-designer`, `skill-auditor`, `skill-evaluator` | CometWeb Quality Skills | `1.7.0` |

The three roaster IDs also exist in the quality bundle. They are not copied a
second time: the dedicated Roaster Suite packages are the canonical source for
those IDs in this repository.

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
