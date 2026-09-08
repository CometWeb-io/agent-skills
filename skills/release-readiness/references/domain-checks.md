# Release Readiness Domain Checks

Use this as the baseline domain rubric and gate catalog. Add candidate-specific checks whenever the change introduces a credible new failure mode. Keep canonical `gate` values unchanged when a check is intended to satisfy a required gate family.

## Canonical gate families

### Product

#### `release_scope_acceptance`

Binding baseline. Verify:

- intended release scope is explicit enough to test;
- critical journeys/behaviors touched by the change have acceptance criteria;
- no known P0/blocker defect remains on a critical journey;
- feature flags/defaults/rollout intent match release intent;
- breaking behavior, deprecation, migration, or compatibility impact is understood.

Common non-gate checks:

- empty/loading/error/permission states;
- role/tenant/plan variants;
- semantic correctness of displayed data;
- accessibility/usability regressions that materially block supported users;
- launch-critical analytics events when success measurement depends on them.

#### `ai_safety_behavior`

Conditional binding gate for high-impact AI changes. Verify the product behavior that creates material user harm risk, including failure/override/escalation paths. Do not treat model benchmark quality as sufficient evidence of safe product behavior.

## QA

#### `candidate_verification`

Binding baseline. Verify the exact candidate using the smallest test set that still covers release-critical behavior:

- required CI is green for the candidate;
- critical-path integration/E2E/smoke evidence exists;
- changed-risk negative/error paths are exercised;
- release-blocking regression failures are resolved;
- test output is tied to candidate identity.

Common checks:

- unit/integration/contract/E2E layers proportional to change risk;
- role/tenant/isolation matrix;
- browser/device/platform support matrix;
- flaky/quarantined tests and whether they intersect release scope;
- source-vs-built-artifact differences;
- staging/production-parity limitations.

## Security

#### `security_release`

Binding baseline. Verify:

- no unresolved release-blocking security finding in assessed scope;
- no known exposed production secret/credential;
- materially exposed surfaces have appropriate security evidence;
- validated specialist findings are incorporated rather than merely linked.

#### `auth_access_control`

Binding when `auth_change=yes`. Directly verify:

- authentication/session/token behavior;
- role and permission boundaries;
- object/tenant authorization;
- privilege escalation and account-recovery paths where relevant;
- negative authorization tests.

#### `sensitive_data_handling`

Binding when `sensitive_data_change=yes`. Verify:

- collection/storage/transit exposure paths;
- logs/errors/telemetry/exports/backups;
- access controls and retention/deletion mechanics where material;
- secrets/keys/environment separation;
- privacy gate has been routed separately when required.

Common security checks:

- dependency and supply-chain findings;
- injection/SSRF/file/parser surfaces;
- cookie/session/token hardening;
- rate limiting and abuse controls;
- runtime security headers/TLS where relevant;
- artifact provenance/integrity for high-risk releases.

Use a dedicated security scan for material security scope. This skill consumes validated findings; it is not a penetration-test substitute.

## Operations

#### `release_delivery`

Binding baseline for deployable/published software. Verify the release artifact can reach the target through the intended mechanism:

- deploy/publish pipeline exists and is executable;
- target environment/config/secrets/signing state are understood;
- permissions and required dependencies are present;
- health/readiness/startup behavior is known.

For OSS, this means package/tag/signing/publishing integrity.

#### `recovery_strategy`

Binding baseline for deployable software. Verify a credible recovery path:

- rollback, version rollback, kill switch, feature-flag disable, or forward-recovery path;
- operator/decision owner;
- recovery trigger;
- recovery constraints introduced by schema/data changes.

Do not call a recovery path credible merely because source control can revert a commit.

#### `observability`

Binding baseline. Verify critical release failures can be detected and acted on:

- logs/metrics/traces as appropriate;
- release/correlation/version identifiers;
- actionable alerts and routing;
- owner/on-call/escalation;
- health/business signals linked to failure modes.

#### `migration_integrity`

Binding for schema/data migration. Verify:

- migration artifact corresponds to candidate;
- preconditions and ordering;
- idempotency/restart/retry semantics where relevant;
- data integrity checks;
- rollback or forward-recovery;
- backup/restore or recovery evidence proportional to irreversibility.

#### `infra_resilience`

Binding for major infrastructure changes. Verify:

- capacity and rate limits;
- failure domains;
- queue/backlog/retry behavior;
- third-party/provider degradation;
- networking/DNS/TLS/load balancer behavior where changed;
- rollback/recovery and observability for the new topology.

#### `incident_regression`

Binding for release after a related incident. Reproduce or otherwise directly verify the original failure mode and its guardrail. General green CI does not satisfy this gate by itself.

#### `store_delivery`

Binding for mobile store release. Verify:

- exact signed build/artifact;
- signing/provisioning/version/build metadata;
- release track/staged rollout plan;
- backend compatibility and feature-flag assumptions;
- current applicable platform-policy gate when material.

## Documentation

#### `operator_docs`

Binding baseline for deployed apps/services when documentation is needed for safe operation. Verify current documentation for:

- deploy/publish procedure;
- recovery/rollback/forward recovery;
- environment/configuration prerequisites;
- migrations;
- known operational limitations;
- incident/escalation procedure.

Direct execution is often not meaningful, so `SUPPORTED` evidence can be sufficient when docs are candidate-current.

#### `consumer_docs`

Binding baseline for OSS libraries. Verify:

- install/upgrade instructions;
- compatibility/runtime requirements;
- breaking changes and migration guidance;
- API/usage examples where needed;
- known issues/security reporting route.

Common documentation checks:

- user/admin docs;
- API/schema/change docs;
- release notes/changelog;
- known issues/workarounds;
- support macros/runbooks.

Documentation existence is not enough; verify it matches candidate behavior.

## Billing

Apply whenever commercial model is paid or release touches monetization, checkout, subscriptions, metering, entitlements, credits, invoices, cancellation, refund, or billing provider behavior.

#### `billing_entitlements`

Binding for paid products. Verify:

- plan/price/product mapping in the target configuration;
- entitlement enforcement matches purchased plan;
- access cannot be trivially bypassed or accidentally removed;
- billing state and product access can be reconciled.

#### `billing_state_transitions`

Binding when `billing_change=yes`. Verify material transitions:

- successful/failed checkout;
- webhook replay/retry/idempotency;
- upgrade/downgrade;
- cancel/expiry/grace period;
- failed payment/recovery if used;
- refund/credit behavior where supported;
- trial conversion/expiry;
- metering and reconciliation if usage-based.

Do not infer tax, legal, or payment-network compliance from functional billing tests.

## Support

#### `support_path`

Binding baseline. Interpret according to audience:

External release:

- visible support/contact route where appropriate;
- ownership and escalation/on-call path;
- severity/triage expectations;
- status/incident communication channel where warranted;
- billing/account/privacy/security escalation routes.

Internal release:

- named owner/team;
- escalation route;
- incident/reproduction context.

OSS release:

- issue/discussion/support route;
- security-reporting path;
- version/package context for reproduction.

Common checks:

- support can identify release version/account/tenant/request IDs;
- known issues/workarounds are available;
- launch coverage matches customer commitments/time zones;
- support can distinguish incident vs account/billing issue.

## Cross-domain candidate-specific checks

Add non-canonical checks for material risks such as:

- destructive backfill/import/export;
- dependency/runtime upgrade;
- cloud region/provider migration;
- forced customer migration;
- major third-party integration change;
- feature-flag cutover;
- high-volume cron/job/queue behavior;
- disaster-recovery assumptions;
- data export/import correctness;
- analytics changes that determine launch success measurement.

Do not invent a new canonical gate family when an existing family already captures the required release condition.
