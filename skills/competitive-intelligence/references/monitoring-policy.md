# Monitoring Policy

## Contents

1. Watch design
2. Competitor tiers
3. Signal cadences
4. Source health
5. Removal confirmation
6. Alert policy
7. Re-baselining
8. Cost and coverage budgets

## 1. Watch design

A watch is a matrix of `competitor × signal area × source`, not a single generic search query.

For every watched signal define:

- source identifier/location,
- signal category,
- criticality,
- expected volatility,
- cadence,
- last successful collection,
- last verified state,
- fallback source if one exists,
- alert threshold.

Do not increase cadence without a reason. More checks can create more noise without improving decision quality.

## 2. Competitor tiers

### Tier 1 — direct/strategic

Track core buying criteria, pricing/packaging, product releases, positioning, and major company moves most closely.

### Tier 2 — adjacent/substitute

Track category overlap, pricing/positioning, major product launches, and meaningful distribution moves.

### Tier 3 — emerging/watch

Track broad strategic moves and threshold-crossing signals. Avoid expensive deep collection on every cycle.

Tier changes are themselves decisions. Promote/demote based on market overlap, deal presence, customer substitution, strategic adjacency, or repeated material moves — not on publicity alone.

## 3. Signal cadences

Use configurable cadence by volatility and decision relevance. Sensible starting ranges:

| Signal | Typical starting cadence |
|---|---|
| Pricing/packaging | daily to weekly for Tier 1; weekly to monthly otherwise |
| Changelog/releases/docs | daily to weekly |
| Homepage/positioning | weekly |
| Integrations/marketplaces | weekly to monthly |
| Reviews/buyer sentiment | weekly to monthly |
| SEO/content/traffic estimates | monthly unless a campaign is being investigated |
| Company/hiring/funding | weekly to monthly |
| Security/compliance/status | event-driven or weekly/monthly depending on use case |

These are operational defaults, not evidence TTLs and not guarantees that the skill can self-schedule.

## 4. Source health

Track source health separately from competitor state.

Allowed source-health states:

- `OK` — collection succeeded and the expected content/schema is usable.
- `CHANGED` — source structure changed; extraction may need re-baselining.
- `UNAVAILABLE` — temporary failure, timeout, or source outage.
- `BLOCKED` — access/tool restriction prevents collection.
- `STALE` — source exists but has not been successfully re-verified within policy.
- `UNKNOWN` — status cannot be established.

A source failure never means the competitor field was removed.

When a critical source is `UNAVAILABLE`, `BLOCKED`, `CHANGED`, or `STALE`, preserve the last accepted state and downgrade current coverage rather than writing `null`/empty values as if they were observed removals.

## 5. Removal confirmation

Removals are especially error-prone because extraction failures look like absence.

Treat a material removal as `CONFIRMED` only when one of these applies:

- the first-party source explicitly states a sunset/removal/deprecation; or
- the field is absent in a successful comparable collection and a second relevant source/refresh supports the absence; or
- replacement documentation clearly supersedes the old state.

Do not confirm removal from a single failed scrape, 404 caused by URL migration, missing selector, or inaccessible region.

## 6. Alert policy

Use two channels conceptually:

- **Immediate/conditional alerts** for newly accepted `CRITICAL` events and configured `HIGH` categories.
- **Periodic digests** for `HIGH`/`MEDIUM` events, confirmations, retractions, and pattern changes.

Suppress alerts when:

- only verification timestamp changed,
- event key already alerted and no material status changed,
- change is below threshold,
- source health is degraded and the change may be an extraction artifact.

A retraction/correction of a previously alerted material event should itself be eligible for an alert.

## 7. Re-baselining

Re-baseline a source or field when:

- URL/site structure changed materially,
- extraction schema no longer maps reliably,
- category or plan taxonomy changed,
- a product rebrand invalidates field identity,
- a merger/acquisition changes the tracked entity boundary,
- repeated false positives indicate bad normalization.

Re-baselining must preserve prior snapshot history. Do not rewrite old state to make the new schema look cleaner.

## 8. Cost and coverage budgets

Prioritize collection by expected decision value:

1. Tier 1 + high-volatility + high-impact signals.
2. Material open hypotheses/falsifiers.
3. Tier 2 broad coverage.
4. Tier 3 threshold watches.

If the research budget is constrained, reduce low-value source breadth before weakening verification on high-impact claims.

Report coverage explicitly: `checked / expected / stale / failed / not configured` by competitor and signal area when the user needs operational health.
