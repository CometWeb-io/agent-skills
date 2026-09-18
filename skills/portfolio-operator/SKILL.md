---
name: portfolio-operator
description: Evidence-grounded cross-domain portfolio control plane for deciding what a user or small team should focus on across products, client work, research/academic commitments, growth, operations, and side projects. Use when the user asks what to do this week/next 7-30 days across multiple projects, how to allocate limited capacity, which commitments conflict, what to pause/drop/delegate, how to reconcile client deadlines with product/research work, or for a portfolio-wide review. Do not use for deep prioritization inside one product/repo, release GO/NO-GO, or executing a multi-skill workflow when a specialist/control-plane skill owns that task.
---

# Portfolio Operator

Protocol version: **1.1**.

Operate as a cross-domain allocation control plane. Reconstruct the smallest defensible portfolio truth, expose capacity conflicts, and return a bounded plan for the active horizon.

Do **not** replace Product Operator. Product Operator owns deep state reconciliation and sequencing inside a specific product/repo. Portfolio Operator decides how much attention that product should receive relative to other commitments.

Do **not** replace Skill Orchestrator. When the user wants a multi-skill workflow executed end-to-end, hand off to Skill Orchestrator rather than becoming a workflow engine.

## 0. Load the control plane

Always read:

- [references/source-routing.md](references/source-routing.md)
- [references/portfolio-model.md](references/portfolio-model.md)
- [references/prioritization.md](references/prioritization.md)
- [references/delegation.md](references/delegation.md)
- [references/output-contract.md](references/output-contract.md)

Read [references/evaluation.md](references/evaluation.md) when changing, testing, or diagnosing the skill.

When filesystem + code execution are available, use `scripts/portfolio_kernel.py` for deterministic ranking, capacity-conflict detection, report validation, and human rendering. Use `scripts/run_evals.py` when modifying the skill/kernel. Never claim a script ran if it did not.

## 1. Establish the portfolio contract

Resolve from current context and connected sources before asking the user:

```text
HORIZON:         7d | 14d | 30d | user-defined
PRIMARY GOAL:    <outcome or UNKNOWN>
PORTFOLIO SCOPE: <projects/domains included>
HARD COMMITMENTS:<known external/internal obligations>
CAPACITY:        <user-provided | calendar-derived | relative-only | unknown>
SOURCE LANES:    <calendar/tasks/code/client/research/outcome coverage>
PRIOR SNAPSHOT:  <available | unavailable>
MUTATIONS:       read-only
AS OF:           <timestamp with timezone>
```

Defaults:

- `14d` for "co mam robić teraz / przez najbliższe dwa tygodnie";
- `7d` for weekly planning;
- `30d` for portfolio review or upcoming-deadline planning;
- read-only unless the user explicitly asks for mutations.

Do not invent capacity, hours, deadlines, owners, revenue, customer requirements, or dependencies. When exact capacity is unknown, operate with relative effort classes and focus-stream limits instead of fabricating a calendar.

## 2. Retrieve only portfolio-significant truth

Use [references/source-routing.md](references/source-routing.md).

Retrieve enough to answer cross-domain allocation, not every backlog row or repository file.

Prefer:

- explicit current goals and constraints;
- hard calendar/submission/client deadlines;
- externally promised deliverables;
- project/task state that can change the horizon;
- product/release state only when it materially changes portfolio allocation;
- blocked/waiting dependencies;
- outcome/revenue/customer signals that change focus.

Stop when additional retrieval is unlikely to change `MUST DO / CAPACITY CONFLICTS / NOW / DELEGATE / DELEGATE CANDIDATE / WAITING / PAUSE / DROP / NEXT`.

## 3. Build a bounded Portfolio Ledger

Use [references/portfolio-model.md](references/portfolio-model.md) for the domain taxonomy, commitment types, effort classes, portfolio statuses, and the full item shape including the precision and delegation fields.

Do not fill missing fields with guesses. Unknown is a valid state.

## 4. Separate commitment from importance

Use [references/prioritization.md](references/prioritization.md) and apply its `MUST DO` test literally. "Important", "strategic", "nice to have", or "would improve the product" is not enough.

A future gate that does not block the active horizon belongs in `WAITING` or `NEXT`, not `MUST DO`.

## 5. Model capacity without pretending precision

If exact capacity is not supplied, follow the capacity rules in [references/prioritization.md](references/prioritization.md): relative effort classes, one primary focus stream, at most two secondary streams, maintenance for non-focus projects, and explicit deferral over a fictional schedule.

Do not invent numeric hours to make the plan look precise.

When hard commitments conflict, state the conflict and what trade-off must be resolved. Do not silently drop an external promise.

## 6. Enforce the specialist depth ceiling

Use [references/delegation.md](references/delegation.md) for the delegation map, the handoff shape, and the re-entry rule.

**Specialist depth ceiling:** Portfolio Operator may state an **outcome-level** portfolio action, why it deserves capacity, and an observable done condition. It must not expand that action into the internal backlog, component checklist, implementation sequence, release procedure, or detailed specialist methodology of one project.

When specialist depth is required, keep the portfolio item at `scope_level=portfolio`, give it a short `portfolio_outcome`, create a separate narrow handoff, and re-enter Portfolio Operator only if the specialist result changes allocation.

Do not put specialist-scoped implementation detail directly into `MUST DO` or `NOW`. When `portfolio_outcome` exists, the human renderer must use it instead of any deeper internal `action` text.

### Provenance gate for dates, numbers, and targets

Every **user-facing exact date, deadline, numeric target, currency amount, count, or time-bound KPI** must have either:

- `evidence_ref` pointing to the source that supports the exact value; or
- `user_defined=true` when the user explicitly supplied/approved it.

If neither exists, remove the exact number/date and express the item relationally (for example `within this horizon`, `after the pilot`, `before the client commitment`) rather than inventing precision. Ordinary `evidence[]` is not enough for an exact user-facing value unless the item also identifies the specific `evidence_ref`.

### Delegation reality gate

Use `DELEGATE` only when the assignee is real and currently usable: a known specialist skill/control plane, or an external person/agent/system backed by `delegate_evidence_ref` or explicitly supplied by the user.

If the executor is only hypothetical or not confirmed, use `DELEGATE CANDIDATE` or `PAUSE / DROP`; never create fictional execution capacity.

## 7. Rank after gates, then allocate focus

When execution is available, use the kernel ranking as an aid. Arithmetic cannot override hard commitments or binding gates: apply the gate order in [references/prioritization.md](references/prioritization.md) first, and let a numeric score order items only within a class.

Then allocate one primary focus stream, up to two secondary streams, and maintenance/watch for the rest. If this allocation is impossible, emit `CAPACITY CONFLICTS` before adding more `NOW` work.

## 8. Treat consequential choices as decisions, not hidden ranking

Portfolio Operator may make reversible focus allocation decisions from current evidence. It must not disguise a material strategic/legal/financial/reputational choice as a score.

When two materially different portfolio bets remain plausible and the choice is consequential, create a narrow `DELEGATE -> AI Council` handoff with:

- decision question;
- options;
- evidence already known;
- what changes depending on the choice.

Do not select the option merely because one has a slightly higher arithmetic score.

## 9. Deliver a bounded human brief

Use [references/output-contract.md](references/output-contract.md) for the brief's section order and limits: `MUST DO`, `CAPACITY CONFLICTS`, `NOW`, `DELEGATE`, `DELEGATE CANDIDATE`, `WAITING`, `PAUSE / DROP`, `NEXT`, normally within 450 words and 10 user-facing actions for a standard 14-day plan.

Omit empty sections. Do not print the full ledger, source registry, scores, connector telemetry, or raw sidecar unless requested.

When the user explicitly asks for a view by area, group the same decisions under `CLIENT / PRODUCT / RESEARCH / GROWTH / OPS`; do not create a second competing priority system.

## 10. Preserve the machine sidecar

When filesystem/execution is available, create `portfolio-report.json` in the shape given in [references/output-contract.md](references/output-contract.md) and validate it with `scripts/portfolio_kernel.py` before claiming the brief is complete.

`MUST DO` and `NOW` items require evidence and an observable `done_when` in the sidecar. Exact user-facing dates and numeric targets require `evidence_ref` or `user_defined=true`; `DELEGATE` items must pass the delegation reality gate.

## 11. Use snapshots for repeated reviews

A prior Portfolio Operator snapshot is a comparison baseline, not current truth.

On repeated weekly/14-day runs:

- revalidate hard commitments and deadlines;
- detect completed/new/overdue work;
- explain material focus shifts;
- expose chronic WIP, repeated deferral, and commitments that keep slipping;
- do not preserve a focus lane merely because it existed last time.

## 12. Hard boundaries

- Remain **read-only** by default.
- Do not replace Product Operator with shallow repository analysis.
- Do not cross the specialist depth ceiling: keep product/client/research internals out of portfolio actions.
- Do not replace Skill Orchestrator with hidden multi-skill execution.
- Do not create tasks, send email, move calendar events, change repositories, or message customers unless explicitly requested and supported by the relevant tool/workflow.
- Do not infer implementation from task status or infer customer outcome from shipped code.
- Do not treat prior conversation/memory as authoritative current state when a system-of-record exists.
- Do not invent capacity, hours, deadlines, owners, revenue, obligations, dependencies, or customer requirements.
- Do not show exact dates, numeric targets, counts, currency amounts, or deadline claims without `evidence_ref` or `user_defined=true`.
- Do not put an unconfirmed person/agent/system in `DELEGATE`; use `DELEGATE CANDIDATE` or pause.
- Do not let optional product work displace a hard external commitment without making the trade-off explicit.
- Do not call every active project a focus stream.
- Do not produce a "balanced" plan that gives token work to every project; explicit pause is a valid outcome.

## Definition of done

A standard portfolio run is complete when:

- [ ] Horizon, primary goal, scope, and capacity confidence are recorded.
- [ ] Hard commitments and fixed deadlines are reconciled.
- [ ] Portfolio-significant project state is current enough for allocation.
- [ ] Capacity conflicts are explicit.
- [ ] One primary and at most two secondary focus streams are defensible when capacity is unknown.
- [ ] `MUST DO / NOW / DELEGATE / WAITING / PAUSE / DROP / NEXT` are bounded.
- [ ] Specialist depth is delegated instead of duplicated.
- [ ] Exact user-facing dates/numeric targets pass the provenance gate.
- [ ] Every `DELEGATE` item names a real available executor; hypothetical owners stay `DELEGATE CANDIDATE`/paused.
- [ ] Human brief is concise and machine sidecar preserves evidence.
