# Finding contract

One object per distinct defect:

```text
finding_id
axis
severity: BLOCKER | MAJOR | MINOR | NOTE
confidence: HIGH | MEDIUM | LOW
locator
observation
impact
evidence[]: {kind: OBSERVATION|EXTERNAL|INFERENCE, source, locator}
falsifier
repair_direction
style_preference: true|false
brief_violation: true|false
blocks_acceptance: true|false
```

Rules:

- BLOCKER/MAJOR requires a concrete locator, impact, and at least one well-formed evidence object.
- BLOCKER requires `blocks_acceptance: true`.
- Style preference alone is never material unless it demonstrably violates the brief.
- Keep observation and inference distinct; a suspicion that needs fact-checking goes to `verify[]`.
- Deduplicate only when one root-cause repair genuinely closes all listed instances.
