# Repair ledger — pricing-guide-v3

## Ledger status

VALID

- Candidate: `pricing-guide-v3`, mode STANDARD, portfolio mode (6 effort units).
- `scripts/kernel.py` on the ledger below: VALID, closed 1, open 2.

## Blocking open work

- RP-01 — CR-001 — Status: REOPENED (re-opens RP-01). Class: PATCH. Patch risk: LOW.
  The table edit removed the retired Starter tier but also dropped the annual price column, so the earlier closure is withdrawn.
  Verification required: the plan table shows every live tier with both the monthly and the annual price.

## Proven closures

- RP-02 — CR-002, CR-003 — Status: CLOSED. Class: REWRITE.
  Root cause: the FAQ answered a billing question with a claim the source did not support.
  Done when: each FAQ answer cites the billing policy section it restates.
  Verification: fresh PASS on `pricing-guide-v3`, claim-to-source check, 6 of 6 FAQ answers cite a policy section (review note 2026-10-02).

## Deferred and won't fix

- RP-03 — CR-004 — Status: DEFERRED. Reason: the usage figures need the Q4 usage export, due 2026-10-15. Depends on: RP-02.

## Regressions

- RP-01 dropped the annual price column. RP-01 is REOPENED and is not counted as closed.

## Remaining open

- RP-01 (CR-001) and RP-03 (CR-004).

## Ledger

```json
{
  "schema": "cometweb.repair-ledger/v1",
  "mode": "STANDARD",
  "portfolio_mode": true,
  "candidate_id": "pricing-guide-v3",
  "items": [
    {"repair_id": "RP-01", "finding_ids": ["CR-001"], "repair_class": "PATCH", "root_cause": "plan table still lists the retired Starter tier", "done_when": "no page mentions a tier missing from the pricing page", "depends_on": [], "regression_detected": true, "status": "REOPENED", "reopen_of": "RP-01", "effort_band": "XS", "blast_radius": "SECTION", "reversibility": "EASY"},
    {"repair_id": "RP-02", "finding_ids": ["CR-002", "CR-003"], "repair_class": "REWRITE", "root_cause": "the FAQ answers a billing question with a claim the source does not support", "done_when": "each FAQ answer cites the billing policy section it restates", "depends_on": [], "verification_evidence": [{"fresh": true, "result": "PASS", "method": "claim-to-source check", "evidence": ["review note 2026-10-02: 6/6 FAQ answers cite policy sections"], "candidate_id": "pricing-guide-v3", "observed_at": "2026-10-02T11:05:00+02:00"}], "status": "CLOSED", "effort_band": "S", "blast_radius": "SECTION", "reversibility": "EASY"},
    {"repair_id": "RP-03", "finding_ids": ["CR-004"], "repair_class": "REANALYSIS", "depends_on": ["RP-02"], "status": "DEFERRED", "defer_reason": "needs the Q4 usage export, due 2026-10-15", "effort_band": "M", "blast_radius": "CROSS_ARTIFACT", "reversibility": "MODERATE"}
  ],
  "regressions": ["RP-01: the new tier table drops the annual price column"],
  "remaining_open": ["RP-01", "RP-03"]
}
```
