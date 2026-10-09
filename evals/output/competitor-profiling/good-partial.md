# Competitor profile — Acme

## Profile status

- Status: PARTIAL
- Profile ID: `competitor-acme-2026-10-05`

## Scope and as_of

- as_of: 2026-10-05
- Scope: public product baseline only.

## Source manifest

| ID | Kind | Locator | observed_at |
| --- | --- | --- | --- |
| S1 | official | https://example.invalid/product | 2026-10-05 |

## Claim ledger

| ID | State | Claim | Source IDs |
| --- | --- | --- | --- |
| C1 | OBSERVED | The public product page describes the listed capability. | S1 |

## Competitor profile

- Company: Acme is the named subject.
- ICP: UNKNOWN.
- Positioning: UNKNOWN.
- Product: one public product page was observed.
- Pricing: UNKNOWN.
- Proof: UNKNOWN.
- Discovery: public source coverage only.

## Contradictions and gaps

- Pricing and proof require additional primary sources.

## Competitive Intelligence handoff

- baseline_id: `competitor-acme-2026-10-05`
- source_profile_status: PARTIAL
- Handoff: refresh the baseline before making a recurring delta claim.

```json
{
  "summary": "Built an evidence-backed initial competitor baseline.",
  "status": "partial",
  "not_verified": [
    "live pricing verification"
  ],
  "profile": {
    "subject": "Acme competitor",
    "as_of": "2026-10-05",
    "scope": "public first baseline",
    "sources": [
      {
        "id": "S1",
        "kind": "official",
        "locator": "https://example.invalid/pricing",
        "observed_at": "2026-10-05"
      }
    ],
    "claims": [
      {
        "id": "C1",
        "text": "The source describes the product and pricing page.",
        "state": "OBSERVED",
        "source_ids": [
          "S1"
        ]
      }
    ],
    "sections": {
      "company": {
        "summary": "covered",
        "claim_ids": [
          "C1"
        ]
      },
      "icp": {
        "summary": "covered",
        "claim_ids": [
          "C1"
        ]
      },
      "positioning": {
        "summary": "covered",
        "claim_ids": [
          "C1"
        ]
      },
      "product": {
        "summary": "covered",
        "claim_ids": [
          "C1"
        ]
      },
      "pricing": {
        "summary": "covered",
        "claim_ids": [
          "C1"
        ]
      },
      "proof": {
        "summary": "covered",
        "claim_ids": [
          "C1"
        ]
      },
      "discovery": {
        "summary": "covered",
        "claim_ids": [
          "C1"
        ]
      }
    },
    "contradictions": [],
    "gaps": []
  },
  "competitive_intelligence_handoff": {
    "baseline_id": "competitor:acme:2026-10-05",
    "source_profile_status": "PARTIAL"
  }
}
```
