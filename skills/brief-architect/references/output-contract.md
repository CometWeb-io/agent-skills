# Output contract

The primary output is an **ArtifactBrief**, not a generic project plan. v1.3 retains lineage and mode fields without requiring consumers to discard the v1 shape.

```text
schema: cometweb.artifact-brief/v1
brief_id                            # required when brief_version is set
brief_version                       # positive integer; required when brief_id is set
supersedes_brief_id?                # non-empty and not this brief_id
mode: LIGHT | STANDARD | DEEP       # default STANDARD
status: READY | PROVISIONAL | BLOCKED | INVALID
objective
audience
use_moment                          # required in DEEP
scope                               # required in DEEP
risk_level: LOW | MEDIUM | HIGH | CRITICAL   # default LOW
exclusions[]
evidence_policy: SOURCE_BOUND | EVIDENCE_REQUIRED | CONTEXTUAL_DRAFT | CREATIVE
freshness_boundary
deliverables[]                      # a name, or {id, type}; ids unique
acceptance_criteria[]: {id, priority:MUST|SHOULD|MAY, check, observable:true, evidence_required?, verification_method?}
                                    # priority defaults to MUST; a MUST criterion with
                                    # evidence_required: true needs verification_method
protected_invariants[]              # a rule string, or {id, rule} ({id, description} also accepted);
                                    # required in DEEP when risk_level is HIGH or CRITICAL
rubric_lock?: {pack_id, revision, sha256, locked_before_execution: true}
known[]
assumptions[]: {value, material, consequential?}
                                    # a string counts as material; assumption is accepted for value;
                                    # consequential: true is an error (it is a decision, not an assumption)
decision_needed[]: {id?, question, material, resolved}
                                    # a string counts as open and material; decision is accepted for question
material_changes[]?                 # brief delta: changed material fields
requires_downstream_revalidation?   # brief delta: true when anything material changed
recommended_next_skill
```

Lead with the brief itself. Put `BLOCKED/PROVISIONAL` reasons immediately after status. Do not invent owner, deadline, budget, metric, or source policy to make the object look complete.

`schema`, `exclusions`, `freshness_boundary`, `known` and
`recommended_next_skill` are for the reader; the kernel does not check them.

The deterministic kernel validates readiness and lineage semantics. It does not prove that the chosen objective, audience, or acceptance criteria are strategically correct.

`kernel.readiness(brief)` returns `{status, missing[], errors[],
open_material_decisions, material_assumptions, mode}`. `kernel.delta(old, new)`
compares two briefs and returns `{status: CHANGED|UNCHANGED, material_changes[],
requires_downstream_revalidation, errors[]}`; the compared fields are
`objective`, `audience`, `evidence_policy`, `scope`, `use_moment`,
`risk_level`, `acceptance_criteria`, `protected_invariants` and `rubric_lock`.

## Optional PRD extension (local pilot)

`artifact_profile: PRD` and `prd` are optional for generic briefs. When enabled,
the kernel validates the requirements, dependency DAG and delivery-slice trace
defined in [prd-profile.md](prd-profile.md). Any change to `artifact_profile` or
`prd` is material and requires downstream revalidation.
