# Partner review — Northwind Example 3PL (week 8)

Mode: REVIEW.

## Learning Contract

- Engagement motion: DESIGN_PARTNER (active since 2026-08-07).
- Learning strategy: narrow validation in mid-size 3PL warehouses.
- H1 (must-cover): dock scheduling conflicts cost measurable overtime every week.
- H2 (must-cover): shift leads run the tool day to day without IT.
- Capacity constraint: one engineer, at most 3 active partners.

## Evidence readiness

- Material evidence: 8 weeks of product usage logs and 6 weekly feedback calls (live-confirmed).
- Critical unknowns: whether the overtime reduction holds at peak season (starts in November).
- Stale claims: none; usage data read 2026-10-02.
- Contradiction search: compared shift-lead interviews with usage logs; both show daily use at 2 of 3 sites.
- Binding evidence gap: none for this review.

## Activation / review output

- Partner charter summary: weekly 30-minute feedback call, shift-lead access at 3 sites, no bespoke integrations.
- Pilot success/failure criteria: H1 succeeds if weekly overtime on dock shifts falls for 4 consecutive weeks; fails if usage drops below 3 days a week at 2 sites.
- Current usage/implementation state: live at 2 of 3 sites; third site waits for a door-sensor install on their side.
- Request-triage summary: 5 requests — 3 CORE (carrier booking link, shift handover note, mobile view), 1 SEGMENT (multi-site view), 1 BESPOKE (custom ERP export, declined under the charter).
- Learning yield: H1 supported at 2 sites (live-confirmed in usage logs, 2026-09-04 to 2026-10-01); H2 supported, shift leads create 90% of bookings.
- Bespoke/support burden: low; 2 support tickets in 8 weeks.
- Next review date: 2026-10-30.
- Lifecycle state: CONTINUE — health is strong and the partner still answers new questions; willingness to buy is not yet tested, so this is not a conversion candidate.

## Reproducibility

- As of: 2026-10-02T16:00:00+02:00.
- Sources: product usage logs, feedback-call notes, the partner charter.
- Not verified: the partner's own overtime figures, which they report but we cannot see.

```json
{
  "partner": "Northwind Example 3PL",
  "ratings": {
    "workflow_usage": 4,
    "learning_yield": 4,
    "user_champion_engagement": 4,
    "implementation_progress": 4,
    "feedback_quality": 5,
    "transferability": 4,
    "value_signal": 3
  },
  "bespoke_pressure": 1,
  "support_burden": 1,
  "blocker_persistence": 0,
  "willingness_to_buy": 2,
  "product_ready_for_conversion": false,
  "timing_capacity_blocker": false
}
```
