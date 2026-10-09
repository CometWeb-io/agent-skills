# Output contract

Return:

- `skill_id`, current version/commit, previous version when comparing, and audit mode;
- coverage by audit surface;
- findings with stable IDs, severity, locator, evidence, impact, falsifier, and repair direction;
- semantic-version verdict and direction-aware public contract compatibility;
- for breaking changes: migration guide state plus structured migration plan (`consumer_actions`, `rollback_ref`, `verification_cases`, before/after fixtures when available);
- unsupported or stale host compatibility claims, separating static shape from fresh real-host evidence;
- unknowns/deferred checks;
- package/eval/registry/documentation drift;
- when a regression spans versions, a bounded bisection result using only measurements with the same comparison fingerprint;
- next owner (`skill-creator`, `skill-evaluator`, `quality-loop-operator`, or none).

Never rewrite the audited skill inside the audit result unless a separate authorized update workflow invokes `skill-creator`. Never call a contract change breaking without considering input/output direction.

## Audit payload

`scripts/kernel.py` validates an audit record with exactly these fields;
`references/contract.json` declares them and `tooling/skill_contracts.py` checks
the kernel, this file and `evals/cases.json` against it.

```text
skill_id                            # non-empty
mode: LIGHT|STANDARD|DEEP|DELTA     # default STANDARD
version                             # semver (x.y.z with optional -pre/+build); a commit hash is not accepted
previous_version?                   # semver; version must be greater
baseline_version                    # DELTA only: required and different from version
contract_compatibility: BACKWARD_COMPATIBLE|BREAKING|UNKNOWN|NOT_APPLICABLE   # default NOT_APPLICABLE; UNKNOWN defers
migration_guide_present: true       # required for BREAKING
migration_plan:                     # required for BREAKING
  consumer_actions[]                # non-empty strings
  rollback_ref
  verification_cases[]              # non-empty strings
runtime_host_status?: STATIC_SHAPE_ONLY|REAL_HOST_VERIFIED|DEGRADED|UNSUPPORTED|UNKNOWN
runtime_support_claimed: true|false # true needs runtime_host_status REAL_HOST_VERIFIED
empirical_eval_required: true|false # true routes a PASS to skill-evaluator
package:
  skill_md_lines                    # integer >= 1; over 500 is a progressive-disclosure issue
  broken_references                 # integer >= 0, default 0; > 0 is an issue
  unresolved_dependencies           # integer >= 0, default 0; > 0 is an issue
  forbidden_artifacts               # integer >= 0, default 0; > 0 is an issue
  symlinks                          # integer >= 0, default 0; > 0 is an issue
  behavior_eval_cases               # integer >= 0, default 0; 0 is an issue
  negative_routing_cases            # integer >= 0, default 0; 0 is an issue
  runtime_host_claims[]             # strings; each must also be in runtime_verified_hosts
  runtime_verified_hosts[]
  branch_coverage?                  # number in [0, 1]; below 0.95 is an issue
  mutation_score?                   # number in [0, 1]; below 0.80 is an issue
checks[]:
  status: PASS|FAIL|UNKNOWN|N_A
  severity: BLOCKER|MAJOR|MINOR|NOTE    # default NOTE
  material: true|false              # material PASS/FAIL needs evidence; material UNKNOWN defers
  evidence[]                        # a FAIL at BLOCKER or MAJOR always needs it
  rationale                         # required for N_A
  # At least one check is required for a completed audit. An empty list is
  # never PASS; use a material UNKNOWN check or contract_compatibility UNKNOWN
  # when the audit is explicitly deferred.
deep_checks:                        # DEEP only; every key must be true
  topology_inventory
  trigger_overlap
  reference_integrity
  dependency_graph
  executable_coverage
  package_unpacked
  supply_chain
  host_claims
  version_contracts
```

The kernel returns `{status, errors[], issues[], unknown_material, next_skill}`,
also for a payload that is not an object (`payload:not-object`, with no issues
and zero unknowns).
`status` is `INVALID` (any error), `DEFER` (material unknowns), `CHANGES_REQUIRED`
(issues; `next_skill` is skill-creator) or `PASS`. A PASS also carries
`version_bump` (MAJOR, MINOR, PATCH or null when there is no previous version),
`migration_required` and `empirical_effectiveness_proven: false`. A non-string
value for any enum above is an error, not a crash.
