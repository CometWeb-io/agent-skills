# Worked Examples

Read this file only when a concrete manifest pattern is useful.

## Example 1 — Routine SaaS patch

Scope:

- profile `saas_web`;
- external;
- free;
- all risk flags `no`;
- risk assessment complete;
- mode `standard`.

Required gates:

- release scope acceptance;
- candidate verification;
- security release;
- release delivery;
- recovery strategy;
- observability;
- operator docs;
- support path.

If all are binding/current and coverage is 100%, `GO` is admissible.

## Example 2 — Paid SaaS, no billing code change

Commercial = `paid` adds `billing_entitlements` even when `billing_change=no`.

Rationale: release readiness covers whether the paid product can deliver the purchased access in the target environment, not only whether billing code changed.

Evidence can include:

- current production plan/price mapping;
- entitlement mapping/config;
- a representative non-destructive provider/product-state verification.

Missing billing entitlement gate → `DEFER`.

## Example 3 — Billing state-machine change

Set:

- `commercial=paid`;
- `billing_change=yes`;
- mode `deep`.

Additional gates:

- `billing_entitlements`;
- `billing_state_transitions`.

Test at least the changed material transitions: successful/failed checkout, replay/retry/idempotency, upgrade/downgrade/cancel/expiry, and reconciliation as applicable.

A green checkout happy path does not satisfy state-transition readiness.

## Example 4 — Auth change

Set `auth_change=yes`; engine derives R3 and requires DEEP + `auth_access_control`.

Candidate-specific evidence should test negative authorization boundaries, not merely successful login.

Typical closure evidence:

- tenant A cannot access tenant B object;
- role downgrade removes privilege;
- expired/revoked token/session fails;
- sensitive action enforces current permission.

## Example 5 — Data migration

Set `schema_or_data_migration=yes`.

Require:

- `migration_integrity`;
- `recovery_strategy`;
- R3/DEEP.

If rollback is impossible, do not fail merely because rollback is impossible. Require a credible forward-recovery/restore strategy tied to the actual migration and data state.

## Example 6 — Mobile store rollout

Set `mobile_store_release=yes`; engine derives at least R2, adds `store_delivery`, and routes `platform_policy` governance.

Evidence should bind to exact signed build and rollout track. If store policy is materially relevant, verify the current official source at assessment time.

## Example 7 — Accepted non-binding risk

A documentation gap is material but does not invalidate safe operation. Release owner explicitly accepts it for three days with support workaround.

Use `accepted_risk`, not `pass_with_controls`, because the underlying gap still exists.

Expected verdict: at most `GO_WITH_CONTROLS`.

## Example 8 — Missing gate false-green trap

Suppose Product, QA, Security, Docs, Billing, Support all score 100 but no recovery check exists.

In v1-style scoring this could appear green. In v2 the engine derives `recovery_strategy` as required and returns `DEFER` regardless of weighted score.
