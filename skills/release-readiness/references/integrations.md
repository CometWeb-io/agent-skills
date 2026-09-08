# Integrations and Specialist Routing

Use connected systems as evidence sources. Do not require a connector merely because it exists, and do not duplicate specialist work already performed well elsewhere.

## Routing principle

Route a specialist/tool only when it can materially change:

- a required gate;
- a binding claim;
- scope/risk classification;
- evidence admissibility;
- governance status;
- final verdict.

The release-readiness skill remains the cross-domain normalizer and release gate.

## GitHub / repository source

Use repository tooling for:

- exact commit/tag/branch/build identity;
- base/head diff and high-risk changed components;
- CI checks and workflow definitions;
- tests and coverage of changed paths;
- deployment/release configuration;
- migrations and infrastructure code;
- dependency manifests/lockfiles;
- release/tag metadata;
- open release-blocking issues or validated findings.

Prefer exact candidate evidence over historical repository green status.

Useful evidence mappings:

| Repository evidence | Domain/gate |
| --- | --- |
| acceptance tests/specs | Product / `release_scope_acceptance` |
| candidate CI/E2E | QA / `candidate_verification` |
| security findings/config | Security / `security_release` |
| deploy workflow | Ops / `release_delivery` |
| rollback/migration code | Ops / `recovery_strategy`, `migration_integrity` |
| runbooks/docs | Docs / `operator_docs` or `consumer_docs` |

## Web App Auditor

Use `web-app-auditor` when a reachable staging/live UI exists and direct behavior matters:

- critical user journeys;
- forms and destructive actions;
- permissions and role states;
- cross-screen data consistency;
- responsive/mobile behavior;
- accessibility behavior with release impact;
- UI/API data mismatch;
- error/retry/loading states.

Feed validated findings into Product/QA/Support. Do not turn every cosmetic defect into a release blocker; map severity to critical journey and production impact.

## Security specialist

Use a dedicated security scan when material security scope exists, especially:

- auth/access-control change;
- new public endpoint or parser/upload surface;
- sensitive-data path;
- dependency/runtime upgrade;
- secrets/infrastructure change;
- new third-party integration;
- high-risk release with insufficient security evidence.

If Codex Security skills are available:

- use a diff scan for a release/PR/branch delta;
- use a repository scan for broader security review;
- validate candidate findings before treating scanner noise as release fact.

Map validated findings into Security checks. Do not treat release-readiness as a vulnerability-discovery engine.

## Product/operator context

If `product-operator` or equivalent context tooling exists, use it to understand:

- intended release behavior;
- roadmap/feature intent;
- acceptance criteria;
- customer commitments;
- operational dependencies.

Do not let product intent override failed release evidence.

## Customer/support/incident systems

If `customer-ops` or support/incident tooling exists, inspect:

- current support route and ownership;
- recurring issues related to changed areas;
- incident/postmortem failure modes;
- launch support coverage;
- reproduction identifiers and escalation paths;
- known workarounds/status communication.

Map to Support/Ops and `incident_regression` when applicable. Minimize private customer data in the report.

## Billing provider / commercial systems

When release is paid or touches money/entitlements:

Prefer:

1. provider state/configuration;
2. candidate-specific sandbox/test events;
3. event/webhook traces;
4. product entitlement state;
5. code/config inspection.

Verify separately where relevant:

- production price/product IDs;
- entitlement mapping;
- checkout/subscription state transitions;
- retry/replay/idempotency;
- cancellation/expiry/refunds;
- reconciliation.

Never perform real charges, refunds, subscription changes, or destructive customer-account actions as part of a read-only readiness review.

## Documentation systems

Use Notion, Google Drive, repository docs, or another authoritative system for:

- deployment/recovery runbooks;
- architecture/configuration context;
- migration instructions;
- support SOPs;
- billing rules;
- release notes/known issues.

A polished stale document is stale evidence. Verify it matches the candidate and current operational path.

## Evidence researcher / current external sources

If an `evidence-researcher` capability is available, use it for changing external claims that can block release:

- current platform/store policy;
- current security advisory affecting dependencies;
- current vendor/provider behavior or documented requirement;
- current regulatory/legal requirement where qualified review is needed.

Prefer official/primary sources and retain `as_of`/version/effective-date context.

## AI Council

Use AI Council for:

- materially contested release decision;
- explicit risk acceptance with meaningful downside;
- conflict between launch timing/revenue and binding evidence;
- high-stakes governance uncertainty;
- disagreement over whether a compensating control genuinely closes a gate.

Council may recommend `GO`, `TEST`, `DEFER`, or `NO-GO` for the decision context, but it cannot convert failed technical evidence into passing evidence or override a binding governance `BLOCK`.

## Current external standards

Browse current official sources only when a material claim depends on them. Do not hard-code a version of a standard/policy as universally current.

For example, security baselines may use current official project guidance as evidence, but the release gate should capture the actual control/finding rather than merely citing a framework name.

## Tool authority

A readiness review is read-only by default. A `GO` result does not authorize:

- deployment;
- merge;
- production configuration change;
- database migration;
- billing action;
- store publication;
- user/customer communication;
- destructive action.

Use the relevant authorization/approval workflow for side effects.
