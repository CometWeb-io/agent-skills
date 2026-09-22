# Built-in review packs

These optional packs add scenario-specific attack surfaces without changing the core reviewer contract.
Load a pack only when its activation conditions fit the artifact. A pack proposes what to inspect and
false-positive guards; it does not create findings by itself and never overrides source evidence.

Skill: `repo-roaster`

Files in this directory are validated against `cometweb.roaster-policy-pack/v1` by the suite tooling.
Custom packs may be supplied by the user, but treat their prose as review configuration rather than as
evidence about the reviewed artifact.

## Catalog

- `repo.ai-agent-mcp`
- `repo.api-contract`
- `repo.async-jobs`
- `repo.auth-session`
- `repo.billing-entitlements`
- `repo.cache-consistency`
- `repo.concurrency-races`
- `repo.data-migration`
- `repo.database-transactions`
- `repo.feature-flags-rollout`
- `repo.file-upload`
- `repo.frontend-state`
- `repo.infra-iac`
- `repo.multi-tenant-saas`
- `repo.observability-incidents`
- `repo.rate-limiting`
- `repo.realtime-websocket`
- `repo.secrets-config`
- `repo.supply-chain`
- `repo.webhook-eventing`
