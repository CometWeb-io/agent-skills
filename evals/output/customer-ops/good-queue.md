# Customer Ops Queue — 2026-10-02T09:00+02:00

**As of:** 2026-10-02T09:00+02:00
**Coverage:** PARTIAL
**Sources:** helpdesk (all open tickets), CRM (accounts with an open case), GitHub (linked issues); checked 2026-10-02T08:45+02:00
**Critical gaps:** the billing provider export is unavailable, so billing-state columns are UNKNOWN

## Now

| Rank | Case | Account | Type | Evidence | Priority | Escalation | Retention | SLA/deadline | Owner | Next action |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | CASE-2241 | acct-2001 | outage report | HIGH | P0 | EXECUTIVE | HIGH | breached 08:30 (provider SLA) | support lead | confirm scope with INC-31 commander |
| 2 | CASE-2207 | acct-1190 | billing bug | MEDIUM | P1 | EXPEDITED | MEDIUM | UNKNOWN (not readable) | engineering | run the plan-change replay |
| 3 | CASE-2230 | acct-1543 | how-to question | HIGH | P3 | STANDARD | LOW | due 2026-10-03T17:00+02:00 | unassigned | assign to the support queue owner |

## Incident / specialist gates

- CASE-2241 — linked to INC-31 (export jobs stuck); incident commander owns customer comms — support lead mirrors the incident update.

## Overdue commitments

- CM-7 on CASE-2188: status update promised for 2026-10-01T12:00+02:00, not sent — owner support, send today with a new checkpoint.

## Stalled / ownerless handoffs

- CASE-2230: routed support → product → support in 48 h; no owner — needs an assignee.

## Emerging clusters

- Export jobs stuck after the 2026-09-30 release — 4 accounts / 6 cases — 2026-09-30 to 2026-10-02 — evidence MEDIUM.

## Data quality / contradictions

- CASE-2207: the CRM shows the plan as Growth, the helpdesk form says Starter; the CRM record is newer and is used.

## Needs approval

- Send the CM-7 status update to acct-1610 (draft attached to CASE-2188).
