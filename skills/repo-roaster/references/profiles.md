# Repository review profiles

Profiles change what the reviewer searches first; they do not change evidence rules.

## `FULL_REPO`

Map the full accessible topology, critical paths, shared state, cross-cutting auth/config, CI/CD, observability, and dependency boundaries before local findings.

## `PR`

Start from base/head diff, then expand to affected call sites, contracts, schema, tests, feature flags, rollout/rollback, and semantic blast radius. Do not treat a small diff as a small risk.

## `SERVICE`

Prioritize API/input boundaries, authn/authz, state mutations, transactions, external calls, retries/timeouts, idempotency, queues/jobs, observability, configuration, and deploy/rollback behavior.

## `MONOREPO`

Prioritize ownership boundaries, shared packages, dependency direction, build graph, version coupling, cross-app config, generated artifacts, and changes that create broad fan-out.

## `LIBRARY`

Prioritize public API/ABI contract, backward compatibility, error behavior, concurrency/thread safety when relevant, dependency surface, semantic versioning assumptions, tests/examples, and upgrade burden.

## `CLI`

Prioritize input parsing, file/system mutation, destructive-command guards, exit codes, idempotency, shell/process handling, platform assumptions, configuration precedence, and recovery.

## `DESKTOP_APP`

Prioritize local privilege boundaries, IPC, filesystem/keychain/storage, auto-update, native bridge/Tauri/Electron boundaries, offline state, migration, crash recovery, and platform-specific behavior.

## `MOBILE_APP`

Prioritize local secure storage, permission flows, network/offline behavior, background work, sync/conflict handling, schema migrations, platform lifecycle, update compatibility, and sensitive telemetry.

## `DATA_PIPELINE`

Prioritize idempotency, replay, watermark/checkpoint semantics, ordering, late/duplicate events, schema evolution, data lineage, dead-letter/recovery path, partial writes, and backfill safety.

## `AI_AGENT_SYSTEM`

Prioritize tool authorization, prompt/instruction boundaries, untrusted data propagation, action confirmation, secret/context exposure, tool result validation, retry loops, side-effect idempotency, eval coverage, and human escalation.

## `INFRA`

Prioritize privilege, secret/config handling, state management, network boundaries, immutable/reproducible deploys, drift, rollback, destructive changes, dependency/provider pinning, and observability.

## `MIGRATION`

Prioritize backward/forward compatibility, lock duration, data transformation correctness, partial failure, dual-read/write behavior, rollback strategy, large-table behavior, idempotency, and deploy ordering.
