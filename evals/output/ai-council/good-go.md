# Council decision — introduce an annual plan for Example Tracker

- As Of: 2026-09-30T10:00:00+02:00 (Europe/Warsaw)
- Current Validity: VALID (first decision on this key)
- Freshness: own pricing CURRENT (checked 2026-09-29); competitor plans CURRENT (checked 2026-09-28); churn data STALE beyond 90 days
- Oldest material admissible evidence: 12 days
- Watch Dependencies: 2 active, 0 triggered

## Verdict

GO — Overall Decision Confidence 72%

- Council Mode: STANDARD
- Required Confidence: 65%
- Recommended option: B — annual plan at a 15% discount, offered to new customers only for the first 60 days
- Evidence Coverage: 84%; Critical Gap: effect on monthly-plan churn is not measured
- Contradiction Coverage: 100%; critical unresolved contradictions: 0
- Binding gates: legal CLEAR, finance CLEAR_WITH_CONTROLS
- Human Approval: not required
- Recommendation: launch option B to new customers and review cash flow after 30 days.

## Confidence map

| Dimension | Confidence | Note |
| --- | ---: | --- |
| Thesis | 75% | Annual billing is the norm in this category |
| Evidence | 70% | Pricing pages verified; churn effect unmeasured |
| Execution | 80% | Billing provider already supports annual intervals |
| Financial | 65% | Weakest and binding: discount reduces year-one revenue per customer |

## Independence and forecasts

Raw consensus 4 of 5 advisers for B; adjusted consensus 3.3 of 5 after discounting two advisers who relied on the same competitor survey. Forecast: 60% that at least 20% of new customers pick annual within 60 days.

## Why

1. [F] Four of the five closest competitors offer an annual plan at 15–20% off (pricing pages checked 2026-09-28).
2. [F] The billing provider supports annual intervals without code changes (provider docs, checked 2026-09-29).
3. [A] Customers who choose annual churn less than monthly customers; not yet measured for this product.
4. [I] Offering it to new customers only limits cannibalisation of existing monthly revenue.

## Double-crux / minority

The falsifiable unknown is whether the discount pulls revenue forward or only reduces it. Minority report (1 adviser): wait for 90 days of churn data before discounting.

## Gates / assumptions / evidence gaps

| Gate | Status | Controls / handoff |
| --- | --- | --- |
| legal | CLEAR | Terms already cover annual renewals |
| finance | CLEAR_WITH_CONTROLS | Cash-flow review at day 30; stop the offer if monthly-plan downgrades exceed 5% |

Top assumption risk: annual customers churn less (unverified; see WD-1).

## What changes the decision

- WD-1: monthly-plan downgrades to annual exceed 5% in the first 30 days → reopen.
- WD-2: a top-three competitor drops its annual discount → re-run the comparison.

## Memory

Saved: yes. Decision Key: `pricing/annual-plan`. Snapshot: `3f9a1c…e2`. Current Validity: VALID. History signal strength: weak (first decision on this key). Watching WD-1 and WD-2.

```json
{
  "id": "ai-council:DecisionEnvelope:pricing-annual-plan",
  "type": "DecisionEnvelope",
  "producer": "ai-council",
  "producer_version": "5.2.0",
  "protocol_version": "2.0",
  "subject": "Introduce an annual plan for Example Tracker",
  "generated_at": "2026-09-30T10:00:00+02:00",
  "as_of": "2026-09-30T10:00:00+02:00",
  "sensitivity": "internal",
  "dependencies": [],
  "payload": {
    "schema": "cometweb.decision/v2",
    "decision_question": "Should Example Tracker introduce an annual plan?",
    "profile": "STANDARD",
    "as_of": "2026-09-30T10:00:00+02:00",
    "verdict": "GO",
    "option": "B",
    "gates": [
      {"gate_id": "legal", "status": "CLEAR"},
      {"gate_id": "finance", "status": "CLEAR_WITH_CONTROLS"}
    ],
    "blockers": [],
    "controls": ["cash-flow review at day 30"],
    "evidence_deps": [],
    "snapshot_hash": "3f9a1ce2",
    "validity": "VALID",
    "human_approval": "not_required"
  },
  "payload_hash": "pending"
}
```
