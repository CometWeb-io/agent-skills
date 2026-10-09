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
- ICP: synthetic fixture scope only; C1.
- Positioning: synthetic fixture scope only; C1.
- Product: the public plan surface is recorded as observed.
- Pricing: plans are recorded without a value or superiority judgment.
- Proof: source-backed synthetic fixture only; C1.
- Discovery: public source coverage only.

## Contradictions and gaps

None within the declared synthetic fixture scope; no real competitor findings are claimed.

## Competitive Intelligence handoff

- baseline_id: `competitor-acme-2026-10-05`
- source_profile_status: READY
- Handoff: Competitive Intelligence may use this as a baseline; it is not a delta.

```json
{
  "summary": "Built an evidence-backed initial competitor baseline.",
  "status": "complete",
  "not_verified": [],
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
    "source_profile_status": "READY",
    "profile_sha256": "sha256:72f2456cdf88c87856010940e9f6d3d89cdea108ffd7088e6dddf11b3c70e203"
  }
}
```
