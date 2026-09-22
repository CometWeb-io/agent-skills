# Output contract

Return:
- candidate/baseline identity and exact candidate versions;
- frozen `rubric_hash`, `benchmark_hash`, suite/config hashes, host/model/harness identity, and exact execution configuration;
- execution status, case/run counts, skipped assertions, and exclusion reasons;
- candidate vs baseline success metrics plus same-case paired table (`baseline_only`, `candidate_only`, both pass, both fail);
- paired statistical result (`SIGNIFICANT_IMPROVEMENT`, `SIGNIFICANT_REGRESSION`, `NONINFERIOR`, `INCONCLUSIVE`, `INSUFFICIENT_DATA`) with test method, alpha, p-value when applicable, predeclared effect/non-inferiority margin, and number of pairs;
- stochastic stability result (`STABLE`, `FLAKY`, `INSUFFICIENT_DATA`) with runs/case, flaky fraction, instability index, and stability thresholds;
- any predeclared sequential-stop result and checkpoint actually used;
- trigger precision/recall and discovery-vs-forced invocation split;
- invariant regressions;
- token/cost/duration deltas and Pareto status when measured;
- result (`IMPROVED`, `NO_MATERIAL_CHANGE`, `TRADEOFF`, `REGRESSION`, `INSUFFICIENT_EVIDENCE`, or `DESIGN_READY`);
- promotion eligibility, claim scope, and which runtime evidence is still missing.

Never infer significant improvement from unpaired aggregate pass-rate deltas when a paired design is available. Never describe flaky or statistically inconclusive DEEP real-host evidence as promotion proof.
