# Living Roadmap and Delta Analysis

## Principle

Treat a roadmap as a versioned assessment snapshot, not a permanent truth. Preserve the old snapshot and revalidate only what new evidence can invalidate.

## Baseline Snapshot

Record at minimum:

- schema version,
- assessment timestamp,
- repository/repo set and pinned refs when available,
- target-state contract,
- coverage ledger,
- claim ledger,
- capability inventory,
- roadmap items and hard dependencies,
- unavailable sources,
- snapshot hash.

Use:

```bash
python scripts/roadmap_kernel.py snapshot --roadmap-json '@roadmap.json'
```

Do not edit an old snapshot in place after presenting it as final.

## Watch Dependencies

Attach revalidation triggers to material claims/items. Useful trigger classes:

- repository ref/commit changes on a relevant surface,
- CI/release state changes,
- production/runtime incident,
- product requirement or target-state change,
- vendor/platform behavior change,
- security/privacy/legal constraint change,
- new customer/outcome evidence,
- dependency item completed/rejected/superseded.

## Delta Workflow

1. Load the prior snapshot.
2. Pin the new assessment scope/ref.
3. Identify changed sources/surfaces before deep rereading.
4. Revalidate directly affected claims.
5. Revalidate capabilities that depend on changed claims.
6. Revalidate roadmap items linked to changed claims or changed hard dependencies.
7. Propagate invalidation transitively through hard dependency edges.
8. Re-run priority only for affected items unless the target-state contract changed.
9. If the target state changed materially, treat all priority ordering as open for revalidation.
10. Produce a delta summary plus a new immutable snapshot.

Use:

```bash
python scripts/roadmap_kernel.py delta --before-json '@before.json' --after-json '@after.json'
```

## Validity statuses

Use:

- `VALID` - binding evidence remains admissible and dependencies have not changed materially.
- `WATCH` - still usable, but a known trigger is near or evidence is aging.
- `REVALIDATE` - a binding claim/dependency/target changed.
- `STALE` - snapshot is too old or too weak to use as current truth.
- `SUPERSEDED` - replaced by a newer accepted snapshot.

Do not regenerate the whole roadmap merely because one file changed. Do not preserve the old priority merely because item text did not change.
