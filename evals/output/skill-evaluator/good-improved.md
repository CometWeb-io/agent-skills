# Skill evaluation — example-summarizer 1.4.0 vs 1.3.1

## Candidate and baseline

- Skill: `example-summarizer`
- Candidate: 1.4.0 (archive `example-summarizer-1.4.0.zip`)
- Baseline: 1.3.1 (prior version)
- Mode: STANDARD

## Frozen experiment contract

- rubric_hash: `49672f0ef3b3a542b3b86b475936cc9adf1ddf60369e9b120ba33900294c99d8`
- benchmark_hash: `1b32c28cb38c05480eccc1bd60ff97029b57a05c96718b96dad7e9d84894f549`
- suite_hash (candidate and baseline): `f8ebd43dbef1f029bf4930c65c9b7c5cc76af476927cee861ff18fcc73bfc4ab`
- Host/model/harness: example-host-a, example-model-2, harness 0.9.3, reasoning effort medium — identical for both arms.
- Exclusions predeclared before execution: none.

## Execution status

- Execution status: EXECUTED (REAL_HOST), 2026-09-28 to 2026-09-29
- Cases: 12 declared, 12 executed (EC-01 to EC-12); 3 runs per case, 36 runs per arm
- Skipped assertions: 2 — the length assertion in EC-07 could not be graded in either arm (the host truncated the transcript); recorded as skipped, not failed.
- Run log: `runs/2026-09-28-summarizer/` (72 transcripts)

## Success metrics and paired table

| Metric | Candidate | Baseline | Source |
| --- | --- | --- | --- |
| Pass rate | 33/36 (91.7%) | 24/36 (66.7%) | run log, deterministic graders |
| Pass-rate delta | +0.25 | — | computed from the rows above |

| Same-case outcome (runs) | Count |
| --- | --- |
| both pass | 23 |
| candidate_only | 10 |
| baseline_only | 1 |
| both fail | 2 |

## Paired statistical result

- Status: SIGNIFICANT_IMPROVEMENT
- Method: exact McNemar on 36 paired runs, alpha 0.05, p = 0.012; predeclared minimum effect +0.05.

## Stochastic stability

- Status: STABLE
- 3 runs per case; flaky fraction 0/12 cases; instability index 0.03; thresholds: flaky fraction ≤ 0.10, index ≤ 0.10.

## Trigger precision and recall

- Candidate precision 18/19 (0.947), recall 18/19 (0.947); floors 0.90 / 0.90.
- Discovery cases: 6; forced-invocation cases: 6; negative controls: 4 (one false trigger, EC-11).

## Invariant regressions

- None: the 3 invariant assertions passed in every candidate run.

## Resource deltas and Pareto status

- Tokens: 1.20× baseline (budget 1.50×). Duration: 1.10× baseline (budget 2.00×).
- Pareto status: FRONTIER.

## Result

IMPROVED

Model-judge agreement was CALIBRATED (adjudicated agreement 0.91 on the 8 judged assertions).

```json
{
  "skill_id": "example-summarizer",
  "candidate_version": "1.4.0",
  "baseline_version": "1.3.1",
  "mode": "STANDARD",
  "execution_mode": "REAL_HOST",
  "rubric_hash": "49672f0ef3b3a542b3b86b475936cc9adf1ddf60369e9b120ba33900294c99d8",
  "benchmark_hash": "1b32c28cb38c05480eccc1bd60ff97029b57a05c96718b96dad7e9d84894f549",
  "suite_hash": "f8ebd43dbef1f029bf4930c65c9b7c5cc76af476927cee861ff18fcc73bfc4ab",
  "baseline_suite_hash": "f8ebd43dbef1f029bf4930c65c9b7c5cc76af476927cee861ff18fcc73bfc4ab",
  "declared_case_ids": ["EC-01", "EC-02", "EC-03", "EC-04", "EC-05", "EC-06", "EC-07", "EC-08", "EC-09", "EC-10", "EC-11", "EC-12"],
  "executed_case_ids": ["EC-01", "EC-02", "EC-03", "EC-04", "EC-05", "EC-06", "EC-07", "EC-08", "EC-09", "EC-10", "EC-11", "EC-12"],
  "negative_control_count": 4,
  "discovery_case_count": 6,
  "forced_case_count": 6,
  "runs_per_case": 3,
  "runtime_executed": true,
  "uses_llm_judge": true,
  "judge_agreement": {"status": "CALIBRATED"},
  "pareto_status": "FRONTIER",
  "paired_analysis": {"status": "SIGNIFICANT_IMPROVEMENT"},
  "stability": {"status": "STABLE"},
  "config": {"host": "example-host-a", "model": "example-model-2", "harness_version": "0.9.3", "reasoning_effort": "medium"},
  "baseline_config": {"host": "example-host-a", "model": "example-model-2", "harness_version": "0.9.3", "reasoning_effort": "medium"},
  "candidate": {"passed": 33, "total": 36, "trigger_tp": 18, "trigger_fp": 1, "trigger_fn": 1, "tokens": 61200, "duration_s": 742},
  "baseline": {"passed": 24, "total": 36, "trigger_tp": 17, "trigger_fp": 2, "trigger_fn": 2, "tokens": 51000, "duration_s": 675},
  "invariant_regressions": 0,
  "promotion_policy": {"min_pass_rate_delta": 0.05, "trigger_precision_floor": 0.9, "trigger_recall_floor": 0.9, "max_token_ratio": 1.5, "max_duration_ratio": 2.0}
}
```

## Promotion eligibility and claim scope

- Promotion eligible: yes
- Claim scope: example-host-a with example-model-2, harness 0.9.3, reasoning effort medium, runs from 2026-09-28 to 2026-09-29. Other hosts and models were not run.
- Missing runtime evidence: a second host; a DEEP run (5 runs per case) before a major-version claim.
