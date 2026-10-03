# Improvement backlog — content skills, window ending 2026-10-03

## Status

PROPOSED

- as_of 2026-10-03T09:00:00+02:00, learning window 60 days, min_count 2.
- `scripts/kernel.py` (`evaluate_case`) on the payload below: PROPOSED, 1 proposal, 1 watch, 1 retired, 0 invalid.

## Observations

| ID | Pattern | Skill | Run | Context | Severity | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| OBS-01 | pricing claim without source | content-writer 2.3 | run-111 | CTX-01 | MAJOR | CONFIRMED |
| OBS-02 | pricing claim without source | content-writer 2.3 | run-118 | CTX-02 | MAJOR | CONFIRMED |
| OBS-03 | pricing claim without source | content-writer 2.4 | run-124 | CTX-03 | MINOR | CONFIRMED |
| OBS-04 | routing miss on golden-set prompts | router | run-125 | CTX-04 | MINOR | CONFIRMED |
| OBS-05 | table header dropped in export | longform export | run-061 | CTX-05 | MINOR | CONFIRMED |

## Proposals

### P-01 — pricing claim without source

- Independence: 3 contexts (CTX-01, CTX-02, CTX-03), 3 runs, across two writer versions.
- Severity: MAJOR. Root layer: INSTRUCTION.
- Evidence: OBS-01, OBS-02, OBS-03 (reviewer findings on three unrelated briefs).
- Causal hypothesis: the writer's evidence step covers statistics but not prices, so price statements pass without a source.
- Affected skills: content-writer.
- Change: add "prices and plan limits" to the claims that need a cited source in the evidence step.
- Expected effect: no uncited price claim reaches review in the next 10 runs.
- Blast radius: content-writer only; no shared reference changes.
- Compatibility risk: low; existing briefs gain one check.
- Regression test: REG-01, a price claim without a cited source fails review.
- Lifecycle: PROPOSED (not implemented).

## Watch

- routing miss on golden-set prompts — Reason: insufficient-independent-contexts. One context (CTX-04, OBS-04). Test gap owned by the skills maintainer.

## Retired

- table header dropped in export — Reason: outside-learning-window. Last seen 2026-06-02 (OBS-05, CTX-05); kept as history, not policy.

## Invalid observations

- None.

## Mutation boundary

Proposals only. No skill, registry entry or test was modified in this run; P-01 needs an explicit request before anyone edits content-writer.

```json
{
  "operation": "integrate",
  "input": {
    "as_of": "2026-10-03T09:00:00+02:00",
    "window_days": 60,
    "min_count": 2,
    "records": [
      {"pattern": "pricing claim without source", "severity": "MAJOR", "root_layer": "INSTRUCTION", "context_id": "CTX-01", "run_id": "run-111", "observed_at": "2026-09-12T10:00:00+02:00", "evidence": ["OBS-01"], "regression_test": {"id": "REG-01", "assertion": "a price claim without a cited source fails review"}},
      {"pattern": "pricing claim without source", "severity": "MAJOR", "root_layer": "INSTRUCTION", "context_id": "CTX-02", "run_id": "run-118", "observed_at": "2026-09-20T15:30:00+02:00", "evidence": ["OBS-02"]},
      {"pattern": "pricing claim without source", "severity": "MINOR", "root_layer": "INSTRUCTION", "context_id": "CTX-03", "run_id": "run-124", "observed_at": "2026-09-29T08:45:00+02:00", "evidence": ["OBS-03"]},
      {"pattern": "routing miss on golden-set prompts", "severity": "MINOR", "root_layer": "ROUTING", "context_id": "CTX-04", "run_id": "run-125", "observed_at": "2026-09-30T12:00:00+02:00", "evidence": ["OBS-04"], "test_gap": {"assertion": "golden-set prompts route to benchmark-curator", "owner": "skills maintainer"}},
      {"pattern": "table header dropped in export", "severity": "MINOR", "root_layer": "KERNEL", "context_id": "CTX-05", "run_id": "run-061", "observed_at": "2026-06-02T09:00:00+02:00", "evidence": ["OBS-05"]}
    ]
  }
}
```
