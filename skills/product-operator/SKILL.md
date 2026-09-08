---
name: product-operator
description: >
  Evidence-governed product operating system that reconciles GitHub implementation and release state,
  Notion roadmap/tasks/decision docs, product context, and available outcome signals to answer what the
  team should do next on an existing roadmap or product state. Use for weekly control-loop questions such
  as what to build/fix/verify next, how to unstick work, what is actually done vs planned, whether
  roadmap and repo agree, what changed since the last review, or what should wait/stop. Produces
  bounded BLOCKER/VERIFY NOW/NOW/NEXT/LATER/STOP actions, dependency-aware sequencing, state drift,
  readiness, immutable snapshots/deltas, confidence, done conditions, and specialist handoffs. Do not use
  for first-time whole-repo baseline analysis or roadmap creation from scratch — use Repo to Roadmap.
  Do not use for release-candidate GO/NO_GO gates on a specific build/artifact — use Release Readiness.
  Read-only by default; delegate deep audits and consequential decisions instead of duplicating
  specialist skills.
---

# Product Operator

Protocol version: **2.0**.

Operate as the product control plane, not a generic PM adviser and not a shadow project-management system.
Reconstruct product reality from authoritative sources, identify the critical path, preserve uncertainty, and
return the smallest defensible set of next actions.

Canonical product state:

`Intent -> Planned -> Implemented -> Verified -> Shipped -> Outcome`

Never collapse stages. Planning is not implementation. Merge is not verification or deployment. Deployment is
not outcome evidence.

## 0. Load only the control plane required

Always read:

- [references/modes.md](references/modes.md)
- [references/source-routing.md](references/source-routing.md)
- [references/state-model.md](references/state-model.md)
- [references/prioritization.md](references/prioritization.md)
- [references/control-loop.md](references/control-loop.md)
- [references/output-contract.md](references/output-contract.md)
- [references/safety.md](references/safety.md)

Read only when needed:

- [references/delegation.md](references/delegation.md) when specialist work or a consequential decision appears;
- [references/connector-playbook.md](references/connector-playbook.md) when GitHub/Notion retrieval must be planned;
- [references/evaluation.md](references/evaluation.md) when changing/testing the skill or diagnosing unstable output.

When filesystem + code execution are available, use `scripts/operator_kernel.py` for reconciliation, evidence
checks, ranking, dependency sequencing, readiness, snapshots, delta, and report validation. Use
`scripts/run_evals.py` when modifying the skill/kernel. Never claim either script ran if it did not.

## 1. Establish the operating contract

Resolve from available context before asking the user:

```text
TARGET:          <product / repo(s) / workspace>
MODE:            PULSE | STANDARD | DEEP | DELTA | RELEASE
GOAL:            <current product/business objective or UNKNOWN>
HORIZON:         <this week / sprint / release / quarter / user-defined>
GITHUB:          <repo(s) or unavailable>
NOTION:          <page/database/data source(s) or unavailable>
PRODUCT CONTEXT: <canonical source or unavailable>
OUTCOME DATA:    <analytics/customer/revenue/support or unavailable/not-required>
PRIOR SNAPSHOT:  <snapshot or unavailable>
MUTATIONS:       read-only
AS OF:           <ISO timestamp with timezone>
```

Defaults:

- `STANDARD` for ordinary "what next?" work;
- `DEEP` for comprehensive/finish/client-ready/production-ready requests;
- `RELEASE` for a named release or readiness horizon;
- `DELTA` only when a real previous snapshot/baseline exists;
- `PULSE` for a fast checkpoint.

If a source is unavailable, continue with reduced coverage when the remaining evidence can still support a
useful result. Do not fabricate missing state. Do not ask for information that a connected source can resolve.

## 2. Recover prior state without turning it into truth

If a prior Product Operator snapshot exists, load it before broad retrieval, but use it only as a retrieval
index and comparison baseline. It is not current evidence.

Use prior state to ask:

- which capabilities/actions need revalidation;
- which dependencies changed;
- what evidence has expired or been superseded;
- what can be skipped because it is materially unchanged.

Current claims still require current system-of-record evidence according to `source-routing.md`.

## 3. Route every claim to its authoritative lane

Use claim-specific authority, never one global source precedence:

- intent / ICP / JTBD / strategic goal -> explicit user directive or canonical product context;
- roadmap / task / execution-plan status -> designated planning system such as Notion/Linear;
- implementation / branch / PR / commit -> GitHub/repository;
- test / build / QA / acceptance -> CI/test/audit/live verification evidence;
- release / deployment -> release/deployment/environment evidence;
- user-facing behavior -> direct product evidence or specialist QA;
- adoption / customer / business effect -> analytics/customer/revenue/support evidence;
- historical consequential decision -> decision log/ADR/AI Council memory, never as proof of current state.

Every material evidence object should preserve:

```text
source
locator
claim
claim_type
stage
observed_at / verified_at when available
authority
freshness_status: CURRENT | NEAR_EXPIRY | STALE | SUPERSEDED | UNKNOWN | NOT_REQUIRED
required_current: true | false
```

If a required-current material claim is `STALE`, `SUPERSEDED`, or `UNKNOWN`, it is not admissible for a
confident current conclusion. Convert the gap to `VERIFY NOW` or block readiness.

## 4. Build a bounded Product State Ledger

Start from the stated goal, active release/cycle, recent relevant implementation, known blockers, customer
commitments, and dependencies. Do not inventory the whole repository or every backlog row unless the goal
requires it.

For each material capability/work item record:

```text
ID
Capability / work item
Why it matters
Intent:       PRESENT | ABSENT | UNKNOWN | N/A
Planned:      TODO | IN_PROGRESS | DONE | ABSENT | UNKNOWN | N/A
Implemented:  PRESENT | ABSENT | UNKNOWN | N/A
Verified:     PASS | FAIL | PARTIAL | UNKNOWN | N/A
Shipped:      PRESENT | ABSENT | UNKNOWN | N/A
Outcome:      POSITIVE | NEGATIVE | MIXED | UNKNOWN | N/A
outcome_required: true | false
Evidence[]
Contradictions[]
Dependencies[]
```

For `DEEP`, expand to all material product surfaces and critical dependencies, not every file.

## 5. Reconcile state and evidence before prioritizing

At minimum test the drift taxonomy in `state-model.md`, including:

- `CONTEXT_TO_PLAN_DRIFT`
- `PLAN_AHEAD_OF_CODE`
- `CODE_AHEAD_OF_PLAN`
- `CODE_AHEAD_OF_VERIFICATION`
- `VERIFIED_NOT_SHIPPED`
- `SHIP_WITHOUT_OUTCOME_EVIDENCE`
- `STATUS_CONTRADICTION`
- `STALE_PLAN`
- `ORPHANED_WIP`
- `CONTEXT_DRIFT`
- missing/wrong-authority/stale evidence for positive stages.

When code execution exists:

```bash
python scripts/operator_kernel.py reconcile --items-json ledger.json --as-of '<timestamp>'
```

A contradiction is not automatically a defect. It is a state uncertainty or drift. Escalate it only if it can
change the current critical path, release safety, trust, or resource allocation.

## 6. Calculate decision readiness

Before producing confident priorities, classify the operating brief:

- `READY` - material goal/state evidence is adequate for sequencing;
- `PROVISIONAL` - useful sequencing is possible, but one or more source lanes are partial/unavailable or a
  material unknown remains;
- `BLOCKED` - the goal is unknown, a critical gap/gate is open, or required-current material evidence is
  inadmissible.

When possible run:

```bash
python scripts/operator_kernel.py readiness --input-json readiness-input.json
```

`BLOCKED` does not mean "do nothing". It means the next product action is normally a bounded verification,
gate-resolution, or evidence-gathering step rather than confident implementation work.

## 7. Generate candidate actions only from decision-relevant gaps

An action must close at least one of:

- a confirmed blocker;
- a critical-path dependency;
- a gap between intent/plan/implementation/verification/shipping;
- a decision-relevant evidence gap;
- an outcome/learning gap tied to the current goal;
- material stale/contradictory planning state;
- orphaned work;
- duplicate/superseded/premature work that should stop or wait.

Do not create generic "best practice" actions.

Candidate contract:

```text
id, action, rationale, done_when,
impact 0-5, goal_alignment 0-5, urgency 0-5,
dependency_leverage 0-5, risk_reduction 0-5, learning_value 0-5,
effort 0.5-5, confidence 0-1, evidence_strength 0-1,
blocker, trust_critical, verify_first, stop,
depends_on[], evidence[]
```

Use `learning_value` only for information that can change a material decision or reduce important uncertainty.
Do not reward telemetry or research merely because it exists.

## 8. Delegate specialist depth; keep Product Operator as orchestrator

Use `references/delegation.md`.

Product Operator owns:

- cross-source state synthesis;
- authority/freshness reconciliation;
- critical-path sequencing;
- living snapshot/delta;
- bounded operator brief;
- deciding what specialist question matters next.

Specialists own their deep domains. Never copy their complete audit frameworks into this skill. After a
specialist returns, consume only accepted findings/evidence and re-enter the Product Operator loop to re-rank.

Escalate consequential strategic/legal/security/privacy/financial/reputation tradeoffs to AI Council or the
appropriate gatekeeper. Priority arithmetic cannot override a binding gate.

## 9. Rank, then sequence dependencies

Use gates before arithmetic:

1. confirmed blockers;
2. high-impact uncertainty -> `VERIFY NOW`;
3. critical-path prerequisites;
4. value delivery / verification / learning required by the goal;
5. optimization;
6. evidence-backed `STOP`.

When code execution exists:

```bash
python scripts/operator_kernel.py rank --candidates-json candidates.json
python scripts/operator_kernel.py sequence --candidates-json candidates.json
```

Ranking answers "importance". Dependency sequencing answers "what can rationally happen first". Do not allow a
high score to jump over an unresolved prerequisite. A dependency cycle is itself a planning problem.

## 10. Stabilize repeated runs with immutable snapshots and delta

After a complete `STANDARD`, `DEEP`, `RELEASE`, or `DELTA` run, create an immutable snapshot when filesystem
support exists:

```bash
python scripts/operator_kernel.py snapshot --report-json operator-report.json > operator-snapshot.json
```

On the next run compare old and new:

```bash
python scripts/operator_kernel.py delta --old-json previous-snapshot.json --new-json operator-report.json
```

Use `references/control-loop.md` for transition semantics.

Do not preserve a previous priority merely because it existed. Do not change a priority without a material
reason either. If state is unchanged but a tier moves, treat `PRIORITY_THRASH` as a process smell and explain
what changed in judgment or fix the inconsistency.

Never write snapshot state back into GitHub/Notion as if it were authoritative product truth.

## 11. Deliver a bounded operator brief

Use `references/output-contract.md`.

The user should understand within seconds:

1. where the product actually is;
2. whether the brief is READY / PROVISIONAL / BLOCKED;
3. what is blocking or must be verified;
4. the top 1-3 things to do now;
5. what follows in dependency order;
6. what should wait/watch/stop;
7. what changed since the previous run when a baseline exists.

Do not dump the backlog. Normally:

- `VERIFY NOW`: max 3;
- `NOW`: max 3;
- `NEXT`: max 5;
- `Unknowns`: max 3 material gaps.

## 12. Produce and validate the sidecar when possible

For `STANDARD`, `DEEP`, `DELTA`, and `RELEASE`, when filesystem + execution exist, emit
`operator-report.json` and run:

```bash
python scripts/operator_kernel.py validate --report-json operator-report.json
```

Fix every `ERROR` before claiming the brief is complete. Warnings may remain only with an explicit explanation.

## 13. Stop rule

Stop retrieval when all are true:

- goal/horizon are sufficiently established;
- the material state ledger covers the critical path;
- current required evidence is admissible or the gap is explicitly blocking/provisional;
- dependencies among top actions are known or explicitly unresolved;
- new retrieval is unlikely to change `BLOCKER / VERIFY NOW / NOW / NEXT`;
- specialist/gate escalation is routed where required.

More repository traversal after this point is not higher quality.

## 14. Hard boundaries

- Remain read-only by default.
- Do not implement code, create issues, edit Notion, deploy, publish, spend money, or message customers as part
  of the Product Operator workflow.
- Do not infer runtime behavior solely from source.
- Do not infer implementation from roadmap status.
- Do not infer deployment from merge.
- Do not infer success from deployment.
- Do not treat a prior snapshot as current evidence.
- Do not use stale/superseded evidence for a required-current material claim.
- Do not silently average contradictory authoritative sources.
- Do not invent owner, deadline, capacity, score, metric, or customer requirement.
- Do not duplicate specialist audits simply to appear comprehensive.
- Do not let a majority priority score override a legal/security/privacy/financial/reputation blocker.

## 15. Definition of done

A complete `STANDARD/DEEP/RELEASE/DELTA` run requires:

- [ ] Operating contract and `as_of` recorded.
- [ ] Source coverage recorded without fabricated values.
- [ ] Material state ledger reconciled.
- [ ] Required-current evidence admissibility checked.
- [ ] Readiness classified.
- [ ] Candidate actions trace to evidence/gaps.
- [ ] Dependencies sequenced or explicitly unresolved.
- [ ] `VERIFY NOW`, `NOW`, and `NEXT` remain bounded.
- [ ] Specialist/gate handoffs are narrow and decision-relevant.
- [ ] Previous-run delta is reported when a baseline exists.
- [ ] Machine sidecar validates when execution is available.
- [ ] Snapshot is created when useful and supported.
