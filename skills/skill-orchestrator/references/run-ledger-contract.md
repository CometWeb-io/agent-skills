# Durable workflow run ledger

`scripts/workflow_ledger.py` is a host-local operational sidecar for resumable
orchestrator runs. It is not part of CW-AIP and never interprets, upgrades, or
overrides Council or Release Readiness verdicts.

The source of truth is an append-only, hash-chained `events.jsonl` under a
0700 run directory. Existing roots are checked, never chmodded. New roots
are created with mode 0700. The manifest and event log are 0600; existing ledger
artifacts with group or world permissions are rejected. Symlinked roots, run
directories, manifests, and logs are rejected, and run and step identifiers
cannot contain path separators or traversal components.

## CLI and resume contract

Create a run, then pass the same plan back when resuming so a plan change is
detected:

```bash
python3 scripts/workflow_ledger.py create --root "$LEDGER_ROOT" \
  --run-id run-1 --plan-json plan.json
python3 scripts/workflow_ledger.py claim-next "$LEDGER_ROOT/run-1" \
  --plan-json plan.json
python3 scripts/workflow_ledger.py complete-step "$LEDGER_ROOT/run-1" \
  --step-id step-1 --attempt-id ATTEMPT \
  --envelope-id ENVELOPE --envelope-hash HASH --envelope-json envelope.json
```

`resume` is an alias of `claim-next`. `fail-step`, `block-step`, and `cancel`
append explicit terminal events for the current attempt or run. `status`
replays the event log. A changed plan appends `plan_stale_detected` and returns
`STALE_PLAN`; the run cannot resume against either the old or changed plan
until a new run is created.

Steps use their declared `step_id` (or `id`); otherwise the manifest assigns
`step-1`, `step-2`, and so on. `claim-next` selects the first non-completed
step. A failed step may be retried after its attempt is explicitly closed;
a blocked step and an orphaned running attempt stop resume. A completed step is
never claimed again.

## Event semantics

Every claimed attempt has an `attempt_id`, which is required when completing,
failing, or blocking it. A missing or non-active attempt is an orphan
transition and fails closed. Repeating
the same completion, failure, block, or cancellation is idempotent only when
its recorded payload is identical; a different envelope, reason, or
cancellation payload is a conflicting duplicate and fails closed.

Ledger records expose `run_id`, `event_type`, `event_hash`, `plan_hash`,
`current_plan_hash`, `step_id`, `attempt_id`, `attempt_number`, `worker_id`,
`envelope_id`, `envelope_hash`, and `reason` where applicable. `id` is accepted
as an input-plan alias for `step_id`; it is normalized into the manifest.

Supported run states are `PENDING`, `RUNNING`, `BLOCKED`, `FAILED`, `CANCELLED`,
`COMPLETED`, and `STALE_PLAN`. The replayed run `status` is derived from the
event log, not trusted from a mutable state file. A missing final newline or
partial JSON record is a truncated log and is rejected.

The ledger stores hashes and references, not raw prompts, credentials,
transcripts, or arbitrary tool output. `COMPLETED` means workflow execution
finished; it is not a Council or Release Readiness authorization.

Every new completion records `completion_class`: `RECEIPT_ONLY` for untyped
operational receipts, `SCHEMA_VALIDATED` for a validated final CW-AIP wrapper,
or `DOMAIN_ACCEPTED` for a pinned producer/profile kernel gate. These labels
describe deterministic checks, never model effectiveness or permission to act.
Any step with `envelope_out` requires full `--envelope-json`, correct producer,
type and recomputed envelope/payload hashes; its `dependencies` must equal the
completed prefix's envelope IDs. An ID/hash alone cannot complete a typed step.
Legacy receipts still replay as `RECEIPT_ONLY` and cannot unlock a typed
downstream step. Start a new run with validated envelopes rather than upgrading
an old receipt's status. Untyped receipt-only logging remains supported.

## PRD prerequisite

For steps declared with the optional PRD gate, read `references/prd-handoff.md`.
Completion revalidates the full envelope against the pinned schema/kernel and
requires READY before writing the completion. Rejected input leaves the attempt
active and cannot unlock the next step. New run-created events bind manifest steps;
legacy non-PRD ledgers remain readable.

## Concurrent callers and crash boundary

Every mutation holds a run-local OS lock across replay, eligibility checks and
append: POSIX flock or Windows byte-range locking. Contending callers serialize;
only one active attempt is allowed. Windows mode bits do not validate ACLs:
use a private user-owned directory with appropriate ACLs on that host.
Locks release when the process exits. An interrupted record still fails closed
as a truncated log; an orphaned attempt requires explicit resolution.

The hash chain detects accidental changes, not an attacker who can rewrite the
entire local directory. This is a sequential local executor, not a distributed
runtime. External effects require API idempotency and read-back; the ledger
cannot make an external write and local append atomic or promise exactly once.
