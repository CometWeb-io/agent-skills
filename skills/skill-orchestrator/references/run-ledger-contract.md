# Durable workflow run ledger

`scripts/workflow_ledger.py` is a host-local operational sidecar for resumable
orchestrator runs. It is not part of CW-AIP and does not reinterpret Council or
Release Readiness verdicts.

The source of truth is an append-only, hash-chained `events.jsonl` under a
0700 run directory. Events and manifests are 0600. A completed step records its
`run_id`, `event_type`, `event_hash`, `plan_hash`, `step_id`, `envelope_id`, and
`envelope_hash`; the same completion is idempotent,
but a conflicting duplicate blocks the run.

Supported run states are `PENDING`, `RUNNING`, `BLOCKED`, `FAILED`, `CANCELLED`,
`COMPLETED`, and `STALE_PLAN`. Resume must reject a changed plan hash, tampered
event chain, missing envelope, symlinked path, or orphaned running attempt.
Completed steps are never silently rerun.

The replayed run `status` is derived from the event log, not trusted from a
mutable state file.

The ledger stores hashes and references, not raw prompts, credentials,
transcripts, or arbitrary tool output. `COMPLETED` means workflow execution
finished; it is not a Council or Release Readiness authorization.
