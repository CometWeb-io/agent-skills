# Customer Ops Brief — week 40 — as of 2026-10-02T17:00+02:00

**Coverage:** PARTIAL (billing provider export unavailable)

## Now

- INC-31 (SEV2, MONITORING): acct-2001 recovery still pending.
- CASE-2241 (P0): executive escalation tied to INC-31.
- CM-7 overdue since 2026-10-01; sent today with a new checkpoint.

## Next

- Problem cluster "exports cannot be scheduled" (9 accounts / 14 cases) waiting on a product decision.
- example-org/billing#418 for CASE-2207, fix date not set.

## Watch

- Two new reports of slow PDF exports; below the cluster threshold.

## Closed loop

- CASE-2150 import fix verified: the customer re-ran the import [Helpdesk | ticket 2150 | 2026-10-02T09:30Z].
- One reopen: CASE-2133 reopened after the 4.12.0 release.

## Quality

- Median requester wait 3.1 h (week 39: 2.4 h); 1 reopen; 1 promise breach (CM-7).

## Metrics

- First-response time: median 3.1 h, window 2026-09-26 to 2026-10-02, denominator 58 new tickets.
- Verified-fix rate: 4 of 6, window week 40, denominator cases marked fixed by engineering.

## Data quality

- 1 unowned case (CASE-2230); plan-name conflict on acct-1190; billing export missing.

## Needs approval

- Send the CM-1 status update to acct-1190 (draft ready).
- Create the GitHub issue drafted for CASE-2207 in example-org/billing.
