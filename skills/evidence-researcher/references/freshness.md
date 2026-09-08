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
