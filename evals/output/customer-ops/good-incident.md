# Incident INC-31 — export jobs stuck in "queued"

**As of:** 2026-10-02T10:15+02:00
**State:** MONITORING
**Customer-impact severity:** SEV2
**Specialist gates:** none
**Commander:** platform on-call
**Started / detected:** started 2026-09-30T22:10+02:00, detected 2026-10-01T07:40+02:00
**Known affected scope:** CSV and PDF exports for workspaces on the EU cluster

## Customer impact

Exports requested since the 2026-09-30 release stayed queued; no data was lost, but customers could not download reports for up to 33 hours.

## Confirmed facts

- [Status page | incident 31 | 2026-10-01T08:05Z] incident opened, EU exports affected.
- [Job queue metrics | export-worker-eu | 2026-10-02T07:50Z] queue depth back to baseline after the worker rollback.

## Unknowns

- Whether exports requested during the window were silently dropped or only delayed for two accounts whose jobs show no completion record.

## Hypotheses

| Hypothesis | For | Against | Next test |
|---|---|---|---|
| H1: the release changed the worker's queue name | rollback fixed new jobs | old jobs still queued | diff the worker config between releases |
| H2: a stuck lock on the export table | lock warnings in logs | lock released at 03:00 | replay one queued job on staging |

## Current mitigation / workaround

- Worker rolled back to the previous release; customers can re-request an export.

## Customer exposure

| Account/ref | Exposure | Comms | Recovery verification | Follow-up |
|---|---|---|---|---|
| acct-2001 | 3 exports delayed | status page + email | pending (re-request not yet confirmed) | support lead |
| acct-1543 | 1 export delayed | status page | confirmed export received 2026-10-02 | none |

## Timeline

| Time | Event | Source |
|---|---|---|
| 2026-09-30T22:10+02:00 | release deployed | deploy log, release 4.12.0 |
| 2026-10-01T07:40+02:00 | first customer report | helpdesk CASE-2241 |
| 2026-10-02T07:30+02:00 | worker rolled back | deploy log, rollback 4.11.3 |

## Canonical customer communication

- Latest confirmed message: "Exports are processing again; please re-request any export from before 07:30 CEST."
- Next checkpoint 2026-10-02T16:00+02:00; no confirmed ETA for the root-cause fix.

## Engineering / prevention

- example-org/platform#902 (open): queue-name drift; add a release check.

## Verification

- Criteria: every affected account confirms a successful export, and new exports complete within 5 minutes for 24 hours. acct-2001 is still pending, so the state stays MONITORING.
