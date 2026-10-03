# Skill Audit Brief — example-summarizer 1.3.1

## Package identity

- skill_id: `example-summarizer`
- Version: 1.3.1 (previous 1.3.0), package source `example-org/example-skills@4b7e0d2`
- Mode: DEEP
- Audit verdict: PASS

## Coverage by audit surface

| Surface | Status | Evidence |
| --- | --- | --- |
| Discovery and routing precision | PASS | `evals/cases.json`: 24 positive, 6 negative routing cases |
| Instruction conflicts | PASS | `SKILL.md` read in full (142 lines); no competing precedence rule |
| Reference integrity | PASS | all 5 references resolve in the unpacked archive |
| Dependency graph | PASS | one helper, standard library only |
| Executable eval coverage | PASS | branch coverage 0.97, mutation score 0.86 on `4b7e0d2` |
| Supply chain | PASS | no install step, no network fetch in scripts |
| Host compatibility claims | PASS | runtime claim backed by run log `host-run-0412` |
| Package hygiene | PASS | unpacked `example-summarizer-1.3.1.zip`; 0 symlinks, 0 forbidden artifacts |
| Migration records | N_A | no contract change between 1.3.0 and 1.3.1 |

## Findings

### SA-001 — MINOR — Negative routing cases do not cover translation requests

- Severity: MINOR
- Locator: `evals/cases.json`
- Evidence: the 6 negative cases cover rewriting and proofreading, none covers translation.
- Impact: a translation request could reach this skill without a test noticing.
- Falsifier: searched the case file and the front-door rules for translation prompts; none. SURVIVES.
- Repair direction: add one negative translation case.

## Semantic version and contract compatibility

- Contract compatibility: BACKWARD_COMPATIBLE — only an optional input field was added (input direction widens).
- Version bump: PATCH (1.3.0 → 1.3.1). An added optional input usually justifies MINOR; noted, not a defect, because no consumer contract changes.

## Host compatibility claims

| Host | Status | Evidence |
| --- | --- | --- |
| example-host-a | REAL_HOST_VERIFIED | run log `host-run-0412` on 1.3.1, 2026-09-30 |

## Unknowns and deferred checks

- None.

## Package, eval, registry and documentation drift

- None found: the registry, `README.md` and the archive all state 1.3.1.

## Audit payload

```json
{
  "skill_id": "example-summarizer",
  "mode": "DEEP",
  "version": "1.3.1",
  "previous_version": "1.3.0",
  "contract_compatibility": "BACKWARD_COMPATIBLE",
  "runtime_host_status": "REAL_HOST_VERIFIED",
  "runtime_support_claimed": true,
  "empirical_eval_required": true,
  "package": {
    "skill_md_lines": 142,
    "broken_references": 0,
    "unresolved_dependencies": 0,
    "forbidden_artifacts": 0,
    "symlinks": 0,
    "behavior_eval_cases": 24,
    "negative_routing_cases": 6,
    "runtime_host_claims": ["example-host-a"],
    "runtime_verified_hosts": ["example-host-a"],
    "branch_coverage": 0.97,
    "mutation_score": 0.86
  },
  "checks": [
    {"status": "PASS", "severity": "MAJOR", "material": true, "evidence": ["archive: 5 of 5 references resolve"]},
    {"status": "FAIL", "severity": "MINOR", "material": false, "evidence": ["evals/cases.json: no translation negative"]},
    {"status": "N_A", "severity": "NOTE", "material": false, "rationale": "no contract change"}
  ],
  "deep_checks": {
    "topology_inventory": true,
    "trigger_overlap": true,
    "reference_integrity": true,
    "dependency_graph": true,
    "executable_coverage": true,
    "package_unpacked": true,
    "supply_chain": true,
    "host_claims": true,
    "version_contracts": true
  }
}
```

## Next owner

skill-evaluator — the structure passes; whether the skill improves summaries is not shown by this audit and needs a paired experiment. SA-001 can ride along to skill-creator.
