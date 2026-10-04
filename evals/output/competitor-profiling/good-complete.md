# Competitor profile — Acme

## Profile status

- Status: COMPLETE
- Profile ID: `competitor-acme-2026-10-05`

## Scope and as_of

- as_of: 2026-10-05
- Scope: public company, product, pricing and proof baseline; no private data.

## Source manifest

| ID | Kind | Locator | observed_at |
| --- | --- | --- | --- |
| S1 | official | https://example.invalid/pricing | 2026-10-05 |

## Claim ledger

| ID | State | Claim | Source IDs |
| --- | --- | --- | --- |
| C1 | OBSERVED | The public pricing page lists the current plans. | S1 |

## Competitor profile

- Company: Acme is the named subject; company facts remain limited to S1.
- ICP: unknown; no unsupported segment claim.
- Positioning: unknown; requires a broader source set.
- Product: the public plan surface is recorded as observed.
- Pricing: plans are recorded without a value or superiority judgment.
- Proof: no independent proof source was found.
- Discovery: public source coverage only.

## Contradictions and gaps

None. Remaining unknowns are listed as gaps, not silently filled.

## Competitive Intelligence handoff

- baseline_id: `competitor-acme-2026-10-05`
- source_profile_status: READY
- Handoff: Competitive Intelligence may use this as a baseline; it is not a delta.
