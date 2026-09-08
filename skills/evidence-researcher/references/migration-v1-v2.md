# Migration from v1 to v2

## Structural change

v1 often used one `evidence` row for both source metadata and one-or-many claim relationships. v2 normalizes this into:

- one `source` artifact,
- one claim-specific `evidence` edge per claim/direction.

## Kernel migration

```bash
python scripts/evidence_kernel.py migrate-v1 --ledger-json old.json > migrated.json
python scripts/evidence_kernel.py validate --ledger-json migrated.json
python scripts/evidence_kernel.py audit --ledger-json migrated.json
```

## Important caveat

A v1 boolean `contradiction_tested=true` does not contain the original falsifier query or inspection design. The migration creates a compatibility search record marked as a migration shim so the graph remains structurally usable, but high-stakes/current material claims should rerun the falsifier pass.

## Status compatibility

v1 factual `VERIFIED/PARTIAL/UNSUPPORTED/CONTRADICTED/UNKNOWN` states map directly when valid. v2 adds `SUPPORTED_INFERENCE` and forbids `VERIFIED` for inferences.

## Snapshot policy

Keep the original v1 artifact. Treat the migrated v2 pack as a new derived snapshot; do not pretend the v1 history was originally captured with v2 provenance granularity.
