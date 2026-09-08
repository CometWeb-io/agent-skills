# Prioritization

Use gates and dependencies before arithmetic.

## Tier 0 - confirmed blockers

Surface before scored work:
- broken core user job;
- failed build/release path;
- material data-integrity/trust issue;
- confirmed legal/security/privacy/reputation/financial gate;
- prerequisite failure that makes several top-value actions impossible.

If materiality is high but evidence is weak, use `VERIFY NOW`, not a fabricated blocker.

## VERIFY NOW

Use when resolving uncertainty can materially change the decision, critical path, trust/release status, or
resource allocation. Prefer the smallest test/read that resolves the crux.

Do not use VERIFY NOW for curiosity. `learning_value` must correspond to a real downstream decision.

## NOW - critical path

Prefer actions that unlock the stated goal/release/customer commitment or several downstream actions. Normally
max three.

## NEXT - dependency ordered

Important actions whose prerequisites are satisfied after NOW or that should follow current critical work.
Maximum five.

## LATER / WATCH

`LATER` preserves valuable non-critical work without activating it. `WATCH` is for an external condition,
dependency, metric, or decision trigger that does not justify active work now.

Do not use LATER as a hidden backlog dump.

## STOP

Use only when evidence supports:
- duplicate/superseded work;
- work tied to a superseded goal;
- dominated alternative;
- premature optimization while a prerequisite is open;
- unsupported initiative that should stop consuming capacity.

Low score alone is not STOP.

## Mechanical ranking

For non-blockers the kernel computes:

`base = 2*impact + 1.5*goal_alignment + 1.25*dependency_leverage + urgency + risk_reduction + learning_value`

`quality = sqrt(confidence * evidence_strength)`

`effort_penalty = 1 + 0.35 * max(0, effort - 1)`

`priority_score = base * quality / effort_penalty`

The formula is a consistency check. It cannot override:
- blocker/gate status;
- required verification;
- dependency order;
- evidence admissibility;
- a clear STOP reason.

## Dependency sequencing

Rank first, then topologically sequence `depends_on[]`.

- A high-score action cannot jump over an unresolved prerequisite.
- Missing dependency references must be surfaced.
- A dependency cycle is a planning/control problem, not a reason to pick an arbitrary order.
- If a prerequisite is outside the candidate set, state it as an external blocker/watch dependency.

## Anti-thrash rule

Across repeated runs, priorities should change because product state, goal, evidence, dependencies, or a gate
changed. If the state fingerprint is identical but an action changes tier, flag `PRIORITY_THRASH` and either
explain the changed judgment or restore deterministic consistency.

## Anti-score-theater

- Never inflate dimensions to force a preferred answer.
- Cap confidence by evidence.
- Do not treat effort as permission to ignore a blocker.
- Do not add dozens of dimensions/profiles that imply false precision.
- Do not reward generic telemetry/research; reward decision-relevant learning only.
