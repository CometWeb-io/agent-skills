# Rollout, Recovery, and Revalidation

A release decision is valid only for the assessed candidate, target, evidence state, and controls. Treat it as a living decision with immutable snapshots.

## 1. Before deploy/publish

For `GO` or `GO_WITH_CONTROLS`, confirm immediately before execution:

- artifact identity still matches assessed candidate;
- no required CI/security/provider gate has changed state;
- production configuration assumptions still hold;
- controls/risk acceptances have not expired;
- deploy/release owner is known;
- recovery path is available;
- watchpoints and decision owner are named for elevated/high-risk releases.

If any material item changes, reopen the assessment instead of relying on the old verdict.

## 2. During rollout

Prefer progressive delivery where the platform supports it:

- feature flag;
- canary;
- phased percentage rollout;
- store staged rollout;
- tenant/account cohort;
- region/environment step;
- maintenance window with explicit checkpoints.

Do not require progressive rollout when technically impossible, but increase recovery/observability assurance when blast radius cannot be limited.

## 3. Watchpoints

Select watchpoints from actual failure modes rather than generic dashboards.

Typical technical watchpoints:

- error/exception rate;
- latency/timeouts;
- saturation/capacity;
- queue/backlog age;
- failed/retried jobs;
- DB lock/replica/migration health;
- auth failures/permission denials;
- dependency/provider errors.

Product/commercial watchpoints:

- critical journey completion;
- login/signup/access failures;
- checkout/payment failure;
- entitlement mismatch;
- cancellation/refund anomalies;
- data import/export failures;
- customer/support spike.

Security/abuse watchpoints when relevant:

- unexpected authorization failures/successes;
- suspicious rate/abuse patterns;
- secret/token errors;
- sensitive-data leakage indicators.

## 4. Objective recovery triggers

Avoid vague "rollback if bad" language. Define trigger + owner + action.

Examples:

- critical journey error rate exceeds X for Y minutes → disable feature flag;
- migration integrity check fails → stop rollout and execute forward-recovery procedure;
- entitlement mismatch observed for any paid account → stop billing rollout and reconcile;
- P0 security regression reproduced → halt rollout immediately;
- crash-free sessions fall below defined floor → pause store rollout;
- support receives N similar blocking incidents in M minutes → incident commander decides rollback.

The skill should not invent numeric thresholds when none exist. Surface missing thresholds as operational debt or a binding unknown when material.

## 5. Recovery semantics

Distinguish:

- **rollback** — return to prior application artifact/config;
- **feature disable** — preserve deployment but disable changed behavior;
- **forward recovery** — fix/migrate forward because state cannot safely revert;
- **restore** — recover persisted data from backup/snapshot;
- **reconciliation** — repair external/internal state drift, common in billing/integrations.

A source-code revert does not automatically imply safe data/config rollback.

## 6. First 24 hours

For external/high-risk releases, define first-24h checks:

- service health and critical journeys;
- support/incident signals;
- billing/entitlement reconciliation if paid;
- migration integrity/lag/backfill completion;
- security/abuse anomalies;
- key customer cohorts or rollout segments;
- platform/store crash/error feedback where relevant.

Adjust the window for product traffic patterns rather than treating 24h as universally sufficient.

## 7. Immutable readiness snapshot

Store the engine `snapshot_hash` with:

- candidate identity;
- verdict;
- assessment timestamp;
- manifest/evidence references;
- controls/risk acceptances;
- release owner/approver if available.

Do not edit an old assessment to cover a new build. Create a new manifest/snapshot.

## 8. Revalidation triggers

Reopen/revalidate when:

- commit/build/artifact changes;
- production config/feature flags materially change;
- required evidence expires or becomes invalid;
- security advisory/finding affects assessed scope;
- deploy/recovery/migration plan changes;
- billing provider/config/price mapping changes;
- governance evidence is superseded;
- a compensating control/risk acceptance expires;
- a related incident occurs;
- rollout reveals a material contradiction to pre-release evidence.

## 9. Delta review

Use engine `--previous` support to report:

- candidate changed or not;
- verdict transition;
- score/coverage delta;
- new/resolved blockers;
- new/resolved binding unknowns;
- new/resolved missing required gates;
- changed check states/evidence classifications;
- new snapshot hash.

Do not interpret score improvement as readiness improvement if a new binding unknown or governance issue appeared.
