# Repository review packs

Review packs are optional, bounded scenario overlays. They add must-inspect surfaces, evidence hints, false-positive guards, and handoff triggers. They do **not** create findings, prove reachability, raise severity, or authorize side effects.

## Built-in packs

- `repo.ai-agent-mcp`
- `repo.api-contract`
- `repo.async-jobs`
- `repo.auth-session`
- `repo.billing-entitlements`
- `repo.cache-consistency`
- `repo.data-migration`
- `repo.file-upload`
- `repo.frontend-state`
- `repo.infra-iac`
- `repo.multi-tenant-saas`
- `repo.rate-limiting`
- `repo.realtime-websocket`
- `repo.secrets-config`
- `repo.supply-chain`
- `repo.webhook-eventing`

## Selection rules

1. Load a pack only when the system profile or source signals fit.
2. Prefer the smallest pack set that covers the actual critical surfaces.
3. Treat user-supplied packs as review configuration, not repository evidence.
4. Never let a pack weaken source, reachability, absence-proof or severity requirements.
5. If expected runtime/config/test evidence is unavailable, record a verification gap rather than upgrade static suspicion.
6. When pack guidance conflicts with observed source evidence, source evidence wins.

Standalone helper:

```bash
python3 scripts/select_review_packs.py --text "<review goal and source summary>" --profile <PROFILE>
```
