# Risk Routing and Required Gates

Use this file to determine profile, scope completeness, risk tier, mode floor, required gate families, and governance surfaces.

## 1. Profiles

| Profile | Typical release unit | Baseline interpretation |
| --- | --- | --- |
| `saas_web` | web app + backend | production deploy, user flows, runtime observability |
| `api_service` | API/service | contract behavior, deploy/recovery, runtime health |
| `mobile_app` | signed mobile build | app artifact, backend dependencies, staged/store rollout |
| `desktop_app` | signed desktop build | installer/update channel, compatibility, recovery/update path |
| `internal_tool` | internal production app | operator ownership, access control, deploy/recovery |
| `oss_library` | package/tag/release | package artifact, compatibility, publishing, consumer docs |
| `generic` | unknown/mixed | use conservative deployable-software defaults |

Do not use profile selection to suppress a material cross-profile dependency. Example: a mobile release that changes backend billing still requires billing and backend operational evidence.

## 2. Scope fields

Resolve all release-scope fields before unconditional `GO`.

### Audience

- `external`
- `internal`
- `library_consumers`
- `unknown`

### Commercial

- `paid`
- `free`
- `not_applicable`
- `unknown`

### Risk flags

Resolve each to `yes | no | unknown`:

| Flag | Why it matters |
| --- | --- |
| `first_production_release` | operational unknowns and first-live failure modes |
| `auth_change` | access-control/session/account-takeover risk |
| `billing_change` | money/entitlement/state-transition risk |
| `schema_or_data_migration` | corruption/rollback/forward-recovery risk |
| `sensitive_data_change` | exposure/privacy/data-lifecycle risk |
| `public_api_breaking_change` | downstream consumer compatibility risk |
| `major_infra_change` | capacity/network/provider/failure-domain risk |
| `mobile_store_release` | signing/store/distribution/platform-policy risk |
| `incident_recovery_release` | regression of a known production failure mode |
| `high_impact_ai_change` | material automated-decision/harm risk |
| `legal_or_regulatory_change` | release may depend on current legal/regulatory interpretation |

`unknown` is admissible while investigating but prevents complete scope. Do not convert unknown to no merely to satisfy the engine.

## 3. Risk tier and minimum mode

The engine derives:

### R1 — routine

No elevated/high-risk flag is `yes`.

- Minimum mode: `FAST`.
- Default threshold floor: score 88, conditional 78, evidence coverage 90%.

### R2 — elevated

Any of:

- public API breaking change;
- major infrastructure change;
- mobile store release;
- incident-recovery release.

Minimum mode: `STANDARD`.
Default threshold floor: score 92, conditional 84, evidence coverage 95%.

### R3 — high risk

Any of:

- first production release;
- auth change;
- billing change;
- schema/data migration;
- sensitive-data change;
- high-impact AI change;
- legal/regulatory change.

Minimum mode: `DEEP`.
Default threshold floor: score 95, conditional 90, evidence coverage 98%.

Threshold overrides may raise but never lower these floors.

## 4. Baseline required gate families

A required gate is complete only when at least one applicable check uses that canonical gate family and is marked `binding: true`.

### SaaS web / API service / mobile / desktop / internal tool / generic

Require:

- `release_scope_acceptance`
- `candidate_verification`
- `security_release`
- `release_delivery`
- `recovery_strategy`
- `observability`
- `operator_docs`
- `support_path`

### OSS library

Require:

- `release_scope_acceptance`
- `candidate_verification`
- `security_release`
- `release_delivery`
- `consumer_docs`
- `support_path`

For OSS, `release_delivery` means package/tag/signing/publishing integrity rather than production deployment.

## 5. Conditional required gate families

| Condition | Add required gate(s) |
| --- | --- |
| commercial = `paid` | `billing_entitlements` |
| `auth_change=yes` | `auth_access_control` |
| `billing_change=yes` | `billing_entitlements`, `billing_state_transitions` |
| `schema_or_data_migration=yes` | `migration_integrity`, `recovery_strategy` |
| `sensitive_data_change=yes` | `sensitive_data_handling` |
| `public_api_breaking_change=yes` | `api_compatibility` |
| `major_infra_change=yes` | `infra_resilience`, `recovery_strategy`, `observability` |
| `mobile_store_release=yes` | `store_delivery` |
| `incident_recovery_release=yes` | `incident_regression` |
| `high_impact_ai_change=yes` | `ai_safety_behavior` |

If a conditional gate is logically inapplicable despite a positive flag, revisit the flag or profile. Do not mark the required gate N/A to bypass the matrix.

## 6. Governance surfaces

Use governance gates for constraints that are not ordinary readiness-score items.

Supported surfaces:

- `legal`
- `privacy`
- `financial_risk`
- `responsible_ai`
- `reputation`
- `platform_policy`

Derive automatically at minimum:

| Condition | Governance surface |
| --- | --- |
| `sensitive_data_change=yes` | `privacy` |
| `mobile_store_release=yes` | `platform_policy` |
| `high_impact_ai_change=yes` | `responsible_ai` |
| `legal_or_regulatory_change=yes` | `legal` |

Add other surfaces explicitly when evidence shows they are material.

## 7. Governance statuses

Use only:

- `NOT_REQUIRED`
- `CLEAR`
- `CLEAR_WITH_CONTROLS`
- `COUNSEL_REQUIRED`
- `BLOCK`

A required `CLEAR` needs an evidence basis. A `CLEAR_WITH_CONTROLS` needs current controls, owner, and expiry/due point.

## 8. Typical release archetypes

### Routine patch

Usually R1, `STANDARD` or `FAST` when mature CI and scope are fully known. Prefer delta evidence from the exact candidate.

### Hotfix

Do not automatically weaken gates. Reduce breadth only where the hotfix is tightly scoped and compensating monitoring/recovery is stronger. A production incident may make `incident_recovery_release=yes`.

### First paid launch

Usually R3. Require paid-product billing entitlement evidence even without a billing code change. Add deeper billing transition checks if checkout/subscription logic is new.

### Auth redesign

R3. Directly verify role/tenant/object authorization and session/token behavior. Route a security specialist.

### Data migration

R3. Require migration integrity plus credible rollback/forward-recovery. For irreversible migrations, prefer tested forward recovery and restore evidence.

### Mobile store release

At least R2; R3 if combined with auth/billing/sensitive data/first launch. Treat signing, provisioning, store artifact identity, staged rollout, and platform-policy evidence as candidate-specific.

### Release after incident

At least R2. Verify the exact prior failure mode through `incident_regression` rather than only running the general suite.
