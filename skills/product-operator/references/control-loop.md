# Living product control loop

Product Operator should reduce repeated analysis cost without becoming a second source of truth.

## First run

1. Establish current goal/horizon/source coverage.
2. Build the material state ledger.
3. Reconcile evidence and drift.
4. Classify readiness.
5. Rank + dependency-sequence actions.
6. Emit report and immutable snapshot.

## Repeated run

1. Load previous snapshot as a retrieval index only.
2. Identify material claims/actions requiring revalidation.
3. Retrieve current authoritative evidence.
4. Build the current report from current evidence.
5. Run `delta` against the prior snapshot.
6. Explain stage, blocker, issue, and priority changes.
7. Create a new immutable snapshot; never overwrite the old one.

## Snapshot contract

`scripts/operator_kernel.py snapshot` emits:
- `snapshot_version`;
- `as_of`;
- `target`;
- `snapshot_hash` over the whole report;
- `state_fingerprint` over stable state-driving fields;
- embedded report.

Snapshots are immutable analysis artifacts, not authoritative planning/product data.

## Delta semantics

Track at minimum:
- state stage transitions;
- new/removed state items;
- new/resolved reconciliation issues;
- priority tier changes;
- `PRIORITY_THRASH` when state is materially identical but priority moves.

A delta should answer "what changed that changes what we do?", not list every changed line.

## Stall detection

If repeated runs show no relevant stage progress while the same blocker/VERIFY NOW action persists, label the
situation as operationally stalled in the human report. Do not invent an owner or cause. Ask/route only the
smallest missing dependency/evidence needed to unstick it.

## Goal change

When the product goal materially changes, do not mechanically compare old priorities as if they were still
commensurable. Preserve the historical snapshot, mark old actions as `superseded` where appropriate, and rebuild
the critical path under the new goal.

## No shadow roadmap

Do not write inferred statuses back to Notion/GitHub or treat the snapshot as task state. Current product truth
continues to live in the original systems of record.
