# Freshness and Temporal Truth

## Required distinctions

Keep separate:

- `published_at` — artifact publication time,
- `effective_from` — when the rule/state applies,
- `effective_to` — when it stops applying,
- `last_verified_at` — when the current artifact was actually inspected,
- `expires_at` — explicit verification expiry if known,
- `source_version` — version/commit/release,
- `superseded_by_source_id` — newer controlling artifact.

Publication date is not effective date.

## Temporal statuses

Use only:

`CURRENT | NEAR_EXPIRY | STALE | SUPERSEDED | DRAFT | NOT_YET_EFFECTIVE | UNKNOWN`

## Live-verification classes

For material claims, re-open the current authority during the research run for:

- law/regulation and regulatory guidance,
- security advisories/exploitation status,
- vendor policy/terms,
- competitor pricing/availability,
- fast-changing service status,
- internal metric/process state when a current system of record exists.

`verified_for_research=true` means the source was inspected for the current research run. It is **not** permission for a downstream decision skill to treat it as decision-specific verified evidence.

## Conservative reuse defaults

| Claim type | Default cache window |
| --- | ---: |
| law/regulation | 0 days |
| regulatory guidance | 0 days |
| security advisory | 0 days |
| service status | 0 days |
| vendor policy | 7 days |
| competitor pricing | 3 days |
| internal metric/process | 1 day |
| official technical docs/repository behavior | 30 days |
| company announcement/current fact | 30 / 7 days |
| market metric | 30 days |
| qualitative experience | 90 days |
| academic/dataset fact | 365 days |
| historical fact/doctrine | 3650 days |

These are research-cache defaults, not claims about how often reality changes. Domain policy may be stricter.

## Freshness gate

A material time-sensitive FACT needs at least one accepted support edge from a temporally admissible source with adequate authority/directness. Do not fail a claim merely because an older accepted source remains in the ledger when a newer admissible authoritative source establishes the claim; surface the stale source separately.

If no admissible support remains, research status becomes `REFRESH_REQUIRED`.

## Kernel 2.0.1: executable admission rules

A live-verification flag does not override the cache window. Boolean flags must be JSON booleans, not strings such as `"false"` or integer substitutes. Supplied TTLs must be finite numbers in 0–36500 days. A registered default is a ceiling; an explicit source policy can shorten it, not extend it. Unregistered claim types need an explicit policy.

Times must be timezone-aware timestamps. Publication and verification cannot occur after the assessment. Verification cannot precede the recorded publication of the inspected artifact. Reversed effective intervals are invalid. `effective_to`, `expires_at`, and positive cache expiry are exclusive upper boundaries. A `static` label cannot disable the live/current-fact gate.

### Zero-cache evidence

Zero days means no reuse between research runs, not an impossible requirement to verify at the exact assessment microsecond. Record both:

- `research_contract.started_at`: actual start of this research run;
- source `verified_research_id`: exact `research_id` of the run that inspected the source.

The source must also have `verified_for_research: true` and a `last_verified_at` within the inclusive interval from `started_at` to `as_of`. Missing run binding produces `UNKNOWN`. Never synthesize a run ID or timestamp to clear this gate.

For direct CLI evaluation:

```bash
python scripts/evidence_kernel.py temporal \
  --source-json source.json --claim-type service_status \
  --as-of '2026-09-13T10:00:00Z' \
  --research-id res_example \
  --research-started-at '2026-09-13T09:00:00Z'
```

`audit`, `coverage`, and `refresh-plan` take that context from the ledger. If a source supplies a run identifier, a mismatch is inadmissible even for a positive cache window. For legacy positive-window sources without a run identifier, the boolean is still only a supplied assertion; the kernel enforces age but does not authenticate a live inspection.

### Quality, dependencies and independence

Authority, directness, scope fit, measurement quality, pinpoint locator and freshness must hold on the same supporting edge. A stale authoritative source plus a fresh weak summary cannot jointly masquerade as one admissible source.

Inference dependencies are evaluated from their evidence, including supporting claims; a nominal `VERIFIED` label alone is insufficient. Unresolved contradictions or material gaps on a prerequisite block dependent inferences. `refresh-plan.dependent_claim_ids` identifies downstream inferences affected by refresh work; it is not an execution record.

Declared source lineage, identical canonical references, identical content hashes and explicitly shared independence groups are collapsed into connected components for counting. This is conservative duplicate accounting, not proof that remaining components are genuinely independent. Unknown independence stays unknown.

### Completion and migration

An empty pack, a pack with no material claims, or one with open material gaps cannot be `READY`. Completed falsifier records need an actual query summary and a timestamp no later than `as_of`. Migration from v1 preserves legacy flags only as history, resets research verification, and creates incomplete search reminders rather than fabricating executed searches.

The kernel checks consistency of supplied records. It does not authenticate sources, verify the meaning of a quotation, inspect a website, prove entailment, or authorize a downstream decision.
