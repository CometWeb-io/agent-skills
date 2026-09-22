# Output contract

The primary output is an **ArtifactBrief**, not a generic project plan. v1.3 retains lineage and mode fields without requiring consumers to discard the v1 shape.

```text
schema: cometweb.artifact-brief/v1
brief_id
brief_version
supersedes_brief_id?
mode: LIGHT | STANDARD | DEEP
status: READY | PROVISIONAL | BLOCKED | INVALID
objective
audience
use_moment
scope
risk_level: LOW | MEDIUM | HIGH | CRITICAL
exclusions[]
evidence_policy: SOURCE_BOUND | EVIDENCE_REQUIRED | CONTEXTUAL_DRAFT | CREATIVE
freshness_boundary
deliverables[]
acceptance_criteria[]: {id, priority:MUST|SHOULD|MAY, check, observable:true, evidence_required?}
protected_invariants[]
known[]
assumptions[]: {value, material}
decision_needed[]: {id?, question, material, resolved}
changed_fields[]?
downstream_revalidation_required?
recommended_next_skill
```

Lead with the brief itself. Put `BLOCKED/PROVISIONAL` reasons immediately after status. Do not invent owner, deadline, budget, metric, or source policy to make the object look complete.

The deterministic kernel validates readiness and lineage semantics. It does not prove that the chosen objective, audience, or acceptance criteria are strategically correct.
