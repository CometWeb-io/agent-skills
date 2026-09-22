# Output contract

Return an improvement backlog, not an autonomous self-modification log.

```text
schema: cometweb.feedback-integration/v1
as_of?
window_days?
strict: true|false
status: NO_SIGNAL|WATCH|PROPOSED|INVALID
patterns[]: {pattern_id, observations[], independent_contexts, outcome_mix, root_layer, state}
proposals[]: {change, expected_effect, evaluation_plan, regression_test?}
watch[]
retired[]
invalid[]
```

Each proposal preserves pattern, independence count, severity, root layer, causal hypothesis/evidence, affected skills, smallest reversible change, expected effect, blast radius, compatibility risk, and regression test or owned test gap. When a real failure is reproducible, preserve the minimized regression fixture and minimization trace; when a regression appeared across versions, preserve the stable comparison fingerprint and bisection boundary if one can be established.

Do not let stale or false-positive-dominant observations become policy. Do not put candidate-exposed minimized failures directly into a clean holdout. Separate `PROPOSED` from `IMPLEMENTED_UNVERIFIED` and `VERIFIED` in any persistent changelog.
