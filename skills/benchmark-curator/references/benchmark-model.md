# Benchmark model

A benchmark is a versioned population of cases with taxonomy, difficulty, split, provenance and contamination state. Size alone is not representativeness.

## Input shape

This is the payload `scripts/kernel.py` validates, and the shape to build a
benchmark revision in. `tooling/tests/test_contract_docs_match_kernels.py`
fails if this section and the kernel drift apart.

```text
benchmark_id
revision
objective
target_skill
mode: STANDARD|DEEP                      # default STANDARD
required_classes[]: discovery|forced|negative-control|adversarial|regression
leakage_scan: {status, corpus_fingerprint}   # required in DEEP
  status: CLEAN|SUSPECT|CONTAMINATED     # result of the corpus-level scan
  corpus_fingerprint                     # 64 hex chars; required when CLEAN
cases[]:
  id                                     # unique
  class: discovery|forced|negative-control|adversarial|regression
  difficulty: easy|medium|hard|edge
  split: dev|holdout
  contamination_status: CLEAN|SUSPECTED|KNOWN   # this case's own exposure
  source_lane: SYNTHETIC|REAL_TASK|INCIDENT|USER_SUPPLIED
  provenance_ref                         # required unless source_lane is SYNTHETIC
  prompt                                 # unique after case and whitespace folding
  expected_behavior
  assertions[]                           # non-empty strings
```

Two vocabularies are intentional: a case's `contamination_status` records what
is known about that one case, while `leakage_scan.status` is the result of
scanning the whole corpus. A `SUSPECTED` or `KNOWN` case in the holdout makes
the benchmark `CONTAMINATED` regardless of the scan.

DEEP mode also requires at least `max(2, ceil(20% of cases))` holdout cases and
fails when one class holds more than 70% of the cases.

## Status

The first row that matches wins.

| Status | When |
| --- | --- |
| `READY_TO_FREEZE` | No errors; the result carries `benchmark_hash` over the canonical case set |
| `CONTAMINATED` | A contaminated holdout case, or a `CONTAMINATED` leakage scan |
| `NEEDS_REVISION` | A `SUSPECT` leakage scan, or DEEP mode without a leakage scan |
| `NEEDS_REBALANCE` | Only coverage problems: a missing required class, too small a holdout, or class dominance |
| `INVALID` | Anything else, including a malformed leakage status or fingerprint |

Run `python3 scripts/kernel.py benchmark.json` (or pipe the JSON on stdin). It
exits non-zero for any status other than `READY_TO_FREEZE`.
