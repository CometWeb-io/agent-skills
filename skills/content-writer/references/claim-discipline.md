# Claim discipline

Classify **material claims**, not every sentence.

- `SUPPORTED` — inspected evidence directly supports the scoped wording.
- `INFERRED` — the conclusion follows from cited basis claims but is not directly stated; never present it as direct fact.
- `OPINION` — recommendation or interpretation, visibly framed as such.
- `EXAMPLE` — illustrative case, never evidence of prevalence by itself.
- `UNRESOLVED` — potentially supportable but evidence is missing, stale, contradictory, or too weak.
- `UNSUPPORTED` — available evidence does not support the wording.

A material `SUPPORTED` claim stores `evidence[]` with `source` and pinpoint `locator`. If the claim is freshness-sensitive, also require timezone-aware `observed_at` and `freshness_status: CURRENT|NEAR_EXPIRY`.

A material `INFERRED` claim stores non-empty `basis_claim_ids[]`. Scope quantitative claims to population, period, geography, denominator, and method when these change meaning. Never invent citations, quotations, customer outcomes, or measurements to complete a narrative.
