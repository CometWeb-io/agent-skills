# Output contract

Return a compact human brief plus, when supported, a machine sidecar.

Human brief default:

1. `STATE`
2. `POLICY LOCK`
3. `CONFLICTS`
4. `MEASUREMENT` — rubric/benchmark identity plus paired/stability state when the profile measures a skill
5. `RUNTIME LIFECYCLE` — compatibility, host support, rollout state, observation window, rollback/deprecation state when applicable
6. `NEXT STAGE`
7. `REVALIDATE`
8. `BLOCKER`
9. `DONE WHEN`

Machine sidecar fields. This list is the payload `scripts/kernel.py` validates;
`references/contract.json` declares it and `tooling/skill_contracts.py` checks
the kernel, this file and `evals/cases.json` against it. Five fields (`schema`,
`run_id`, `coverage`, `revalidate`, `completion_evidence`) belong in the
sidecar for the reader; the kernel does not check them.

```text
schema
run_id
profile: EDITORIAL|SALES|TECHNICAL_DOCS|RESEARCH|REPO_DEEP|SKILL_QUALITY
mode: LIGHT|STANDARD|DEEP|DELTA     # default STANDARD
as_of                               # timezone-aware ISO time; required when quality_debt is non-empty
candidate_id
base_candidate_id?                  # required and distinct from candidate_id in DELTA
contract_id
policy_lock: {pack_id, revision, sha256, locked_before_evaluation: true}
                                    # required in DEEP and DELTA; sha256 is 64 lowercase hex
adaptive_depth?: {recommended_mode, override_approved?, override_rationale?}
  recommended_mode: LIGHT|STANDARD|DEEP|DELTA   # must equal mode unless an approved override has a rationale
replay_status?: REPRODUCIBLE|DRIFT|INCOMPLETE   # DRIFT or INCOMPLETE blocks on revalidation
cache_reuse[]?:
  decision: REUSE|RECOMPUTE
  fingerprint_match: true           # required for REUSE
  source_status: PASS               # required for REUSE
quality_debt[]?:
  candidate_id?                     # must equal the run candidate_id when present
  severity: BLOCKER|MAJOR|MINOR|NOTE
  status: OPEN|CLOSED|SUPERSEDED
  kind?: FINDING|WAIVER|CONTROL|TEST_GAP|EVIDENCE_GAP
  due_at?                           # timezone-aware ISO time
  closure_evidence                  # required for CLOSED
stages[]:
  skill                             # a stage of the active profile, at most once, in profile order
  state: PENDING|RUNNING|PASS|CHANGES_REQUIRED|BLOCKED|DEFER|SKIPPED
  candidate_id?                     # must equal the run candidate_id when present
  contract_id?                      # must equal the run contract_id when present
  skip_allowed: true                # required for SKIPPED, with skip_rationale; DEEP never skips
  skip_rationale
  rubric_hash                       # SKILL_QUALITY: rubric-designer, benchmark-curator, skill-evaluator
  benchmark_hash                    # SKILL_QUALITY: benchmark-curator, skill-evaluator
  result: IMPROVED|NO_MATERIAL_CHANGE|TRADEOFF|REGRESSION|INSUFFICIENT_EVIDENCE|DESIGN_READY
                                    # skill-evaluator stage only
reconciliation[]?:
  candidate_id?
  status: CONSENSUS|NEAR_CONSENSUS|CONFLICT|UNIQUE
  resolved: true|false              # an unresolved CONFLICT returns NEEDS_RECONCILIATION
  resolution_basis                  # required when resolved
runtime_lifecycle?:
  state: NOT_REQUESTED|READY_FOR_CANARY|CANARY_RUNNING|READY_FOR_STAGED|STAGED_RUNNING|READY_FOR_FULL|FULL|ROLLBACK_REQUIRED|DEPRECATED|BLOCKED
  contract_compatibility: BACKWARD_COMPATIBLE|BREAKING|UNKNOWN
  host_support: REAL_HOST_VERIFIED|STATIC_SHAPE_ONLY|DEGRADED|UNSUPPORTED|UNKNOWN
  stability_status: STABLE|FLAKY|INSUFFICIENT_DATA|NOT_USED
  paired_status: SIGNIFICANT_IMPROVEMENT|SIGNIFICANT_REGRESSION|NONINFERIOR|INCONCLUSIVE|INSUFFICIENT_DATA|NOT_USED
  material_change: true|false
  canary_passed: true|false         # required for staged/full rollout of a material change
  observation_runs?                 # integer >= 0, default 0
  min_observation_runs?             # integer >= 1, default 20
  rollback_version                  # required for a material change
  rollback_executable: true         # required for ROLLBACK_REQUIRED
  major_version_bump: true          # required for BREAKING
  migration_guide_present: true     # required for BREAKING
  removing_public_contract: true|false
  deprecation_record                # required when removing_public_contract
  deprecation_notice                # required for DEPRECATED
coverage
revalidate[]
completion_evidence[]
```

The skill names a stage may carry, in order, per profile (`references/profiles.md`):

- `EDITORIAL`, `SALES`, `TECHNICAL_DOCS`: brief-architect, content-writer, content-reviewer, content-roaster, repair-operator, artifact-acceptance
- `RESEARCH`: brief-architect, content-writer, content-reviewer, science-roaster, repair-operator, artifact-acceptance
- `REPO_DEEP`: repo-roaster, repair-operator
- `SKILL_QUALITY`: skill-auditor, rubric-designer, benchmark-curator, skill-evaluator
 In `SKILL_QUALITY`, a PASS benchmark and a PASS
evaluator stage must carry the same `rubric_hash` (and the evaluator the same
`benchmark_hash`) as the stages they consume.

To check a sidecar, call `validate(payload)` in `scripts/kernel.py`. It returns
`{status, next_stage, errors[], unresolved_conflicts, blocking_quality_debt}`
(a payload that is not an object is `INVALID` with `payload:not-object` and
zero counts),
plus `software_release_verdict: NOT_OWNED` for a complete `REPO_DEEP` run and
`skill_evaluation_result` and `rollout_status` for `SKILL_QUALITY`. `status` is
one of `INVALID`, `BLOCKED`, `NEEDS_RECONCILIATION`, `READY_FOR_NEXT`,
`CHANGES_REQUIRED`, `READY_FOR_ROLLOUT` or `COMPLETE`. An off-list token in any
enum above is an error, not a silent fallback: a lower-case `conflict` would
otherwise never count as a conflict, and a lower-case `waiver` would never
expire into blocking debt.

For `SKILL_QUALITY`, preserve evaluator `paired_status` and `stability_status` into runtime lifecycle governance. READY_FOR_FULL/FULL cannot be reconstructed from prose if these fields are missing. A sidecar records orchestration truth; it does not replace specialist evidence.
