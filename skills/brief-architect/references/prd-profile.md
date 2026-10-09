# PRD profile — local pilot

Use only for a requested product requirements / PRD artifact. Produce a handoff
contract, not the finished product or a forecast of commercial success.

Retain all ArtifactBrief fields and readiness rules. Add `artifact_profile: PRD`
and a `prd` object. Read the current repository/context first when available;
never replace a supplied stack, data plane, identity model or deployment target.

## Scalar types and readiness

The parent kernel requires `objective` and `audience` to be nonempty strings,
not arrays or objects. Put audience details in `known`, keeping audience itself
as a short text description. In DEEP, `scope` and `use_moment` must also be
nonempty strings. `deliverables` and `acceptance_criteria` are nonempty lists.

Use the parent readiness rules for the declared status: missing required fields
mean BLOCKED; invalid fields mean INVALID; a complete brief with an open material
decision or material assumption is PROVISIONAL. An audience expressed as a list
cannot be silently declared READY/PROVISIONAL. No unresolved material branch may
be hidden to make the brief READY.

## Contract extension

- `requirements[]`: `{id, description, priority: P0|P1|P2,
  acceptance_criteria_ids[], depends_on[]}`. Every requirement has at least one
  observable acceptance criterion from the parent brief; dependency IDs refer to
  other requirements and must form a DAG. No percentage quota for priorities.
- `delivery_slices[]`: `{id, requirement_ids[], verification}`. Each requirement
  appears in exactly one delivery slice. Earlier slices must contain its prerequisites.
  `verification` is a nonempty string containing the checks and completion condition,
  never an object, array, boolean or null. Reference criterion IDs inside this text;
  preserve entry conditions separately in `entry_conditions[]`.
- `implementation_constraints[]`: supplied choices or labelled uncertainties;
  no React, PostgreSQL, hosting, auth, deadline or numeric target defaults.
- `data_contracts[]`: supplied entities, ownership/access boundaries, identifiers
  and relationships where relevant. Open material choices go to `decision_needed`.
- `interface_contracts[]`: supplied UI/API boundaries, request/result semantics,
  relevant error/failure handling. Unknowns stay explicit rather than invented APIs.
- `non_goals[]`: excluded capabilities; consistent with parent `exclusions`.

Do not require a technical contract when irrelevant; use an empty list with a
brief reason in `known`. These text fields are context, not proof of correctness.
The kernel checks requirement/criterion/dependency/slice integrity and container
types, not architecture semantics or feasibility.

## JSON output schema and enforcement

For JSON PRD generation, use [prd-output.schema.json](prd-output.schema.json).
It defines a canonical producer format with closed objects and explicit field types.
In Codex CLI, pass it as `codex exec --output-schema <path/to/prd-output.schema.json>`;
mentioning the schema in the prompt alone does not enforce it. Other hosts must
provide their equivalent structured-output mechanism or validate and reject the result.
Do not claim constrained generation for a host that has only read these instructions.

The canonical format uses objects for deliverables, criteria, invariants, decisions
and assumptions; text arrays for technical contracts; and a string for slice
verification. All declared keys are required for strict host output. Use `null` only
where the schema permits it (including unknown scalar fields and an absent rubric
lock), and empty arrays for absent lists. This does not invent missing facts or
relax readiness: null required context or empty required lists remain BLOCKED.
Never fabricate a rubric lock. Use a recorded pre-execution lock or null.

Validate against the schema, then run `kernel.readiness(brief)` and require the
declared status to match the computed status before handoff. Reject a type error;
do not stringify objects or silently coerce them. A schema-valid result can still
be INVALID for unknown IDs, cycles, slice order, coverage or a consequential
assumption. Open material decisions remain PROVISIONAL. Schema validity proves
output shape; semantic kernel checks and content review remain necessary.

## Working rules

Separate facts, decisions and assumptions. Unresolved material choices keep the
brief PROVISIONAL; an unknown strategic choice cannot be hidden as a default.
Use no invented evidence, metrics, owners, prices or implementation approvals.

Define behavioral acceptance for success and meaningful failure/access paths.
Reference requirement IDs in delivery slices so the implementer can verify one
bounded increment at a time. Reprioritize by dependencies and constraints.

Keep the source in Markdown/JSON. PDF is optional only when requested and an
approved renderer exists; do not install or execute an unpinned converter.

PRD changes are material: a changed profile, requirement, contract or delivery
slice requires downstream revalidation. Generic briefs keep their current rules.

## Provenance

Adapted from ognjengt/founder-skills PRD Generator and prd_template.md at
`a45931cad934dc6243a68f905485467935a4ad9a`. MIT, Copyright (c) 2026 Ognjen Gatalo.
Full license: [founder-skills-LICENSE.txt](founder-skills-LICENSE.txt).
