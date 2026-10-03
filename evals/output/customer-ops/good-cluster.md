# Problem Cluster: exports cannot be scheduled outside working hours

**State:** CONFIRMED
**Window:** 2026-07-01 to 2026-09-30
**Accounts:** 9
**Cases:** 14
**Segments:** agencies (6 accounts), in-house teams (3 accounts)
**Evidence grade:** MEDIUM

## Underlying job/problem

Teams want reports ready when the working day starts without someone triggering them by hand.

## Evidence

- [Helpdesk | ticket 1984 | 2026-07-14T09:12Z] "we export every Monday at 6 am by hand".
- [Helpdesk | ticket 2102 | 2026-09-03T07:40Z] asks for a nightly export to a shared drive.

## Requested solutions

- Scheduled exports (7 cases), an export API (4 cases), email delivery (3 cases).

## What the evidence supports

- A recurring manual export at a fixed time; not yet which delivery channel matters most.

## Support load

- 14 cases and about 3 hours of agent time in the window.

## Counterexamples / contradictions

- Two agency accounts already script exports through the API and asked for nothing.

## Workaround / engineering dependency

- The export API works for teams with a developer; no scheduler exists in the product.

## Product evidence handoff

- feedback-integrator: decide whether scheduled exports enter discovery this quarter, with the 9 accounts as interview candidates.

## Missing evidence

- Usage data on how many accounts export weekly at a fixed time.
