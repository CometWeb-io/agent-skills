# Prioritization

Use gates, unresolved decisions, and dependencies before arithmetic.

## Tier 0 - confirmed blockers

`BLOCKER` is **goal-relative**, not a synonym for "important unresolved problem". A condition belongs here only when current evidence shows it prevents the **stated current goal** or a named current critical-path action. Record `blocks_current_goal=true` and `blocked_item=<goal/action>`.

Typical blockers:
- broken core user job that prevents the current workflow;
- failed build/release path required by the current goal;
- material data-integrity/trust issue that makes the current motion unsafe;
- confirmed legal/security/privacy/reputation/financial gate that prohibits the current motion;
- prerequisite failure that makes the named current action impossible.

A **future gate** that blocks only a later motion does not block the current goal. Mark `future_gate=true`, `blocks_current_goal=false`, and keep it in `LATER/WATCH` unless the current goal changes. Example: Paid Beta prerequisites do not block a free friendly/design-partner validation sprint when free validation is already the binding motion.

If the condition might block the current goal but failure is not yet proven, use `VERIFY NOW`, not a fabricated blocker. If your own explanation says the item **does not block** the current action, it cannot also appear under `BLOCKER` for that action.

## VERIFY NOW

Use when resolving uncertainty can materially change the decision, critical path, trust/release status, or resource allocation. Prefer the smallest authoritative read/test that resolves the crux.

If a material choice exists but a missing fact must be established first, `VERIFY NOW` precedes `DECISION NOW`.

## DECISION NOW

Use when adequate facts exist but a consequential unresolved choice still changes the path. Typical domains: pricing, packaging, offers/pilot motion, strategic allocation, market entry, high-lock-in architecture, or material legal/financial/security/privacy/reputation trade-offs.

Mark candidate `decision_required=true` and provide `decision_domain`. The kernel routes it to `DECISION_NOW` unless `verify_first=true`.

Product Operator frames and delegates the question; it does not select the option. A binding existing decision is not reopened without a real trigger.

## NOW - critical path

Prefer executable actions that unlock the stated goal/release/customer commitment or several downstream actions. Normally max three. Do not place unresolved consequential choices in `NOW`.

## NEXT - dependency ordered

Important actions whose prerequisites are satisfied after NOW or that should follow current critical work. Machine sidecar maximum five; human brief normally shows only the top three.

## LATER / WATCH

`LATER` preserves valuable non-critical work without activating it. `WATCH` is for an external condition, dependency, metric, or decision trigger that does not justify active work now.

Do not use LATER as a hidden backlog dump.

## STOP

Use only when evidence supports duplicate/superseded work, work tied to a superseded goal, dominated alternatives, premature optimization while a prerequisite is open, or unsupported initiatives consuming capacity. Low score alone is not STOP.

## Mechanical ranking

For ordinary non-decision candidates the kernel computes:

`base = 2*impact + 1.5*goal_alignment + 1.25*dependency_leverage + urgency + risk_reduction + learning_value`

`quality = sqrt(confidence * evidence_strength)`

`effort_penalty = 1 + 0.35 * max(0, effort - 1)`

`priority_score = base * quality / effort_penalty`

The formula cannot override blocker/gate status, required verification, `DECISION NOW`, dependency order, evidence admissibility, or a clear STOP reason.

## Dependency sequencing

Rank first, then topologically sequence `depends_on[]`.
- A high-score action cannot jump over an unresolved prerequisite or unresolved `DECISION NOW` dependency.
- Missing dependency references must be surfaced.
- A dependency cycle is a planning/control problem, not a reason to pick an arbitrary order.

## Anti-thrash rule

Across repeated runs, priorities should change because product state, goal, evidence, dependencies, a gate, or a resolved material decision changed. If state is identical but an action changes tier, flag `PRIORITY_THRASH` and explain the changed judgment or restore consistency.

## Anti-score-theater

Never inflate dimensions to force a preferred answer. Cap confidence by evidence. Do not treat effort as permission to ignore a blocker. Do not reward generic telemetry/research; reward decision-relevant learning only.
