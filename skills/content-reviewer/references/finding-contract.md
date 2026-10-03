# Finding contract

One object per distinct defect:

```text
finding_id                          # unique
fingerprint?                        # unique when present
finding_status: NEW | CARRIED | REOPENED   # default NEW
revalidated: true                   # required for CARRIED
axis
severity: BLOCKER | MAJOR | MINOR | NOTE
confidence: HIGH | MEDIUM | LOW
locator
observation
impact
evidence[]: {kind: OBSERVATION|EXTERNAL|INFERENCE, source, locator, candidate_id?}
evidence_grade?: A | B | C | D
falsifier
repair_direction
style_preference: true|false
brief_violation: true|false
blocks_acceptance: true|false
```

`confidence`, `observation`, `falsifier` and `repair_direction` are for the
reader; the kernel does not check them.

Rules:

- BLOCKER/MAJOR requires a concrete locator, impact, and at least one well-formed evidence object.
- BLOCKER requires `blocks_acceptance: true`.
- Style preference alone is never material unless it demonstrably violates the brief.
- Keep observation and inference distinct; a suspicion that needs fact-checking goes to `verify[]`.
- Deduplicate only when one root-cause repair genuinely closes all listed instances.
