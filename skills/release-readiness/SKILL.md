---
name: release-readiness
description: Assess whether a specific release candidate, build, artifact, application, service, mobile/desktop build, or API is ready for production in a named environment and issue an evidence-backed GO / GO_WITH_CONTROLS / NO_GO / DEFER verdict across product acceptance, QA, security, operations/reliability, documentation, billing/entitlements, and support/incident readiness. Use when the user names or implies a concrete candidate (version, build ID, branch/tag, artifact digest, deploy target) for launch/release gates, pre-deploy audits, "is this build ready to ship?", hotfix readiness, post-incident releases, and repeated delta/revalidation reviews. Do not use for first-time whole-project roadmap baselines or "analyze the entire repo" — use Repo to Roadmap. Do not use for ongoing weekly prioritization on an existing roadmap — use Product Operator. Orchestrate specialist evidence without pretending to replace security scans, live-app QA, legal/privacy review, or deployment authorization.
---

# Release Readiness

Treat release readiness as a **candidate-specific production decision**, not a repository quality score and not a generic checklist. Optimize against false-positive `GO`: missing scope, omitted gates, stale evidence, environment mismatch, and unapproved risk must reduce confidence or block the verdict rather than disappear from scoring.

## Non-negotiable invariants

1. Tie every verdict to an exact release candidate and target environment.
2. Separate **weighted readiness** from **binding gates**. Never average away a blocker.
3. Prove **scope completeness** before accepting a complete gate set.
4. Derive required gates from profile + risk flags; do not let omitted checks create a false green result.
5. Require candidate-bound, temporally admissible evidence for binding passes.
6. Treat `N/A` as exclusion with rationale, never as credit.
7. Separate `PASS_WITH_CONTROLS` from explicit `ACCEPTED_RISK`.
8. Keep governance gates (`legal`, `privacy`, etc.) outside majority/scoring logic.
9. Re-run the verdict after any material red-team finding or evidence downgrade.
10. Treat a readiness verdict as assessment evidence, **not authorization to deploy or perform side effects**.

## Workflow

Follow this sequence:

1. **Identify the release candidate.** Capture release/build ID, artifact identity, target environment, `as_of`, and change set.
2. **Select profile and mode.** Use `references/risk-routing.md`.
3. **Complete the risk scope.** Resolve every required risk flag to `yes` or `no`; keep `unknown` only when evidence is genuinely missing.
4. **Determine governance surfaces.** Route legal/privacy/financial-risk/responsible-AI/reputation/platform-policy issues when material.
5. **Derive the required gate set.** Use profile + commercial model + risk flags. Never start scoring before this step.
6. **Gather evidence.** Prefer candidate-specific execution/runtime/provider evidence over historical summaries. Read `references/evidence-policy.md`.
7. **Route specialist work selectively.** Use `references/integrations.md`; consume specialist findings instead of duplicating deep scans.
8. **Assess the seven domains.** Use `references/domain-checks.md` and add candidate-specific failure modes.
9. **Bootstrap the manifest when code execution is available.** Generate the full required-gate skeleton from release context, then replace `UNKNOWN` placeholders with evidence-backed states.
10. **Run the deterministic engine.** Read `references/manifest-schema.md`.
11. **Red-team the provisional result.** Search specifically for false-green paths.
12. **Re-run the engine after red-team changes.** Do not preserve a previous verdict for consistency.
13. **Return the release packet.** Use `references/output-contract.md`.
14. **For repeated reviews, compare against the prior manifest.** Report delta, newly introduced blockers, resolved blockers, invalidated evidence, and changed candidate identity.
15. **For GO/GO_WITH_CONTROLS, state revalidation triggers and rollout watchpoints.** Read `references/rollout-revalidation.md`.

## Release contract

Capture only known facts. Do not invent unknown values.

Required release identity for an unconditional verdict:

- release/build/version ID;
- target environment;
- assessment `as_of` timestamp;
- at least one immutable artifact identity: commit SHA, image digest, artifact ID, or build number.

Capture when relevant:

- base/head commit and high-risk diff;
- deployment topology and rollout mechanism;
- database/schema/data migration scope;
- auth/access-control changes;
- paid/free model and billing provider;
- public API compatibility impact;
- supported browsers/devices/platforms;
- production config/feature flags;
- incident history related to the change;
- launch commitments and customer migrations.

If the artifact identity is missing, continue collecting evidence but final verdict cannot exceed `DEFER`.

## Profiles

Choose the closest profile and adapt the rubric without weakening mandatory gates:

- `saas_web`
- `api_service`
- `mobile_app`
- `desktop_app`
- `internal_tool`
- `oss_library`
- `generic`

Do not use a profile to hide risk. A mobile app with backend billing still inherits billing and backend-related gates when applicable.

## Modes and risk tier

Use:

- `FAST` — routine, low-risk, reversible release with mature CI and no high/elevated risk flag.
- `STANDARD` — default for ordinary production changes.
- `DEEP` — first production launch, auth/access-control change, billing change, schema/data migration, sensitive-data change, high-impact AI change, legal/regulatory change, or comparable high-downside uncertainty.

The engine derives `R1/R2/R3` from scope flags and enforces a minimum mode. Do not downgrade mode merely to obtain a faster `GO`.

## Scope completeness

Resolve these risk flags to `yes | no | unknown`:

- first production release;
- auth change;
- billing change;
- schema or data migration;
- sensitive-data change;
- public API breaking change;
- major infrastructure change;
- mobile store release;
- incident-recovery release;
- high-impact AI change;
- legal/regulatory change.

Also record:

- audience: external / internal / library consumers;
- commercial model: paid / free / not applicable;
- governance surfaces;
- whether risk-surface assessment is complete.

Any unresolved scope item that can change the required gate set is an evidence gap. Prefer `DEFER` over assuming `no`.

## Seven readiness domains

Assess independently:

1. **Product** — intended scope, acceptance criteria, critical journeys, compatibility, user/customer impact.
2. **QA** — candidate-specific tests, integration/E2E/smoke, negative paths, regression, supported matrix, artifact execution.
3. **Security** — auth/access control, secrets, dependencies/supply chain, sensitive data, exposed surfaces, validated findings.
4. **Operations** — delivery, recovery, observability, migrations, backups/restore, capacity, dependency failure, incident ownership.
5. **Docs** — deploy/recovery runbooks, configuration, user/admin/API docs, migration notes, known issues, release notes.
6. **Billing** — price/plan mapping, entitlements, state transitions, retries/idempotency, cancellation/refund/invoice/metering behavior.
7. **Support** — contact path, triage, escalation, launch coverage, reproduction context, incident/status communication.

Use the canonical gate families in `references/domain-checks.md` so the deterministic engine can detect missing required scope.

## Finding states

Use only:

- `PASS`
- `PASS_WITH_CONTROLS`
- `ACCEPTED_RISK`
- `FAIL`
- `UNKNOWN`
- `N/A`

Severity:

- `BLOCKER`
- `CRITICAL`
- `MAJOR`
- `MINOR`

Rules:

- `BLOCKER`, `CRITICAL`, or binding failure must not be averaged away.
- `MAJOR` unresolved failure blocks by default.
- `PASS_WITH_CONTROLS` requires a real compensating control, owner, mitigation, and non-expired due/expiry point.
- `ACCEPTED_RISK` is allowed only for non-binding `MAJOR/MINOR` risk with explicit approver, owner, rationale, mitigation, and expiry.
- Never use `ACCEPTED_RISK` for binding, blocker, or critical findings.
- `N/A` requires a logical applicability rationale. "Not checked" means `UNKNOWN`.

## Evidence model

Use:

Evidence level:

- `VERIFIED` — direct execution/observation against the candidate or authoritative runtime/provider state.
- `SUPPORTED` — strong static/config/docs evidence without candidate execution.
- `CLAIMED` — assertion without adequate corroboration.
- `MISSING` — no usable evidence.

Freshness:

- `CURRENT`
- `STALE`
- `MISMATCHED`
- `UNKNOWN`

For each binding pass, store structured evidence with at least:

- summary;
- `last_verified_at` / observed time;
- candidate reference when `VERIFIED` is required;
- source type/location when available.

A binding `PASS` with insufficient evidence, missing timestamp, candidate mismatch, stale evidence, or unknown freshness becomes `UNKNOWN` for gating.

Read `references/evidence-policy.md` for evidence authority, contradiction handling, candidate matching, and temporal rules.

## Governance gates

Keep governance constraints separate from readiness score. Supported surfaces:

- `legal`
- `privacy`
- `financial_risk`
- `responsible_ai`
- `reputation`
- `platform_policy`

Use statuses:

- `NOT_REQUIRED`
- `CLEAR`
- `CLEAR_WITH_CONTROLS`
- `COUNSEL_REQUIRED`
- `BLOCK`

Rules:

- `BLOCK` → `NO_GO`.
- `COUNSEL_REQUIRED` → `DEFER`.
- Missing a required governance gate → `DEFER`.
- `CLEAR_WITH_CONTROLS` requires accountable, current controls and can yield at most `GO_WITH_CONTROLS`.
- Do not let a score or majority opinion override a governance `BLOCK`.
- Do not claim legal/privacy/compliance assurance beyond the evidence actually obtained.

## Specialist routing

Use the release-readiness skill as an **orchestrator and final gate**, not a replacement for specialist discovery.

Route when material:

- repository/diff security scan → Security evidence;
- live app/browser audit → Product/QA/Support evidence;
- GitHub/repository inspection → candidate/diff/CI/deploy/migration evidence;
- support/incident systems → Support/Ops evidence;
- billing provider/state → Billing evidence;
- authoritative docs/runbooks → Docs/Ops evidence;
- current external primary sources → changing vendor/platform/regulatory claims;
- AI Council → materially contested risk acceptance, high downside, or conflict between timing and binding evidence.

Do not recursively invoke every specialist. Route only where it changes a material claim, required gate, or verdict confidence.

## Deterministic engine

When code execution is available, first generate a required-gate skeleton from a release context:

```bash
python scripts/bootstrap_manifest.py \
  --context /path/to/release-context.json \
  --output /path/to/readiness.json \
  --pretty
```

The bootstrapper must preserve unknown risk flags as `unknown` and create required gates as binding `UNKNOWN` placeholders. Never treat generated placeholders as evidence.

Then fill the manifest with observed states/evidence and run:

```bash
python scripts/readiness_engine.py --input /path/to/readiness.json --pretty
```

For delta analysis:

```bash
python scripts/readiness_engine.py \
  --input /path/to/current.json \
  --previous /path/to/previous.json \
  --pretty
```

For CI use, read `references/ci-integration.md`.

The engine enforces:

- artifact identity;
- scope completeness;
- profile/risk-derived required gates;
- risk-tier mode floor;
- evidence admissibility;
- governance gates;
- risk-tier threshold floors;
- blocker precedence;
- controlled-risk and accepted-risk rules;
- immutable snapshot hash;
- revalidation triggers.

Use deterministic output as the default authority. If red-team evidence changes the manifest, update the manifest and re-run; do not manually override the engine result.

## Red-team before final verdict

Test at least:

- Was a required gate omitted rather than passed?
- Was a risk flag set to `no` without evidence?
- Is evidence from another commit/build/environment/configuration?
- Did a green suite skip the actually changed critical path?
- Is a supposedly verified check missing candidate/timestamp binding?
- Is rollback/recovery theoretical rather than operationally credible?
- Can migration/retry/idempotency behavior corrupt data or money?
- Are alerts present but unactionable or unowned?
- Could users be charged incorrectly, lose entitlements, get locked out, or lose data?
- Was a `MAJOR` risk disguised as `PASS_WITH_CONTROLS` without a real control?
- Was risk acceptance used without authority or after expiry?
- Did `N/A` remove inconvenient scope?
- Did a current vendor/platform/security/legal claim rely on stale evidence?
- Did a release after an incident verify the actual regression/failure mode?

Any new material unknown must re-enter the manifest and gate logic.

## Verdict semantics

Use only:

- **GO** — complete scope; all required gates present; no blocking/unknown governance or binding gate; evidence meets tier threshold; no residual controlled/accepted risk requiring conditions.
- **GO_WITH_CONTROLS** — no blocker/binding unknown; required gates complete; remaining risk is genuinely controlled or explicitly accepted within policy; conditions are named and current.
- **NO_GO** — known blocking failure, governance block, or known readiness deficit below the conditional floor.
- **DEFER** — incomplete identity/scope/gate set, inadmissible evidence, mode too shallow, unresolved governance/counsel gate, or insufficient coverage.

Use `DEFER` for "we do not yet know" and `NO_GO` for "we know this should not ship".

## Revalidation and living release decisions

Treat each completed assessment as an immutable snapshot tied to the manifest hash. Reopen/revalidate when a material dependency changes. Do not edit an old snapshot to make a new candidate appear covered.

For repeated reviews:

- compare current vs previous manifest;
- report candidate identity change;
- show new/resolved blockers;
- show new/resolved binding unknowns;
- show new/resolved missing required gates;
- explain evidence invalidated by candidate/config changes;
- create a new snapshot hash.

## Output

Use `references/output-contract.md` unless the user asks for another format. Lead with verdict and decisive gates, not a long generic audit narrative.

For every blocker include:

- domain and gate;
- production failure mode;
- exact evidence/evidence gap;
- smallest credible remediation;
- owner if known;
- exact closure verification.

For high-risk releases include rollout watchpoints and objective rollback/forward-recovery triggers.

## Boundaries

- Operate read-only by default.
- Do not deploy, merge, charge, refund, migrate, delete, publish, or notify users merely because readiness is `GO`.
- Do not claim penetration testing, formal compliance, legal approval, or production safety unless that work was actually performed and evidenced.
- Do not use test count, issue count, repository cleanliness, code coverage, Lighthouse score, or a single security score as a proxy for release readiness.
- Do not encode current law, platform policy, vendor requirements, payment-network rules, or security advisories as timeless facts. Verify current primary sources when material.

## Reference map

Read only what the task needs:

- `references/risk-routing.md` — profiles, risk tiers, scope flags, required gates, governance routing.
- `references/domain-checks.md` — seven-domain checks and canonical gate families.
- `references/evidence-policy.md` — evidence authority, freshness, candidate binding, contradictions.
- `references/manifest-schema.md` — v2 schema and examples.
- `references/integrations.md` — connector/specialist routing.
- `references/rollout-revalidation.md` — deploy watchpoints, recovery triggers, repeated assessment.
- `references/output-contract.md` — final report format.
- `references/ci-integration.md` — CI usage and exit policy.
- `references/evaluation.md` — invariants and golden eval cases.
- `references/examples.md` — worked patterns for routine, paid, auth, migration, mobile and accepted-risk releases.
