# Evaluation

Golden invariants:

1. SPEC_ONLY can never claim empirical improvement.
2. Candidate and baseline must use the same suite hash for direct comparison.
3. Executed cases cannot silently omit declared cases.
4. Discovery, forced and negative controls are required.
5. REAL_HOST promotion needs exact host/model/harness metadata.
6. STANDARD real-host promotion needs at least 3 runs/case; DEEP needs 5.
7. Invariant regressions block promotion even if pass rate increases.
8. Trigger precision/recall floors are enforced.
9. Over-budget improvement is a TRADEOFF, not unconditional IMPROVED.
10. A worse primary metric is REGRESSION.
