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
| S2 | official | https://example.invalid/company | 2026-10-05 |
| S3 | official | https://example.invalid/icp | 2026-10-05 |
| S4 | official | https://example.invalid/positioning | 2026-10-05 |
| S5 | official | https://example.invalid/product | 2026-10-05 |
| S6 | official | https://example.invalid/proof | 2026-10-05 |
| S7 | official | https://example.invalid/discovery | 2026-10-05 |

## Claim ledger

| ID | State | Claim | Source IDs |
| --- | --- | --- | --- |
| C1 | OBSERVED | The public pricing page lists the current plans. | S1 |
| C2 | OBSERVED | Acme is the vendor named on the company page. | S2 |
| C3 | OBSERVED | The product page addresses small retail teams. | S3 |
| C4 | OBSERVED | The vendor describes a lightweight inventory tool. | S4 |
| C5 | OBSERVED | The documentation describes stock tracking. | S5 |
| C6 | OBSERVED | The vendor publishes one case study, not independent efficacy evidence. | S6 |
| C7 | OBSERVED | The site lists a public newsletter. | S7 |

## Competitor profile

- Pricing: The public pricing page lists the current plans. C1.
- Company: Acme is the vendor named on the company page. C2.
- Icp: The product page addresses small retail teams. C3.
- Positioning: The vendor describes a lightweight inventory tool. C4.
- Product: The documentation describes stock tracking. C5.
- Proof: The vendor publishes one case study, not independent efficacy evidence. C6.
- Discovery: The site lists a public newsletter. C7.

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
      },
      {
        "id": "S2",
        "kind": "official",
        "locator": "https://example.invalid/company",
        "observed_at": "2026-10-05"
      },
      {
        "id": "S3",
        "kind": "official",
        "locator": "https://example.invalid/icp",
        "observed_at": "2026-10-05"
      },
      {
        "id": "S4",
        "kind": "official",
        "locator": "https://example.invalid/positioning",
        "observed_at": "2026-10-05"
      },
      {
        "id": "S5",
        "kind": "official",
        "locator": "https://example.invalid/product",
        "observed_at": "2026-10-05"
      },
      {
        "id": "S6",
        "kind": "official",
        "locator": "https://example.invalid/proof",
        "observed_at": "2026-10-05"
      },
      {
        "id": "S7",
        "kind": "official",
        "locator": "https://example.invalid/discovery",
        "observed_at": "2026-10-05"
      }
    ],
    "claims": [
      {
        "id": "C1",
        "text": "The public pricing page lists the current plans.",
        "state": "OBSERVED",
        "source_ids": [
          "S1"
        ]
      },
      {
        "id": "C2",
        "text": "Acme is the vendor named on the company page.",
        "state": "OBSERVED",
        "source_ids": [
          "S2"
        ]
      },
      {
        "id": "C3",
        "text": "The product page addresses small retail teams.",
        "state": "OBSERVED",
        "source_ids": [
          "S3"
        ]
      },
      {
        "id": "C4",
        "text": "The vendor describes a lightweight inventory tool.",
        "state": "OBSERVED",
        "source_ids": [
          "S4"
        ]
      },
      {
        "id": "C5",
        "text": "The documentation describes stock tracking.",
        "state": "OBSERVED",
        "source_ids": [
          "S5"
        ]
      },
      {
        "id": "C6",
        "text": "The vendor publishes one case study, not independent efficacy evidence.",
        "state": "OBSERVED",
        "source_ids": [
          "S6"
        ]
      },
      {
        "id": "C7",
        "text": "The site lists a public newsletter.",
        "state": "OBSERVED",
        "source_ids": [
          "S7"
        ]
      }
    ],
    "sections": {
      "pricing": {
        "summary": "The public pricing page lists the current plans.",
        "claim_ids": [
          "C1"
        ],
        "section_support": [
          {
            "claim_id": "C1",
            "source_id": "S1",
            "rationale": "The synthetic pricing source explicitly states this section claim."
          }
        ]
      },
      "company": {
        "summary": "Acme is the vendor named on the company page.",
        "claim_ids": [
          "C2"
        ],
        "section_support": [
          {
            "claim_id": "C2",
            "source_id": "S2",
            "rationale": "The synthetic company source explicitly states this section claim."
          }
        ]
      },
      "icp": {
        "summary": "The product page addresses small retail teams.",
        "claim_ids": [
          "C3"
        ],
        "section_support": [
          {
            "claim_id": "C3",
            "source_id": "S3",
            "rationale": "The synthetic icp source explicitly states this section claim."
          }
        ]
      },
      "positioning": {
        "summary": "The vendor describes a lightweight inventory tool.",
        "claim_ids": [
          "C4"
        ],
        "section_support": [
          {
            "claim_id": "C4",
            "source_id": "S4",
            "rationale": "The synthetic positioning source explicitly states this section claim."
          }
        ]
      },
      "product": {
        "summary": "The documentation describes stock tracking.",
        "claim_ids": [
          "C5"
        ],
        "section_support": [
          {
            "claim_id": "C5",
            "source_id": "S5",
            "rationale": "The synthetic product source explicitly states this section claim."
          }
        ]
      },
      "proof": {
        "summary": "The vendor publishes one case study, not independent efficacy evidence.",
        "claim_ids": [
          "C6"
        ],
        "section_support": [
          {
            "claim_id": "C6",
            "source_id": "S6",
            "rationale": "The synthetic proof source explicitly states this section claim."
          }
        ]
      },
      "discovery": {
        "summary": "The site lists a public newsletter.",
        "claim_ids": [
          "C7"
        ],
        "section_support": [
          {
            "claim_id": "C7",
            "source_id": "S7",
            "rationale": "The synthetic discovery source explicitly states this section claim."
          }
        ]
      }
    },
    "contradictions": [],
    "gaps": []
  },
  "competitive_intelligence_handoff": {
    "baseline_id": "competitor:acme:2026-10-05",
    "source_profile_status": "READY",
    "profile_sha256": "sha256:a209fd5309410e3531a59087ebf4def0f1291396b373b586628e5a93d68604ab"
  }
}
```
