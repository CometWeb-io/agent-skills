# Output contract

Return:
- candidate/baseline identity and exact candidate versions;
- frozen `rubric_hash`, `benchmark_hash`, suite/config hashes, host/model/harness identity, and exact execution configuration;
- execution status, case/run counts, skipped assertions, and exclusion reasons;
- candidate vs baseline success metrics plus same-case paired table (`baseline_only`, `candidate_only`, both pass, both fail);
- paired statistical result (`SIGNIFICANT_IMPROVEMENT`, `SIGNIFICANT_REGRESSION`, `NONINFERIOR`, `INCONCLUSIVE`, `INSUFFICIENT_DATA`, or `NOT_USED` when no paired analysis ran) with test method, alpha, p-value when applicable, predeclared effect/non-inferiority margin, and number of pairs;
- stochastic stability result (`STABLE`, `FLAKY`, `INSUFFICIENT_DATA`, or `NOT_USED`) with runs/case, flaky fraction, instability index, and stability thresholds;
- any predeclared sequential-stop result and checkpoint actually used;
- trigger precision/recall and discovery-vs-forced invocation split;
- invariant regressions;
- token/cost/duration deltas and Pareto status when measured;
- result (`IMPROVED`, `NO_MATERIAL_CHANGE`, `TRADEOFF`, `REGRESSION`, `INSUFFICIENT_EVIDENCE`, or `DESIGN_READY`);
- promotion eligibility, claim scope, and which runtime evidence is still missing.

Never infer significant improvement from unpaired aggregate pass-rate deltas when a paired design is available. Never describe flaky or statistically inconclusive DEEP real-host evidence as promotion proof.

## Experiment report payload

`scripts/kernel.py` validates an experiment report with exactly these fields;
`references/contract.json` declares them and `tooling/skill_contracts.py` checks
the kernel, this file and `evals/cases.json` against it. All hashes are 64
lowercase hex characters.

```text
skill_id
candidate_version
baseline_version                    # a prior version, or NO_SKILL
mode: STANDARD|DEEP                 # default STANDARD
execution_mode: SPEC_ONLY|LOCAL_DETERMINISTIC|REAL_HOST   # default SPEC_ONLY
rubric_hash
benchmark_hash
suite_hash
baseline_suite_hash                 # must equal suite_hash
declared_case_ids[]                 # unique non-empty strings
executed_case_ids[]                 # the same set as declared_case_ids
negative_control_count              # integer >= 1
discovery_case_count                # integer >= 1
forced_case_count                   # integer >= 1
runs_per_case                       # integer >= 1; REAL_HOST needs 3 (STANDARD) or 5 (DEEP)
runtime_executed: true|false        # must be false for SPEC_ONLY, true otherwise
uses_llm_judge: true|false
judge_agreement: {status}           # default {status: NOT_USED}
  status: CALIBRATED|NEEDS_REVIEW|INSUFFICIENT_DATA|NOT_USED
                                    # DEEP with uses_llm_judge needs CALIBRATED
pareto_status: FRONTIER|DOMINATED|UNKNOWN|NOT_COMPUTED   # default NOT_COMPUTED; DOMINATED is a TRADEOFF
paired_analysis: {status}           # default {status: NOT_USED}
  status: SIGNIFICANT_IMPROVEMENT|SIGNIFICANT_REGRESSION|NONINFERIOR|INCONCLUSIVE|INSUFFICIENT_DATA|NOT_USED
stability: {status}                 # default {status: NOT_USED}
  status: STABLE|FLAKY|INSUFFICIENT_DATA|NOT_USED
config: {host, model, harness_version, reasoning_effort?}           # REAL_HOST
baseline_config: {host, model, harness_version, reasoning_effort?}  # REAL_HOST; all four equal config
candidate:                          # not read for SPEC_ONLY
  passed                            # integers >= 0; passed <= total
  total                             # equal for candidate and baseline
  trigger_tp
  trigger_fp
  trigger_fn
  tokens?                           # number; with duration_s feeds the budget ratios
  duration_s?
baseline:                           # same keys as candidate
invariant_regressions               # integer >= 0, default 0; > 0 is a REGRESSION
promotion_policy:
  min_pass_rate_delta               # default 0.05
  trigger_precision_floor           # default 0.90
  trigger_recall_floor              # default 0.90
  max_token_ratio                   # default 1.50
  max_duration_ratio                # default 2.00
```

DEEP REAL_HOST runs also need a `paired_analysis` status other than NOT_USED
or INSUFFICIENT_DATA and a `STABLE` stability status. The kernel enforces judge
calibration only in DEEP; in STANDARD an uncalibrated judge is recorded but does
not block promotion, so report it as a limit on the claim.

The kernel returns `{status, errors[], promotion_eligible}`, plus
`paired_status` and `stability_status` (except on an INVALID SPEC_ONLY report)
and `empirical_claim_allowed` on some results: false for DESIGN_READY, true for
IMPROVED, NO_MATERIAL_CHANGE and a paired SIGNIFICANT_REGRESSION; treat a
missing value as false. `status` is `INVALID`,
`DESIGN_READY` (SPEC_ONLY; report the execution status as NOT_RUN),
`IMPROVED`, `NO_MATERIAL_CHANGE`, `TRADEOFF`, `REGRESSION` or
`INSUFFICIENT_EVIDENCE`. Measured results add `pass_rate_delta`,
`trigger_precision`, `trigger_recall`, `token_ratio` and `duration_ratio` as
far as they could be computed; a TRADEOFF names its `tradeoff`:
`FLAKY_BEHAVIOR`, `PARETO_DOMINATED`, `TRIGGER_QUALITY` or `RESOURCE_BUDGET`.
