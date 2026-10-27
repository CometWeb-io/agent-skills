# Finding contract

## Review profiles and evidence language

EDITORIAL emphasizes the brief and reader. ADVERSARIAL pressure-tests the same
artifact's claims, proof, product and offer. Neither profile changes severity
thresholds or requires a second review. Diagnose COPY (wording), PROOF (support),
PRODUCT (actual behavior) or OFFER (terms/value) before choosing a repair;
other layers remain possible. A copy change cannot repair a product defect.

In prose, OBSERVED means directly supported by inspected source; MISSING needs
a bounded absence check; INFERRED needs an explicit reasoning basis; and
VERIFY_EXTERNAL is an unresolved truth question requiring authorized verification.
These prose labels are not replacement enums for v1 evidence.kind, which remains
OBSERVATION, EXTERNAL or INFERENCE. The formal v6 package retains its own fields
and diagnosis contract. Never infer authenticity from either validator's success.

## Finding payload

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
