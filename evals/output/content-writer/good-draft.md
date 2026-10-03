# Why small online shops lose orders at checkout

Most abandoned checkouts are not a mystery. Shoppers leave when the total changes late, when they are forced to create an account, or when the form asks for more than it needs. Each of these is something a shop owner can test in an afternoon.

## Surprise costs at the last step

When shipping or fees appear only on the final screen, the price the shopper agreed to is no longer the price they pay. In the Example Shop Benchmark 2026 survey of 1,200 online shoppers, 41% named unexpected extra costs as the reason they left their last abandoned checkout (Example Shop Benchmark 2026, table 3). Show the full price, shipping included, on the product page.

## Forced accounts

A required sign-up asks for commitment before the shopper has paid. A guest checkout option removes that step. We have not yet found a measured figure for small shops specifically, so this draft does not give one; the effect is described, not quantified.

## Long forms

Every field is a chance to stop. Ask for a phone number only if the courier needs it, and say why next to the field.

## What to test first

Start with the cost display, because it is the change most likely to matter and the easiest to reverse.

---

## Handoff

- Candidate: `post-checkout-loss@c1` (brief `brief-checkout-loss` v1)
- Mode: DRAFT
- Evidence policy: CONTEXTUAL_DRAFT
- Release eligible: false — a DRAFT under CONTEXTUAL_DRAFT is never release eligible, and CL-03 is unresolved.

## Claim ledger

| Claim | Status | Material | As fact | Evidence | Basis |
| --- | --- | --- | --- | --- | --- |
| CL-01 41% of surveyed shoppers named unexpected costs | SUPPORTED | yes | yes | Example Shop Benchmark 2026, table 3 | — |
| CL-02 full price on the product page reduces late surprises | INFERRED | yes | no | — | CL-01 |
| CL-03 guest checkout lifts conversion for small shops | UNRESOLVED | yes | no | — | — |
| CL-04 courier-only phone field example | EXAMPLE | no | no | — | — |

## Invariant checks

| Invariant | State |
| --- | --- |
| PI-01 no named competitor is criticised | PASS |

## Unresolved

- CL-03: no measured guest-checkout effect for shops under 50 orders a day; the draft describes the mechanism without a number. Route to `evidence-researcher`.

## Recommended next skill

`evidence-researcher` for CL-03, then a REVISION candidate.

```json
{
  "schema": "cometweb.content-draft/v1",
  "brief_id": "brief-checkout-loss",
  "candidate_id": "post-checkout-loss@c1",
  "mode": "DRAFT",
  "evidence_policy": "CONTEXTUAL_DRAFT",
  "claims": [
    {"claim_id": "CL-01", "text_or_locator": "Surprise costs, paragraph 1", "material": true, "status": "SUPPORTED", "presented_as_fact": true, "freshness_required": false,
     "evidence": [{"source": "Example Shop Benchmark 2026", "locator": "table 3"}], "basis_claim_ids": []},
    {"claim_id": "CL-02", "text_or_locator": "Surprise costs, last sentence", "material": true, "status": "INFERRED", "presented_as_fact": false, "freshness_required": false, "basis_claim_ids": ["CL-01"]},
    {"claim_id": "CL-03", "text_or_locator": "Forced accounts", "material": true, "status": "UNRESOLVED", "presented_as_fact": false, "freshness_required": false, "basis_claim_ids": []},
    {"claim_id": "CL-04", "text_or_locator": "Long forms", "material": false, "status": "EXAMPLE", "presented_as_fact": false, "freshness_required": false, "basis_claim_ids": []}
  ],
  "protected_invariants": ["PI-01"],
  "invariant_checks": [{"id": "PI-01", "state": "PASS"}],
  "unresolved": ["CL-03"],
  "release_eligible": false,
  "recommended_next_skill": "evidence-researcher"
}
```
