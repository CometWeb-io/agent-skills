# Skill Composability and Handoff Contracts

## Contents

1. Ownership rule
2. Core adjacent skills
3. Product/engineering ecosystem handoffs
4. Security/risk handoffs
5. Commercial/communications handoffs
6. Handoff packet contract
7. Return-to-Customer-Ops contract
8. Anti-patterns

## 1. Ownership rule

`customer-ops` owns the **operational customer-to-resolution loop**:

```text
customer evidence -> normalize -> triage/gate -> route -> coordinate -> verify -> follow up -> close/learn
```

It should not absorb specialist workflows merely because customer evidence triggered them.
Produce a compact evidence packet, invoke/hand off the specialist, then bring the result
back into the case graph for customer-visible closure.

## 2. Core adjacent skills

### `customer-research`

Hand off for:

- personas,
- broad JTBD/VOC research,
- external review/community mining,
- quote banks across many sources,
- market-level customer insight synthesis.

Customer Ops supplies structured support signals/problem clusters and explicitly labels the
support-source bias.

### `churn-prevention`

Hand off for:

- cancel-flow design,
- save offers,
- pause/downgrade mechanics,
- dunning/payment recovery program,
- win-back sequence/system.

Customer Ops detects/grounds account risk and operational blockers. It does not redesign
the retention system by default.

### `revops`

Hand off for:

- lifecycle/stage definitions,
- CRM architecture,
- cross-functional routing policy,
- MQL/SQL/revenue process,
- systematic CRM data-hygiene design.

Customer Ops may identify a broken handoff/field as an operational finding.

### `analytics`

Hand off for:

- tracking/event plan,
- instrumentation implementation,
- attribution,
- analytics debugging/design.

Customer Ops consumes telemetry and records when missing/invalid telemetry blocks a case.

### `web-app-auditor`

Use when a customer-reported user-facing defect needs systematic reproduction, UI/data-
integrity verification, flow testing, or regression QA.

Feed:

```text
symptom
route/screen/workflow
expected vs actual
allowed account/test context
evidence already collected
mutation/safety constraints
verification criteria
```

Bring proven reproduction/verification evidence back into the case/GitHub loop.

### `ai-council`

Use for material decisions that need multi-perspective deliberation/risk gates, e.g.:

- exceptional compensation outside policy,
- suspend/disable a risky feature after incident,
- material reputational escalation,
- strategic product shift from repeated evidence,
- high-impact customer/legal/security tradeoff.

Do not invoke Council for routine queue ranking.

## 3. Product/engineering ecosystem handoffs

### `product-operator` (if available)

Hand off when the question becomes:

- what product work should be done next,
- how a customer problem competes with roadmap/strategy/capacity,
- whether to build, defer, test, or decline a customer-driven change.

Customer Ops supplies product evidence pack + current engineering/incident dependencies.

### `release-readiness` (if available)

Feed unresolved customer-risk evidence into pre-production/release decisions:

- open P0/P1 customer cases,
- active/recent incident remediation,
- known regressions/reopens,
- unverified fixes,
- customer-impacting migrations/changes,
- support/runbook gaps relevant to launch.

Release Readiness decides shipment readiness; Customer Ops does not become the release gate.

### `repo-to-roadmap` (if available)

Supply validated customer problem clusters and engineering-linked evidence as one roadmap
input. Do not present support frequency as the roadmap itself.

### `product-teardown` / `competitive-intelligence` (if available)

A recurring competitor-switch signal can justify a handoff for deeper competitor analysis.
One customer mentioning a competitor is only a signal, not a competitive conclusion.

### GitHub security workflows

A customer-reported vulnerability/security finding should route to the appropriate
security triage/scan/finding workflow rather than ordinary bug handling.

## 4. Security/risk handoffs

### Security / privacy / legal

Route when evidence includes:

- unauthorized access,
- credential/secret exposure,
- privacy/confidentiality breach,
- material personal-data exposure,
- data loss/corruption requiring specialist handling,
- formal legal/regulatory request/threat,
- security exploit details.

Customer Ops preserves/restricts evidence and maintains the customer case/exposure state;
it does not independently make breach-notification/legal conclusions.

## 5. Commercial/communications handoffs

### `pricing`

Recurring sourced pricing/value friction across accounts may become pricing evidence. One
refund request or angry price complaint is not a pricing strategy decision.

### `offers`

Use when designing commercial/save/concession offers. Customer Ops can identify the
operational reason but should not invent offer economics.

### `emails`

Lifecycle/win-back/nurture email programs belong to `emails`. Routine factual support
replies can remain in Customer Ops when the user asks to draft/send them.

### `public-relations`

If an incident becomes an earned-media/public-relations matter, route external media
strategy. Canonical incident facts still come from the incident record/risk gates.

### `copywriting`

Product/marketing web copy is outside Customer Ops. Customer support/incident wording
should remain operational, not persuasive marketing copy.

## 6. Handoff packet contract

Every specialist handoff should include only what is needed:

```text
objective / decision needed
case/problem statement
confirmed evidence + source refs + as_of
customer impact / breadth
account_count + case_count if clustered
current priority / evidence grade
constraints / privacy classification
what has already been tried
workaround state
open incident/GitHub/handoff/commitment dependencies
contradictions / unknowns
required deliverable
return-to-customer-ops verification question
```

Do not dump entire private threads when a structured evidence pack is sufficient.

## 7. Return-to-Customer-Ops contract

After specialist work completes, Customer Ops should receive enough to update customer
state:

```text
specialist outcome
decision/action actually performed vs recommended
external/internal artifact ids
current implementation/deployment state
customer-visible verification criteria
new commitments/risks
owner / next checkpoint
```

Examples:

- web-app-auditor proves bug → attach reproduction evidence to GitHub/case.
- product-operator decides TEST → customer case gets honest status; no false promise.
- security triage confirms sensitive issue → case follows restricted comms path.
- churn-prevention designs save flow → Customer Ops does not auto-apply it to an account
  unless the user/process authorizes the intervention.

## 8. Anti-patterns

Do not:

- invoke every adjacent skill for every ticket,
- make the receiving skill reconstruct raw threads unnecessarily,
- treat a handoff as customer resolution,
- use Customer Ops to make a general roadmap/pricing/market verdict,
- let specialist output create a customer commitment without authority,
- lose the case/verification state after handing work away,
- expose private customer evidence to a public research/search workflow.
