# Evaluation contract

Optimize for **downstream ambiguity reduction without inventing decisions**.

## Invariants

A regression exists if any of these becomes possible:

- `READY` with a missing objective, audience, deliverable, evidence policy, or acceptance criterion;
- an acceptance criterion can pass without a stable ID, concrete check, and `observable: true`;
- an unknown evidence policy is accepted;
- a material unresolved decision or material assumption is hidden inside `READY`;
- an immaterial/resolved decision blocks execution;
- malformed input crashes the kernel instead of failing closed.

## Golden cases

Maintain cases for: fully ready brief; missing audience; missing evidence policy; invalid policy; duplicate/unobservable criteria; string and object deliverables; material vs immaterial assumptions; open vs resolved material decisions; malformed collection types.

## Champion/challenger metrics

Compare frozen prompts and measure: downstream clarification count, materially wrong assumptions, acceptance-criterion observability, routing precision, context cost, and whether downstream specialists can execute without guessing. Prefer a challenger only when it reduces ambiguity without increasing unnecessary questioning.

## Verification

Run `python3 scripts/run_evals.py`. Repository hardening should additionally run fuzz, coverage, mutation, routing, and package-regression gates. A green structural validator proves shape, not brief quality.
