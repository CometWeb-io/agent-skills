# Output Contract

Use this structure unless the user requests another format. Keep the report decision-oriented: verdict first, then decisive gates, then closure path.

# Release Readiness — [release id]

## Verdict

State in the first lines:

- `GO | GO_WITH_CONTROLS | NO_GO | DEFER`;
- exact candidate/artifact;
- target environment;
- assessment `as_of`;
- profile / mode / derived risk tier;
- readiness score `/100`;
- evidence coverage `%`;
- snapshot hash (short form is fine in prose; retain full value in machine output).

Then give a 2–5 sentence explanation focused on the decisive conditions.

Good:

> DEFER. The candidate is identified and all scored checks are green, but the release is an auth change (R3) assessed only in STANDARD mode and the authorization gate lacks candidate-bound evidence. Re-run in DEEP with direct role/tenant/object authorization tests against build X.

Bad:

> Overall the app looks mostly ready, with a few areas to improve.

## Scope and required-gate completeness

Show:

- audience;
- commercial model;
- risk flags set to `yes`;
- any unresolved risk flags;
- governance surfaces;
- required gate count;
- missing required gates;
- required minimum mode and whether current mode satisfies it.

If scope is incomplete, make it obvious that the engine cannot know the complete gate set yet.

## Binding gates

Table:

| Gate | Domain | Status | Evidence | Candidate fit | Why it matters |
| --- | --- | --- | --- | --- | --- |

List all required/binding gates. Put `FAIL` and `UNKNOWN` first, then controlled passes, then clean passes.

Do not collapse "gate missing" into "gate failed". Missing gate is a scope/evidence defect and normally produces `DEFER`.

## Governance gates

When any surface is required:

| Surface | Status | Evidence / authority | Controls | Decision impact |
| --- | --- | --- | --- | --- |

Use precise semantics:

- `BLOCK` → release blocked;
- `COUNSEL_REQUIRED` → decision deferred;
- `CLEAR_WITH_CONTROLS` → conditional release only if controls are current.

Do not describe legal/privacy/regulatory review as formal approval unless that is actually what the evidence establishes.

## Release blockers

For every blocking `BLOCKER`, `CRITICAL`, or `MAJOR` finding include:

- blocker ID/title;
- domain + canonical gate if applicable;
- exact evidence;
- credible production failure mode;
- smallest credible remediation;
- owner if known;
- exact verification required to close;
- whether closure requires a new candidate build.

If none, say: "No blocking implementation failure was found within assessed scope." Do not imply that scope/evidence gaps are absent unless they are actually absent.

## Evidence gaps

Separate evidence gaps from implementation defects.

Include:

- release identity gaps;
- unresolved scope flags;
- missing required gates;
- binding unknowns;
- candidate mismatches;
- stale/expired evidence;
- required governance gate gaps;
- missing specialist evidence.

For each gap, state the shortest evidence-producing action that can resolve it.

## Domain readiness

Table:

| Domain | Score | Coverage | Status | Decisive evidence / risk |
| --- | ---: | ---: | --- | --- |

Do not over-interpret score when a binding/governance gate dominates the verdict.

## Controlled risks

For each `PASS_WITH_CONTROLS`:

- underlying residual risk;
- actual compensating control;
- control owner;
- due/expiry;
- what invalidates the control;
- rollout/recovery trigger if relevant.

A control is not merely a planned fix. It must materially reduce current release risk.

## Accepted risks

List separately from controlled passes.

For each `ACCEPTED_RISK`:

- risk and impact;
- why it remains non-binding;
- approver;
- risk owner;
- rationale;
- mitigation;
- expiry;
- decision/ticket reference if available.

Never present accepted risk as `PASS`.

## Ship / closure plan

Choose heading based on verdict.

### For GO / GO_WITH_CONTROLS

1. **Before deploy/publish** — final identity/config/control checks.
2. **During rollout** — staged rollout or blast-radius controls.
3. **Watchpoints** — metrics/logs/product/billing/support signals tied to actual failure modes.
4. **Recovery triggers** — objective trigger + owner + rollback/disable/forward-recovery action.
5. **First observation window** — first 24h or a more appropriate traffic-dependent period.

### For DEFER / NO_GO

Return the shortest closure sequence:

1. blocker/gap;
2. smallest remediation/evidence action;
3. exact verification;
4. whether rebuild/redeploy is required;
5. what verdict could become admissible afterward.

Order by dependency and decision value, not by domain alphabetically.

## Delta from previous assessment

When a previous manifest exists, include:

- previous → current verdict;
- candidate changed?;
- score and coverage delta;
- new blockers;
- resolved blockers;
- new binding unknowns;
- resolved binding unknowns;
- new/resolved missing required gates;
- evidence invalidated by candidate/config changes;
- new snapshot hash.

A higher score with a new binding unknown is not an improvement in release admissibility.

## Post-release debt

List `MINOR` and other non-blocking work that should not be confused with release blockers. Include owner/timing only when known.

## Scope, confidence, and assurance limits

State:

- what was actually inspected/executed;
- what was inferred from static evidence;
- which specialist scans/audits were or were not performed;
- unavailable systems/evidence;
- external/current claims that were or were not live-verified;
- any limitation that materially affects confidence.

Use exact language:

- "verified on candidate X";
- "supported by current runbook";
- "not evidenced";
- "candidate mismatch";
- "DEFER pending migration recovery test".

Avoid:

- "looks safe";
- "probably fine";
- "production-ready" without scope qualifiers;
- implying formal security/compliance/legal assurance that was not performed.

## Final decision line

End with one concise machine-like line:

`Decision: [VERDICT] — [single decisive reason or condition].`

For `GO_WITH_CONTROLS`, include the most important condition. For `DEFER`, include the exact missing proof. For `NO_GO`, include the blocking failure.
