# Evaluation and regression

Changes to Product Operator should be tested against operational failure modes, not only syntax.

## Required checks after kernel/workflow changes

Run:

```bash
python -m unittest discover -s tests -v
python scripts/run_evals.py
```

Then run the skill packaging validator.

## Core invariants

1. Notion `Done` never proves implementation.
2. Merge/implementation never proves verification/deployment.
3. Deployment never proves outcome.
4. Wrong-authority evidence cannot support a stage as direct proof.
5. Required-current stale/unknown evidence blocks confident readiness.
6. High-impact low-evidence uncertainty can become `VERIFY NOW`.
7. Dependency order beats raw score.
8. Dependency cycles are detected, not arbitrarily ordered.
9. Repeated identical state does not silently reshuffle priorities.
10. Missing connectors degrade coverage/readiness without fabricated state.
11. `NOW` remains bounded.
12. Specialist boundaries remain intact.
13. Goal-relative blocker semantics: future gates never masquerade as current blockers.
14. Suspected blockers without confirmed failure stay in VERIFY NOW.
13. Consequential unresolved pricing/packaging/offer/strategic choices become `DECISION NOW`, not Product Operator recommendations.
14. Human output stays bounded even when the sidecar/evidence set is deep.
15. Non-impacting connector/tool-limit noise is not surfaced to the user.

## Quality metrics for real-world iteration

Track manually or in downstream evaluation:
- top-3 priority precision: would a competent product owner agree these are the critical next actions?
- false-blocker rate;
- false-done rate;
- wrong-authority evidence catch rate;
- stale-evidence catch rate;
- dependency-order correctness;
- repeated-run priority stability;
- percentage of specialist delegations that actually change NOW/NEXT;
- retrieval cost before stop rule;
- unresolved critical unknowns hidden vs surfaced.

Do not optimize scoring weights from fewer than several diverse real runs. Prefer fixing categorical logic
(authority, gates, dependencies, stage semantics) before tuning numeric weights.
