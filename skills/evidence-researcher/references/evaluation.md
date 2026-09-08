# Evaluation and Champion/Challenger

## Primary objective

Measure evidence correctness and error-catching, not prose length or source count.

## Invariants

A candidate version regresses if it violates any of these:

- material current claim can become ready without timezone-aware `as_of`,
- live-verification class can become current without run-specific inspection,
- an INFERENCE can be marked `VERIFIED`,
- a material claim can claim contradiction coverage without a falsifier record,
- a critical unresolved contradiction can produce `READY`,
- derivative/syndicated sources can inflate independence,
- v2 evidence edge can reference missing claim/source,
- claim dependency cycle is accepted,
- old pack snapshot is overwritten during refresh,
- `verified_for_research` is treated as Council `verified_for_decision`,
- a stale accepted source makes a claim stale despite a separate current authoritative accepted support edge,
- a failed generic search is treated as evidence of absence without an `ABSENCE_TEST` design.

## Metrics

### Claim decomposition

- atomic claim rate,
- material-claim recall,
- scope precision,
- FACT vs INFERENCE classification accuracy.

### Source and lineage

- primary/system-of-record coverage,
- authority-fit accuracy,
- discovery-to-origin conversion,
- duplicate/derivative-origin detection,
- unknown-independence honesty.

### Evidence edges

- pinpoint locator coverage,
- directness/scope-fit correctness,
- rejected/context-only precision,
- cross-claim source assessment consistency without forced uniformity.

### Temporal truth

- `as_of` coverage,
- stale/superseded/draft/not-yet-effective catch rate,
- version mismatch catch rate,
- false refresh-block rate.

### Contradictions

- falsifier coverage,
- credible opposition recall,
- false-resolution rate,
- absence-test misuse rate.

### Readiness

- `VERIFIED` precision,
- `READY` precision,
- false `REFRESH_REQUIRED` rate,
- unresolved-critical-block precision.

### Efficiency

- sources opened per material claim,
- repeated-source reuse without stale leakage,
- delta refresh scope vs full rerun,
- marginal novelty before stop.

## Golden cases

Maintain fixtures for:

1. official source vs many derivative articles,
2. stale policy replaced by effective version,
3. draft rule vs final rule,
4. not-yet-effective rule,
5. current authoritative source plus older stale accepted support,
6. repository version mismatch,
7. internal system-of-record vs old document,
8. syndicated breaking news with false independence,
9. primary source unavailable,
10. unresolved critical contradiction,
11. inference incorrectly labeled fact,
12. dependency cycle,
13. contradiction flag without falsifier log,
14. failed generic search incorrectly used as absence evidence,
15. v1 -> v2 migration with non-reconstructable search provenance,
16. delta where only one source/version changes.

## Promotion rule

Compare frozen identical inputs. Promote a challenger only after repeatable improvement in authority fit, temporal correctness, contradiction recall, readiness precision, and integration compatibility without invariant regressions.
